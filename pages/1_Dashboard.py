import streamlit as st
import pandas as pd
import plotly.express as px
from database.db_connector import create_connection
from models.dashboard import (
    get_dashboard_metrics, 
    get_recent_contracts,
    get_recent_claims,
    get_claims_by_type,
    get_expiring_contracts_count,
    get_contracts_by_status
)

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Dashboard page
st.markdown('# Dashboard')
st.markdown('View key metrics and recent activities')
st.markdown('---')

# Check database connection
conn = create_connection()
if not conn:
    st.error("Could not connect to the database. Please check your connection settings.")
    st.stop()
else:
    conn.close()

# Display refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.experimental_rerun()

# Get metrics
metrics = get_dashboard_metrics()

# Display metrics in columns
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Customers", metrics['customer_count'])
col2.metric("Active Contracts", metrics['contract_count'])
col3.metric("Pending Claims", metrics['pending_claims'])
# Format total payouts for better readability
def format_currency(value):
    if value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    else:
        return f"${value:.2f}"
col4.metric("Total Payouts", format_currency(metrics['total_payouts']))

# Display important alerts
expiring_count = get_expiring_contracts_count()
if expiring_count > 0:
    st.warning(f"⚠️ {expiring_count} contracts are expiring in the next 30 days. Check the Contract Management page.")

# Display recent contracts
st.subheader("Recent Contracts")
recent_contracts = get_recent_contracts(5)
if recent_contracts:
    df = pd.DataFrame(recent_contracts)
    df['SignDate'] = pd.to_datetime(df['SignDate']).dt.strftime('%Y-%m-%d')
    st.dataframe(df[['ContractID', 'CustomerName', 'InsuranceName', 'SignDate', 'Status']], use_container_width=True)
else:
    st.info("No recent contracts found.")

# Display recent claims
st.subheader("Recent Claims")
recent_claims = get_recent_claims(5)
if recent_claims:
    df = pd.DataFrame(recent_claims)
    df['AssessmentDate'] = pd.to_datetime(df['AssessmentDate']).dt.strftime('%Y-%m-%d')
    df['ClaimAmount'] = df['ClaimAmount'].apply(lambda x: f"${x:,.2f}")
    st.dataframe(df[['AssessmentID', 'CustomerName', 'AssessmentDate', 'ClaimAmount', 'Result']], use_container_width=True)
else:
    st.info("No recent claims found.")

# Display contracts by status
st.subheader("Contracts by Status")
contracts_by_status = get_contracts_by_status()
if contracts_by_status:
    df = pd.DataFrame(contracts_by_status)
    fig = px.bar(df, x='Status', y='Count', title='Contract Status Distribution')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No contract status data available.")

# Display claims by insurance type
st.subheader("Claims by Insurance Type")
claims_by_type = get_claims_by_type()
if claims_by_type:
    df = pd.DataFrame(claims_by_type)
    fig = px.pie(df, values='ClaimCount', names='InsuranceName', title='Claims Distribution by Insurance Type')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No claims distribution data available.")