import streamlit as st
import pandas as pd
import plotly.express as px
from database.db_connector import create_connection, execute_query

def display_dashboard():
    """Display the dashboard with key metrics and charts"""
    st.markdown('<div class="sub-header">Dashboard</div>', unsafe_allow_html=True)
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    connection = create_connection()
    if connection:
        # Total Customers
        total_customers = execute_query(connection, "SELECT COUNT(*) AS count FROM Customers")
        if total_customers:
            col1.metric("Total Customers", total_customers[0]['count'])
        
        # Active Contracts
        active_contracts = execute_query(connection, "SELECT COUNT(*) AS count FROM InsuranceContracts")
        if active_contracts:
            col2.metric("Active Contracts", active_contracts[0]['count'])
        
        # Pending Claims
        pending_claims = execute_query(connection, "SELECT COUNT(*) AS count FROM Assessments WHERE Result = 'Pending'")
        if pending_claims:
            col3.metric("Pending Claims", pending_claims[0]['count'])
        
        # Total Payouts
        total_payouts = execute_query(connection, "SELECT SUM(Amount) AS total FROM Payouts")
        if total_payouts and total_payouts[0]['total'] is not None:
            col4.metric("Total Payouts", f"${total_payouts[0]['total']:,.2f}")
        else:
            col4.metric("Total Payouts", "$0.00")
        
        # Display recent contracts
        display_recent_contracts(connection)
        
        # Display claims by insurance type
        display_claims_by_type(connection)
        
        connection.close()

def display_recent_contracts(connection):
    """Display the recent contracts table"""
    st.markdown('<div class="sub-header">Recent Contracts</div>', unsafe_allow_html=True)
    recent_contracts = execute_query(connection, """
        SELECT c.ContractID, cust.CustomerName, c.SignDate, t.InsuranceName
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        ORDER BY c.SignDate DESC LIMIT 5
    """)
    if recent_contracts:
        df_contracts = pd.DataFrame(recent_contracts)
        df_contracts['Period'] = df_contracts['SignDate'].astype(str)
        st.dataframe(df_contracts[['ContractID', 'CustomerName', 'InsuranceName', 'Period']], use_container_width=True)
    else:
        st.info("No recent contracts found.")

def display_claims_by_type(connection):
    """Display the claims by insurance type chart"""
    st.markdown('<div class="sub-header">Claims by Insurance Type</div>', unsafe_allow_html=True)
    claims_by_type = execute_query(connection, """
        SELECT t.InsuranceName, COUNT(a.AssessmentID) as ClaimCount
        FROM Assessments a
        JOIN InsuranceContracts c ON a.ContractID = c.ContractID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        GROUP BY t.InsuranceName
    """)
    if claims_by_type:
        df_claims = pd.DataFrame(claims_by_type)
        fig = px.pie(df_claims, values='ClaimCount', names='InsuranceName', title='Claims Distribution by Insurance Type')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No claims data available.")
