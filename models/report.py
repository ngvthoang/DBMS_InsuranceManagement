import streamlit as st
import pandas as pd
import plotly.express as px
from database.db_connector import create_connection, execute_query

def display_reports():
    """Display the reports section"""
    st.markdown('<div class="sub-header">Reports</div>', unsafe_allow_html=True)
    
    report_type = st.selectbox(
        "Select Report Type",
        [
            "Contracts Summary", 
            "Claims Analysis", 
            "Payout Summary", 
            "Customer Activity"
        ]
    )
    
    connection = create_connection()
    if connection:
        if report_type == "Contracts Summary":
            display_contracts_summary(connection)
        elif report_type == "Claims Analysis":
            display_claims_analysis(connection)
        elif report_type == "Payout Summary":
            display_payout_summary(connection)
        elif report_type == "Customer Activity":
            display_customer_activity(connection)
        
        connection.close()

def display_contracts_summary(connection):
    """Display the contracts summary report"""
    st.markdown('<div class="sub-header">Contracts Summary Report</div>', unsafe_allow_html=True)
    
    # Contracts by insurance type
    type_data = execute_query(connection, """
        SELECT t.InsuranceName, COUNT(*) as Count
        FROM InsuranceContracts c
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        GROUP BY t.InsuranceName
    """)
    if type_data:
        df_type = pd.DataFrame(type_data)
        fig2 = px.bar(df_type, x='InsuranceName', y='Count', title='Contracts by Insurance Type')
        st.plotly_chart(fig2, use_container_width=True)
    
    # Monthly contract trends
    date_data = execute_query(connection, """
        SELECT DATE_FORMAT(SignDate, '%Y-%m') as Month, COUNT(*) as Count
        FROM InsuranceContracts
        GROUP BY DATE_FORMAT(SignDate, '%Y-%m')
        ORDER BY Month
    """)
    if date_data:
        df_date = pd.DataFrame(date_data)
        fig3 = px.line(df_date, x='Month', y='Count', title='Monthly Contract Trend', markers=True)
        st.plotly_chart(fig3, use_container_width=True)

def display_claims_analysis(connection):
    """Display the claims analysis report"""
    st.markdown('<div class="sub-header">Claims Analysis Report</div>', unsafe_allow_html=True)
    
    # Claims by status
    status_data = execute_query(connection, """
        SELECT Result, COUNT(*) as Count
        FROM Assessments
        GROUP BY Result
    """)
    if status_data:
        df_status = pd.DataFrame(status_data)
        fig1 = px.pie(df_status, values='Count', names='Result', title='Claim Status Distribution')
        st.plotly_chart(fig1, use_container_width=True)
    
    # Claims by insurance type
    type_data = execute_query(connection, """
        SELECT t.InsuranceName, COUNT(*) as Count
        FROM Assessments a
        JOIN InsuranceContracts c ON a.ContractID = c.ContractID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        GROUP BY t.InsuranceName
    """)
    if type_data:
        df_type = pd.DataFrame(type_data)
        fig2 = px.bar(df_type, x='InsuranceName', y='Count', 
                     title='Claims Count by Insurance Type')
        st.plotly_chart(fig2, use_container_width=True)
    
    # Monthly claim trends
    date_data = execute_query(connection, """
        SELECT DATE_FORMAT(AssessmentDate, '%Y-%m') as Month, COUNT(*) as Count
        FROM Assessments
        GROUP BY DATE_FORMAT(AssessmentDate, '%Y-%m')
        ORDER BY Month
    """)
    if date_data:
        df_date = pd.DataFrame(date_data)
        fig3 = px.line(df_date, x='Month', y='Count', 
                      title='Monthly Claim Trend', markers=True)
        st.plotly_chart(fig3, use_container_width=True)

def display_payout_summary(connection):
    """Display the payout summary report"""
    st.markdown('<div class="sub-header">Payout Summary Report</div>', unsafe_allow_html=True)
    
    # Payouts by insurance type
    type_data = execute_query(connection, """
        SELECT t.InsuranceName, COUNT(*) as Count, SUM(p.Amount) as TotalAmount
        FROM Payouts p
        JOIN InsuranceContracts c ON p.ContractID = c.ContractID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        GROUP BY t.InsuranceName
    """)
    if type_data:
        df_type = pd.DataFrame(type_data)
        fig1 = px.bar(df_type, x='InsuranceName', y=['Count', 'TotalAmount'], 
                     title='Payouts by Insurance Type',
                     barmode='group')
        st.plotly_chart(fig1, use_container_width=True)
    
    # Monthly payout trends
    date_data = execute_query(connection, """
        SELECT DATE_FORMAT(PayoutDate, '%Y-%m') as Month, SUM(Amount) as TotalAmount
        FROM Payouts
        GROUP BY DATE_FORMAT(PayoutDate, '%Y-%m')
        ORDER BY Month
    """)
    if date_data:
        df_date = pd.DataFrame(date_data)
        fig2 = px.line(df_date, x='Month', y='TotalAmount', 
                      title='Monthly Payout Trend', markers=True)
        st.plotly_chart(fig2, use_container_width=True)

def display_customer_activity(connection):
    """Display the customer activity report"""
    st.markdown('<div class="sub-header">Customer Activity Report</div>', unsafe_allow_html=True)
    
    # Top customers by number of contracts
    top_customers_contracts = execute_query(connection, """
        SELECT cust.CustomerName, COUNT(c.ContractID) as ContractCount
        FROM Customers cust
        LEFT JOIN InsuranceContracts c ON cust.CustomerID = c.CustomerID
        GROUP BY cust.CustomerID
        ORDER BY ContractCount DESC
        LIMIT 10
    """)
    if top_customers_contracts:
        df_top_contracts = pd.DataFrame(top_customers_contracts)
        fig1 = px.bar(df_top_contracts, x='CustomerName', y='ContractCount', 
                     title='Top Customers by Number of Contracts')
        st.plotly_chart(fig1, use_container_width=True)
    
    # Top customers by payout amount
    top_customers_payouts = execute_query(connection, """
        SELECT cust.CustomerName, SUM(p.Amount) as TotalPayoutAmount
        FROM Customers cust
        JOIN InsuranceContracts c ON cust.CustomerID = c.CustomerID
        JOIN Payouts p ON c.ContractID = p.ContractID
        GROUP BY cust.CustomerID
        ORDER BY TotalPayoutAmount DESC
        LIMIT 10
    """)
    if top_customers_payouts:
        df_top_payouts = pd.DataFrame(top_customers_payouts)
        fig2 = px.bar(df_top_payouts, x='CustomerName', y='TotalPayoutAmount', 
                     title='Top Customers by Total Payout Amount')
        st.plotly_chart(fig2, use_container_width=True)
