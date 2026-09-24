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
    st.caption("Present value of a future amount: PV = FV / (1 + r)ⁿ")
    col1, col2, col3 = st.columns(3)
    fv = col1.number_input("Future value (FV)", value=1000.0, step=100.0, key=f"{key}_fv")
    rate = col2.number_input("Annual rate r (%)", value=5.0, step=0.5, key=f"{key}_r") / 100
    periods = col3.number_input("Years (n)", value=5, min_value=0, step=1, key=f"{key}_n")
    pv = fv / ((1 + rate) ** periods) if (1 + rate) != 0 else float("nan")
    st.metric("Present value (PV)", f"{pv:,.2f}")


def _compound_interest(key: str) -> None:
    st.caption("Future value with compound interest: FV = PV × (1 + r)ⁿ")
    col1, col2, col3 = st.columns(3)
    pv = col1.number_input("Initial principal (PV)", value=1000.0, step=100.0, key=f"{key}_pv")
    rate = col2.number_input("Annual rate r (%)", value=5.0, step=0.5, key=f"{key}_r") / 100
    periods = col3.number_input("Years (n)", value=5, min_value=0, step=1, key=f"{key}_n")
    fv = pv * ((1 + rate) ** periods)
    st.metric("Future value (FV)", f"{fv:,.2f}")
    st.metric("Interest earned", f"{fv - pv:,.2f}")


def _holding_period_return(key: str) -> None:
    st.caption("Holding period return: HPR = (P₁ − P₀ + D) / P₀")
    col1, col2, col3 = st.columns(3)
    p0 = col1.number_input("Buying price (P₀)", value=100.0, step=1.0, key=f"{key}_p0")
    p1 = col2.number_input("Selling price (P₁)", value=110.0, step=1.0, key=f"{key}_p1")
    div = col3.number_input("Dividends/coupons (D)", value=2.0, step=0.5, key=f"{key}_d")
    hpr = (p1 - p0 + div) / p0 if p0 else float("nan")
    st.metric("Holding Period Return", f"{hpr * 100:,.2f}%")


def _bond_price(key: str) -> None:
    st.caption(
        "Price of a fixed-coupon bond = present value of the coupons + present value of the face value."
    )
    col1, col2 = st.columns(2)
    face = col1.number_input("Face value", value=1000.0, step=100.0, key=f"{key}_face")
    coupon_rate = col1.number_input(
        "Annual coupon rate (%)", value=5.0, step=0.25, key=f"{key}_c"
    ) / 100
    ytm = col2.number_input(
        "Yield to maturity YTM (%)", value=6.0, step=0.25, key=f"{key}_ytm"
    ) / 100
    years = col2.number_input("Years to maturity", value=5, min_value=1, step=1, key=f"{key}_y")

    coupon = face * coupon_rate
    price = 0.0
    for t in range(1, int(years) + 1):
        price += coupon / ((1 + ytm) ** t)
    price += face / ((1 + ytm) ** int(years))

    st.metric("Bond price", f"{price:,.2f}")
    if price > face:
        st.info("The bond trades **above par** (at a premium): the coupon exceeds the YTM.")
    elif price < face:
        st.info("The bond trades **below par** (at a discount): the YTM exceeds the coupon.")
    else:
        st.info("The bond trades **at par**: coupon and YTM are equal.")


# Registro: kind -> (etichetta, funzione)
CALCULATORS = {
    "present_value": ("Calculator — Present value", _present_value),
    "compound_interest": ("Calculator — Compound interest", _compound_interest),
    "holding_period_return": ("Calculator — Holding Period Return (HPR)", _holding_period_return),
    "bond_price": ("Calculator — Bond price", _bond_price),
}


def render_calculator(kind: str, key: str) -> None:
    entry = CALCULATORS.get(kind)
    if entry is None:
        st.warning(f"Calculator '{kind}' not available.")
        return
    label, func = entry
    st.markdown(f"**{label}**")
    func(key)
