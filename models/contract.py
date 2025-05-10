import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection, execute_query
from models.customer import get_customers
from models.insurance_type import get_insurance_types

def display_contract_management():
    """Display the contract management section"""
    st.markdown('<div class="sub-header">Contract Management</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Contracts", "Create Contract"])
    
    # View Contracts Tab
    with tab1:
        display_contracts()
    
    # Create Contract Tab
    with tab2:
        create_contract_form()

def display_contracts():
    """Display a table of all contracts"""
    connection = create_connection()
    if connection:
        contracts = execute_query(connection, """
            SELECT c.ContractID, cust.CustomerName, t.InsuranceName, c.SignDate
            FROM InsuranceContracts c
            JOIN Customers cust ON c.CustomerID = cust.CustomerID
            JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        """)
        if contracts:
            df_contracts = pd.DataFrame(contracts)
            st.dataframe(df_contracts, use_container_width=True)
        else:
            st.info("No contracts found in the database.")
        connection.close()

def create_contract_form():
    """Display the form to create a new contract"""
    connection = create_connection()
    if connection:
        customers = execute_query(connection, "SELECT CustomerID, CustomerName FROM Customers")
        insurance_types = execute_query(connection, "SELECT InsuranceTypeID, InsuranceName FROM InsuranceTypes")
        
        if customers and insurance_types:
            with st.form("create_contract_form"):
                contract_id = st.text_input("Contract ID (e.g., CT007)")
                
                customer_options = {f"{cust['CustomerID']}: {cust['CustomerName']}" for cust in customers}
                selected_customer = st.selectbox("Select Customer", options=customer_options)
                
                type_options = {f"{type_['InsuranceTypeID']}: {type_['InsuranceName']}" for type_ in insurance_types}
                selected_type = st.selectbox("Select Insurance Type", options=type_options)
                
                sign_date = st.date_input("Sign Date", value=datetime.date.today())
                
                submitted = st.form_submit_button("Create Contract")
                if submitted:
                    if contract_id and selected_customer and selected_type:
                        customer_id = selected_customer.split(':')[0].strip()
                        type_id = selected_type.split(':')[0].strip()
                        
                        save_contract(contract_id, customer_id, type_id, sign_date)
                    else:
                        st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
        else:
            st.warning("Customers or Insurance Types are missing in the database. Please add them first.")
        
        connection.close()

def save_contract(contract_id, customer_id, type_id, sign_date):
    """Save a new contract to the database"""
    connection = create_connection()
    if connection:
        insert_query = """
        INSERT INTO InsuranceContracts 
        (ContractID, CustomerID, InsuranceTypeID, SignDate) 
        VALUES (%s, %s, %s, %s)
        """
        data = (contract_id, customer_id, type_id, sign_date)
        result = execute_query(connection, insert_query, data)
        if result is not None:
            st.markdown('<div class="success-msg">Contract created successfully!</div>', unsafe_allow_html=True)
        connection.close()

def get_contracts():
    """Get all contracts from the database"""
    connection = create_connection()
    if connection:
        contracts = execute_query(connection, """
            SELECT c.ContractID, cust.CustomerName, t.InsuranceName
            FROM InsuranceContracts c
            JOIN Customers cust ON c.CustomerID = cust.CustomerID
            JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        """)
        connection.close()
        return contracts
    return []
