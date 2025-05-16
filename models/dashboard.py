import streamlit as st
import pandas as pd
import plotly.express as px
from database.db_connector import get_cached_data

@st.cache_data(ttl=300)
def get_dashboard_metrics():
    """Get key metrics for the dashboard"""
    metrics = {}
    
    # Total Customers
    customer_count = get_cached_data("SELECT COUNT(*) AS count FROM Customers")
    metrics['customer_count'] = customer_count[0]['count'] if customer_count else 0
    
    # Active Contracts
    contract_count = get_cached_data("SELECT COUNT(*) AS count FROM InsuranceContracts WHERE Status = 'Active'")
    metrics['contract_count'] = contract_count[0]['count'] if contract_count else 0
    
    # Pending Claims
    pending_claims = get_cached_data("SELECT COUNT(*) AS count FROM Assessments WHERE Result = 'Pending'")
    metrics['pending_claims'] = pending_claims[0]['count'] if pending_claims else 0
    
    # Total Payouts
    total_payouts = get_cached_data("SELECT SUM(Amount) AS total FROM Payouts WHERE Status = 'Approved'")
    metrics['total_payouts'] = total_payouts[0]['total'] if total_payouts and total_payouts[0]['total'] else 0
    
    return metrics

@st.cache_data(ttl=300)
def get_recent_contracts(limit=5):
    """Get the most recent contracts"""
    query = """
        SELECT c.ContractID, cust.CustomerName, c.SignDate, t.InsuranceName, c.Status
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        ORDER BY c.SignDate DESC
        LIMIT %s
    """
    return get_cached_data(query, (limit,))

@st.cache_data(ttl=300)
def get_recent_claims(limit=5):
    """Get the most recent assessments/claims"""
    query = """
        SELECT a.AssessmentID, c.ContractID, cust.CustomerName, 
            a.AssessmentDate, a.ClaimAmount, a.Result
        FROM Assessments a
        JOIN InsuranceContracts c ON a.ContractID = c.ContractID
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        ORDER BY a.AssessmentDate DESC
        LIMIT %s
    """
    return get_cached_data(query, (limit,))

@st.cache_data(ttl=300)
def get_claims_by_type():
    """Get distribution of claims by insurance type"""
    query = """
        SELECT t.InsuranceName, COUNT(a.AssessmentID) as ClaimCount
        FROM Assessments a
        JOIN InsuranceContracts c ON a.ContractID = c.ContractID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        GROUP BY t.InsuranceName
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_expiring_contracts_count():
    """Get count of contracts expiring in the next 30 days"""
    query = """
        SELECT COUNT(*) as count
        FROM InsuranceContracts
        WHERE ExpirationDate BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        AND Status = 'Active'
    """
    result = get_cached_data(query)
    return result[0]['count'] if result else 0

@st.cache_data(ttl=300)
def get_contracts_by_status():
    """Get counts of contracts by status"""
    query = """
        SELECT Status, COUNT(*) as Count
        FROM InsuranceContracts
        GROUP BY Status
    """
    return get_cached_data(query)

def display_dashboard():
    """Display the dashboard with key metrics and charts"""
    st.markdown('<div class="sub-header">Dashboard</div>', unsafe_allow_html=True)
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = get_dashboard_metrics()
    col1.metric("Total Customers", metrics['customer_count'])
    col2.metric("Active Contracts", metrics['contract_count'])
    col3.metric("Pending Claims", metrics['pending_claims'])
    col4.metric("Total Payouts", f"${metrics['total_payouts']:,.2f}")
    
    # Display recent contracts
    display_recent_contracts()
    
    # Display claims by insurance type
    display_claims_by_type()

def display_recent_contracts():
    """Display the recent contracts table"""
    st.markdown('<div class="sub-header">Recent Contracts</div>', unsafe_allow_html=True)
    recent_contracts = get_recent_contracts()
    if recent_contracts:
        df_contracts = pd.DataFrame(recent_contracts)
        df_contracts['Period'] = df_contracts['SignDate'].astype(str)
        st.dataframe(df_contracts[['ContractID', 'CustomerName', 'InsuranceName', 'Period', 'Status']], use_container_width=True)
    else:
        st.info("No recent contracts found.")

def display_claims_by_type():
    """Display the claims by insurance type chart"""
    st.markdown('<div class="sub-header">Claims by Insurance Type</div>', unsafe_allow_html=True)
    claims_by_type = get_claims_by_type()
    if claims_by_type:
        df_claims = pd.DataFrame(claims_by_type)
        fig = px.pie(df_claims, values='ClaimCount', names='InsuranceName', title='Claims Distribution by Insurance Type')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No claims data available.")
