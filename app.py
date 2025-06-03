
import pandas as pd
import numpy as np
import numpy_financial as npf
import streamlit as st
import matplotlib.pyplot as plt

# === Streamlit App ===
st.set_page_config(page_title="CLO IC Model", layout="wide")
st.title("CLO Portfolio IC Model Dashboard")

st.header("Input Parameters")

col1, col2, col3 = st.columns(3)

# Capital commitment inputs
with col1:
    commitment_oakhill = st.number_input("Oakhill Commitment ($)", value=5_000_000, step=500_000)
    commitment_oaktree = st.number_input("Oaktree Commitment ($)", value=15_000_000, step=500_000)
with col2:
    commitment_cvc = st.number_input("CVC Commitment ($)", value=10_000_000, step=500_000)
    commitment_ares = st.number_input("Ares Commitment ($)", value=10_000_000, step=500_000)
with col3:
    default_rate = st.number_input("Default Rate (%)", value=3.0, step=0.5)
    recovery_rate = st.number_input("Recovery Rate (%)", value=65.0, step=1.0)
    distribution_yield = st.number_input("Annual Distribution Yield (%)", value=17.0, step=0.5)

# Compute total commitment
total_commitment = commitment_oakhill + commitment_oaktree + commitment_cvc + commitment_ares

# Capital call schedule
capital_call_schedule = {
    'Year': [2024, 2025, 2026, 2027],
    'Oakhill': [1_500_000, 1_050_000, 1_200_000, 1_250_000],
    'Oaktree': [0, 6_000_000, 6_000_000, 3_000_000],
    'CVC': [0, 2_500_000, 2_500_000, 2_500_000],
    'Ares': [0, 3_500_000, 3_500_000, 3_000_000]
}
capital_call_df = pd.DataFrame(capital_call_schedule)
capital_call_df['Total Call'] = capital_call_df[['Oakhill','Oaktree','CVC','Ares']].sum(axis=1)

# Build detailed cash flow model (12-year horizon)
years = list(range(2024, 2036))
cash_flow_df = pd.DataFrame({'Year': years})
cash_flow_df['Capital Call'] = 0
for idx, row in capital_call_df.iterrows():
    cash_flow_df.loc[cash_flow_df['Year'] == row['Year'], 'Capital Call'] = row['Total Call']
cash_flow_df['Cumulative Call'] = cash_flow_df['Capital Call'].cumsum()

cash_flow_df['Distribution'] = cash_flow_df['Cumulative Call'] * (distribution_yield / 100)
cash_flow_df['Net CF'] = cash_flow_df['Distribution'] - cash_flow_df['Capital Call']

# Default & recovery impact
loss_amount = total_commitment * (default_rate/100) * (1 - recovery_rate/100)
cash_flow_df.loc[cash_flow_df.index[-1], 'Distribution'] -= loss_amount

# Calculate IRR & MOIC for total portfolio
net_cf_series = [-total_commitment] + list(cash_flow_df['Distribution'].iloc[1:])
irr = npf.irr(net_cf_series)
moic = sum(cash_flow_df['Distribution']) / total_commitment

# === Fund-level calculation ===
st.subheader("Fund-Level IRR & MOIC")
funds = ['Oakhill', 'Oaktree', 'CVC', 'Ares']
commitments = {
    'Oakhill': commitment_oakhill,
    'Oaktree': commitment_oaktree,
    'CVC': commitment_cvc,
    'Ares': commitment_ares
}
fund_results = []

# Fund IRR & MOIC Calculation
for fund in funds:
    capital_calls = capital_call_df[fund].tolist()
    fund_cf = []
    invested = 0
    for y in range(12):
        if y < len(capital_calls):
            call_amt = capital_calls[y]
        else:
            call_amt = 0
        invested += call_amt
        dist = invested * (distribution_yield / 100)
        fund_cf.append(dist - call_amt)
    loss_fund = commitments[fund] * (default_rate/100) * (1 - recovery_rate/100)
    fund_cf[-1] -= loss_fund
    irr_fund = npf.irr([-commitments[fund]] + fund_cf[1:])
    moic_fund = sum(fund_cf) / commitments[fund]
    fund_results.append([fund, commitments[fund], irr_fund, moic_fund])

fund_df = pd.DataFrame(fund_results, columns=["Fund", "Commitment", "IRR", "MOIC"])
fund_df["IRR"] = fund_df["IRR"]*100
st.dataframe(fund_df.style.format({"Commitment": "{:,.0f}", "IRR": "{:.2f}%", "MOIC": "{:.2f}x"}))

# === Portfolio level summary ===
st.subheader("Portfolio Results Summary")
st.write("Total Commitment: $", f"{total_commitment:,.0f}")
st.write("Adjusted IRR: ", f"{irr*100:.2f}%")
st.write("Portfolio MOIC: ", f"{moic:.2f}x")

# === Fund-level detailed cash flow charts ===
for fund in funds:
    st.subheader(f"{fund} Fund Cash Flow Analysis")
    fund_calls = capital_call_df[fund].tolist()
    fund_cashflows = []
    invested = 0
    for y in range(12):
        call_amt = fund_calls[y] if y < len(fund_calls) else 0
        invested += call_amt
        dist = invested * (distribution_yield / 100)
        fund_cashflows.append(dist - call_amt)

    # Plot Fund Cash Flow
    fig, ax = plt.subplots()
    ax.bar(range(12), fund_cashflows, label="Fund Cash Flow")
    ax.axhline(0, color='black', linewidth=1)
    ax.set_xlabel("Year")
    ax.set_ylabel("Net Cash Flow ($)")
    ax.set_title(f"{fund} Annual Net Cash Flow")
    st.pyplot(fig)

# === IRR Sensitivity chart ===
st.subheader("IRR Sensitivity to Default Rate")
def_rates = np.arange(0, 10.5, 0.5)
calculated_irrs = []
for dr in def_rates:
    loss = total_commitment * (dr/100) * (1 - recovery_rate/100)
    adj_cf = net_cf_series.copy()
    adj_cf[-1] -= (loss_amount - loss)
    irr_scenario = npf.irr(adj_cf)
    calculated_irrs.append(irr_scenario * 100)

fig, ax = plt.subplots()
ax.plot(def_rates, calculated_irrs, marker='o')
ax.set_xlabel("Default Rate (%)")
ax.set_ylabel("IRR (%)")
ax.set_title("IRR vs Default Rate")
ax.grid(True)
st.pyplot(fig)

# === Cash flow chart ===
st.subheader("Cash Flow Schedule")
fig2, ax2 = plt.subplots()
ax2.bar(cash_flow_df['Year'], cash_flow_df['Net CF'])
ax2.axhline(0, color='black', linewidth=0.8)
ax2.set_xlabel("Year")
ax2.set_ylabel("Net Cash Flow ($)")
ax2.set_title("Annual Net Cash Flow")
st.pyplot(fig2)

# === Full cash flow table ===
st.subheader("Detailed Cash Flow Table")
st.dataframe(cash_flow_df.style.format({
    'Capital Call': '{:,.0f}',
    'Cumulative Call': '{:,.0f}',
    'Distribution': '{:,.0f}',
    'Net CF': '{:,.0f}'
}))
