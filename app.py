# CLO IC Model - Fully Integrated Interactive App (Final Deployable Version)

import pandas as pd
import numpy as np
import numpy_financial as npf
import streamlit as st

# === Streamlit App ===
st.set_page_config(page_title="CLO IC Model", layout="centered")
st.title("CLO Portfolio IC Model Dashboard")

st.header("1️⃣ Input Parameters")

# Adjustable capital commitment inputs
commitment_oakhill = st.number_input("Oakhill Commitment ($)", value=5_000_000, step=500_000)
commitment_oaktree = st.number_input("Oaktree Commitment ($)", value=15_000_000, step=500_000)
commitment_cvc = st.number_input("CVC Commitment ($)", value=10_000_000, step=500_000)
commitment_ares = st.number_input("Ares Commitment ($)", value=10_000_000, step=500_000)

# Adjustable default rate and recovery rate
st.header("2️⃣ Stress Testing Inputs")
default_rate = st.slider("Default Rate (%)", 0.0, 10.0, 3.0)
recovery_rate = st.slider("Recovery Rate (%)", 30.0, 80.0, 65.0)

# Adjustable distribution yield
st.header("3️⃣ Distribution Assumption")
distribution_yield = st.slider("Annual Distribution Yield (%)", 0.0, 20.0, 17.0)

# Compute total commitment
total_commitment = commitment_oakhill + commitment_oaktree + commitment_cvc + commitment_ares

# Build capital call schedule
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

# Distribution assumption
cash_flow_df['Distribution'] = cash_flow_df['Cumulative Call'] * (distribution_yield / 100)
cash_flow_df['Net CF'] = cash_flow_df['Distribution'] - cash_flow_df['Capital Call']

# Apply default & recovery impact
loss_amount = total_commitment * (default_rate/100) * (1 - recovery_rate/100)
cash_flow_df.loc[cash_flow_df.index[-1], 'Distribution'] -= loss_amount

# Calculate IRR & MOIC
net_cf_series = [-total_commitment] + list(cash_flow_df['Distribution'].iloc[1:])
irr = npf.irr(net_cf_series)
moic = sum(cash_flow_df['Distribution']) / total_commitment

# Output Results
st.header("4️⃣ Results Summary")
st.write("Total Commitment: $", f"{total_commitment:,.0f}")
st.write("Adjusted IRR: ", f"{irr*100:.2f}%")
st.write("Portfolio MOIC: ", f"{moic:.2f}x")

# Show full capital call & cash flow schedule
st.header("5️⃣ Capital Call & Cash Flow Schedule")
st.dataframe(cash_flow_df.style.format({
    'Capital Call': '{:,.0f}',
    'Cumulative Call': '{:,.0f}',
    'Distribution': '{:,.0f}',
    'Net CF': '{:,.0f}'
}))
