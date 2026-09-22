"""Calcolatori finanziari interattivi.

Ogni calcolatore è una funzione che disegna i propri input con Streamlit e
mostra il risultato. Sono richiamati da un blocco di tipo "calculator" nel JSON
della lezione, tramite la chiave "kind".

Per aggiungere un nuovo calcolatore: scrivi la funzione e registrala in
CALCULATORS. Nel JSON basterà poi {"type": "calculator", "kind": "<nome>"}.
"""

from __future__ import annotations

import streamlit as st


def _present_value(key: str) -> None:
    st.caption("Valore attuale di un importo futuro: PV = FV / (1 + r)ⁿ")
    col1, col2, col3 = st.columns(3)
    fv = col1.number_input("Valore futuro (FV)", value=1000.0, step=100.0, key=f"{key}_fv")
    rate = col2.number_input("Tasso annuo r (%)", value=5.0, step=0.5, key=f"{key}_r") / 100
    periods = col3.number_input("Anni (n)", value=5, min_value=0, step=1, key=f"{key}_n")
    pv = fv / ((1 + rate) ** periods) if (1 + rate) != 0 else float("nan")
    st.metric("Valore attuale (PV)", f"{pv:,.2f}")


def _compound_interest(key: str) -> None:
    st.caption("Montante con capitalizzazione composta: FV = PV × (1 + r)ⁿ")
    col1, col2, col3 = st.columns(3)
    pv = col1.number_input("Capitale iniziale (PV)", value=1000.0, step=100.0, key=f"{key}_pv")
    rate = col2.number_input("Tasso annuo r (%)", value=5.0, step=0.5, key=f"{key}_r") / 100
    periods = col3.number_input("Anni (n)", value=5, min_value=0, step=1, key=f"{key}_n")
    fv = pv * ((1 + rate) ** periods)
    st.metric("Montante (FV)", f"{fv:,.2f}")
    st.metric("Interessi maturati", f"{fv - pv:,.2f}")


def _holding_period_return(key: str) -> None:
    st.caption("Rendimento di periodo: HPR = (P₁ − P₀ + D) / P₀")
    col1, col2, col3 = st.columns(3)
    p0 = col1.number_input("Prezzo iniziale (P₀)", value=100.0, step=1.0, key=f"{key}_p0")
    p1 = col2.number_input("Prezzo finale (P₁)", value=110.0, step=1.0, key=f"{key}_p1")
    div = col3.number_input("Dividendi/cedole (D)", value=2.0, step=0.5, key=f"{key}_d")
    hpr = (p1 - p0 + div) / p0 if p0 else float("nan")
    st.metric("Holding Period Return", f"{hpr * 100:,.2f}%")


def _bond_price(key: str) -> None:
    st.caption(
        "Prezzo di un bond a cedola fissa = valore attuale delle cedole + valore attuale del nominale."
    )
    col1, col2 = st.columns(2)
    face = col1.number_input("Valore nominale", value=1000.0, step=100.0, key=f"{key}_face")
    coupon_rate = col1.number_input(
        "Tasso cedolare annuo (%)", value=5.0, step=0.25, key=f"{key}_c"
    ) / 100
    ytm = col2.number_input(
        "Rendimento a scadenza YTM (%)", value=6.0, step=0.25, key=f"{key}_ytm"
    ) / 100
    years = col2.number_input("Anni a scadenza", value=5, min_value=1, step=1, key=f"{key}_y")

    coupon = face * coupon_rate
    price = 0.0
    for t in range(1, int(years) + 1):
        price += coupon / ((1 + ytm) ** t)
    price += face / ((1 + ytm) ** int(years))

    st.metric("Prezzo del bond", f"{price:,.2f}")
    if price > face:
        st.info("Il bond quota **sopra la pari** (a premio): la cedola supera l'YTM.")
    elif price < face:
        st.info("Il bond quota **sotto la pari** (a sconto): l'YTM supera la cedola.")
    else:
        st.info("Il bond quota **alla pari**: cedola e YTM coincidono.")


# Registro: kind -> (etichetta, funzione)
CALCULATORS = {
    "present_value": ("Calcolatore — Valore attuale", _present_value),
    "compound_interest": ("Calcolatore — Interesse composto", _compound_interest),
    "holding_period_return": ("Calcolatore — Rendimento di periodo (HPR)", _holding_period_return),
    "bond_price": ("Calcolatore — Prezzo di un bond", _bond_price),
}


def render_calculator(kind: str, key: str) -> None:
    entry = CALCULATORS.get(kind)
    if entry is None:
        st.warning(f"Calcolatore '{kind}' non disponibile.")
        return
    label, func = entry
    st.markdown(f"**{label}**")
    func(key)
