import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection, execute_query
from models.assessment import get_approved_claims

def display_payouts_management():
    """Display the payouts management section"""
    st.markdown('<div class="sub-header">Payouts Management</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Payouts", "Process New Payout"])
    
    # View Payouts Tab
    with tab1:
        display_payouts()
    
    # Process New Payout Tab
    with tab2:
        process_payout_form()

def display_payouts():
    """Display a table of all payouts"""
    connection = create_connection()
    if connection:
        payouts = execute_query(connection, """
            SELECT p.PayoutID, p.ContractID, cust.CustomerName, 
                   p.PayoutDate, p.Amount
            FROM Payouts p
            JOIN InsuranceContracts c ON p.ContractID = c.ContractID
            JOIN Customers cust ON c.CustomerID = cust.CustomerID
            ORDER BY p.PayoutDate DESC
        """)
        if payouts:
            df_payouts = pd.DataFrame(payouts)
            st.dataframe(df_payouts, use_container_width=True)
        else:
            st.info("No payouts found in the database.")
        connection.close()

def process_payout_form():
    """Display the form to process a new payout"""
    approved_claims = get_approved_claims()
    
    if approved_claims:
        with st.form("process_payout_form"):
            payout_id = st.text_input("Payout ID (e.g., P006)")
            
            contract_options = {f"{claim['ContractID']}: {claim['CustomerName']}" for claim in approved_claims}
            selected_contract = st.selectbox("Select Approved Claim", options=contract_options)
            
            payout_date = st.date_input("Payout Date", value=datetime.date.today())
            
            amount = st.number_input("Payout Amount ($)", min_value=0.0, value=0.0, step=100.0)
            
            submitted = st.form_submit_button("Process Payout")
            if submitted:
                if payout_id and selected_contract and amount > 0:
                    contract_id = selected_contract.split(':')[0].strip()
                    
                    save_payout(payout_id, contract_id, amount, payout_date)
                else:
                    st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
    else:
        st.warning("No approved claims without payouts found in the database.")

def save_payout(payout_id, contract_id, amount, payout_date):
    """Save a new payout to the database"""
    connection = create_connection()
    if connection:
        insert_query = """
        INSERT INTO Payouts 
        (PayoutID, ContractID, Amount, PayoutDate) 
        VALUES (%s, %s, %s, %s)
        """
        data = (payout_id, contract_id, amount, payout_date)
        result = execute_query(connection, insert_query, data)
        if result is not None:
            st.markdown('<div class="success-msg">Payout processed successfully!</div>', unsafe_allow_html=True)
        connection.close()
