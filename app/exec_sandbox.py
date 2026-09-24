"""Esecuzione del codice Python degli utenti in modo isolato.

Il codice gira in un SOTTOPROCESSO separato con:
- ambiente ripulito (niente variabili/segreti dell'app: chiavi API, ecc.);
- timeout (il processo viene ucciso se supera il limite);
- limiti di CPU e memoria (dove il sistema operativo lo supporta);
- cattura di stdout/stderr e delle figure matplotlib (salvate come PNG).

Nota: l'esecuzione è pensata per un gruppo di account APPROVATI dall'owner,
non per un pubblico anonimo. È un compromesso ragionevole di sicurezza per uno
strumento di studio con accesso controllato.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Harness che avvolge il codice utente: imposta matplotlib in modalità non
# interattiva, esegue il codice, poi salva tutte le figure aperte come PNG.
_HARNESS = r"""
import sys, os
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as _plt
except Exception:
    _plt = None

_user_code = open(os.environ["USER_CODE_FILE"], encoding="utf-8").read()
_ns = {"__name__": "__main__"}
try:
    exec(compile(_user_code, "<nota>", "exec"), _ns)
except Exception:
    import traceback
    traceback.print_exc()

if _plt is not None:
    _outdir = os.environ["FIG_DIR"]
    for _i, _num in enumerate(_plt.get_fignums()):
        try:
            _plt.figure(_num).savefig(os.path.join(_outdir, f"fig_{_i}.png"),
                                      dpi=110, bbox_inches="tight")
        except Exception:
            pass
"""


def _limit_resources() -> None:  # pragma: no cover - dipende dall'OS
    try:
        import resource

        # Limite di CPU (secondi). Il tempo di parete è gestito dal timeout.
        resource.setrlimit(resource.RLIMIT_CPU, (12, 12))
        # Limite di spazio di indirizzamento generoso: lo stack scientifico
        # (numpy/scipy/matplotlib) mmappa molte librerie condivise, quindi un
        # tetto troppo basso ne impedisce perfino l'import.
        mem = 4 * 1024 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    except Exception:
        pass


def run_code(code: str, timeout: int = 15) -> dict:
    """Esegue `code` e ritorna {stdout, stderr, images:[bytes], timed_out:bool}."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        code_file = tmp_path / "user_code.py"
        code_file.write_text(code, encoding="utf-8")
        fig_dir = tmp_path / "figs"
        fig_dir.mkdir()

        # Ambiente minimo: NIENTE segreti dell'app. PYTHONPATH replica i
        # percorsi dei pacchetti del processo corrente, così il sottoprocesso
        # trova numpy/matplotlib/... indipendentemente da dove sono installati.
        clean_env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(tmp_path),
            "LANG": "C.UTF-8",
            "MPLCONFIGDIR": str(tmp_path / ".mpl"),
            "PYTHONPATH": os.pathsep.join(p for p in sys.path if p),
            "USER_CODE_FILE": str(code_file),
            "FIG_DIR": str(fig_dir),
        }

        try:
            proc = subprocess.run(
                [sys.executable, "-c", _HARNESS],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=clean_env,
                cwd=tmp_path,
                preexec_fn=_limit_resources if sys.platform != "win32" else None,
            )
            stdout, stderr, timed_out = proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = (exc.stderr or "") + f"\n⏱️ Time limit exceeded ({timeout}s)."
            timed_out = True

        images = []
        for png in sorted(fig_dir.glob("fig_*.png")):
            images.append(png.read_bytes())

        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")

        return {
            "stdout": stdout or "",
            "stderr": stderr or "",
            "images": images,
            "timed_out": timed_out,
        }
