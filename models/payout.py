import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection, execute_query
from models.assessment import get_approved_claims
from mysql.connector import Error
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

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
                   p.PayoutDate, p.Amount, p.Status
            FROM Payouts p
            JOIN InsuranceContracts c ON p.ContractID = c.ContractID
            JOIN Customers cust ON c.CustomerID = cust.CustomerID
            ORDER BY p.PayoutDate DESC
        """)
        if payouts:
            df_payouts = pd.DataFrame(payouts)
            
            # Configure AgGrid
            gb = GridOptionsBuilder.from_dataframe(df_payouts)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_side_bar()
            gb.configure_default_column(editable=True, filter=True)
            grid_options = gb.build()

            # Display the interactive table
            AgGrid(
                df_payouts,
                gridOptions=grid_options,
                enable_enterprise_modules=True,
                theme="blue",
                height=400,
                fit_columns_on_grid_load=True,
            )
        else:
            st.info("No payouts found in the database.")
        connection.close()

def process_payout_form():
    """Display the form to process a new payout"""
    approved_claims = get_approved_claims()
    
    if approved_claims:
        with st.form("process_payout_form"):
            # Auto-generate next ID
            connection = create_connection()
            if connection:
                next_id = "P001"  # Default starting ID if no records exist
                try:
                    last_payout = execute_query(connection, "SELECT PayoutID FROM Payouts ORDER BY PayoutID DESC LIMIT 1")
                    if last_payout:
                        last_id = last_payout[0]['PayoutID']
                        next_id = f"P{int(last_id[1:]) + 1:03d}"
                except Error as e:
                    st.error(f"Error fetching last payout ID: {e}")
                finally:
                    connection.close()
                    
            payout_id = st.text_input("Payout ID (e.g., P006)", value=next_id)
            
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
