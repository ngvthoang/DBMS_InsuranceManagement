import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection, execute_query
from models.customer import get_customers
from models.insurance_type import get_insurance_types
from mysql.connector import Error
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

def display_contract_management():
    """Display the contract management section"""
    st.markdown('<div class="sub-header">Contract Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["View Contracts", "Create Contract", "Update Contract", "Contract Extension"])
    
    # View Contracts Tab
    with tab1:
        display_contracts()
    
    # Create Contract Tab
    with tab2:
        create_contract_form()
        
    # Update Contract Tab
    with tab3:
        update_contract_form()
        
    # Contract Extension Tab
    with tab4:
        extend_contracts()

def display_contracts():
    """Display a table of all contracts"""
    connection = create_connection()
    if connection:
        contracts = execute_query(connection, """
            SELECT c.ContractID, cust.CustomerName, t.InsuranceName, c.SignDate, c.ExpirationDate, c.Status
            FROM InsuranceContracts c
            JOIN Customers cust ON c.CustomerID = cust.CustomerID
            JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        """)
        if contracts:
            df_contracts = pd.DataFrame(contracts)
            
            # Configure AgGrid
            gb = GridOptionsBuilder.from_dataframe(df_contracts)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_side_bar()
            gb.configure_default_column(editable=True, filter=True)
            grid_options = gb.build()

            # Display the interactive table
            AgGrid(
                df_contracts,
                gridOptions=grid_options,
                enable_enterprise_modules=True,
                theme="blue",
                height=400,
                fit_columns_on_grid_load=True,
            )
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
                # Auto-generate next ID
                next_id = "CT001"  # Default starting ID if no records exist
                try:
                    last_contract = execute_query(connection, "SELECT ContractID FROM InsuranceContracts ORDER BY ContractID DESC LIMIT 1")
                    if last_contract:
                        last_id = last_contract[0]['ContractID']
                        next_id = f"CT{int(last_id[2:]) + 1:03d}"
                except Error as e:
                    st.error(f"Error fetching last contract ID: {e}")
                
                contract_id = st.text_input("Contract ID (e.g., CT007)", value=next_id)
                
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

def update_contract_form():
    """Display the form to update an existing contract"""
    connection = create_connection()
    if connection:
        contracts = execute_query(connection, """
            SELECT c.ContractID, cust.CustomerName, t.InsuranceName, c.SignDate, c.ExpirationDate
            FROM InsuranceContracts c
            JOIN Customers cust ON c.CustomerID = cust.CustomerID
            JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        """)
        if contracts:
            contract_options = {f"{contract['ContractID']}: {contract['CustomerName']} - {contract['InsuranceName']}" for contract in contracts}
            selected_contract = st.selectbox("Select Contract to Edit", options=contract_options)

            if selected_contract:
                contract_id = selected_contract.split(':')[0].strip()
                contract_data = execute_query(connection, "SELECT * FROM InsuranceContracts WHERE ContractID = %s", (contract_id,))

                if contract_data:
                    contract = contract_data[0]
                    with st.form("update_contract_form"):
                        customer_id = st.text_input("Customer ID", value=contract['CustomerID'])
                        insurance_type_id = st.text_input("Insurance Type ID", value=contract['InsuranceTypeID'])
                        sign_date = st.date_input("Sign Date", value=contract['SignDate'])
                        expiration_date = st.date_input("Expiration Date", value=contract['ExpirationDate'])

                        submitted = st.form_submit_button("Update Contract")
                        if submitted:
                            if customer_id and insurance_type_id and sign_date and expiration_date:
                                update_contract(contract_id, customer_id, insurance_type_id, sign_date, expiration_date)
                            else:
                                st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
        else:
            st.info("No contracts found in the database.")
        connection.close()

def extend_contracts():
    """Display the interface for extending contract expiration dates"""
    connection = create_connection()
    if connection:
        # Fetch contracts nearing expiration (within 3 months)
        nearing_expiration_contracts = execute_query(connection, """
            SELECT c.ContractID, cust.CustomerName, t.InsuranceName, c.SignDate, c.ExpirationDate
            FROM InsuranceContracts c
            JOIN Customers cust ON c.CustomerID = cust.CustomerID
            JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
            WHERE c.ExpirationDate BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 MONTH)
            OR c.ExpirationDate < CURDATE()
        """)
        if nearing_expiration_contracts:
            df_nearing_expiration = pd.DataFrame(nearing_expiration_contracts)

            # Add a checkbox for each row to extend the expiration date
            df_nearing_expiration['Extend Expiration'] = df_nearing_expiration['ContractID'].apply(
                lambda x: st.checkbox(f"Extend expiration for {x}", key=f"extend_{x}")
            )

            # Submit button to update the expiration dates
            if st.button("Extend Expiration Dates"):
                for index, row in df_nearing_expiration.iterrows():
                    if row['Extend Expiration']:
                        new_expiration_date = row['ExpirationDate'] + datetime.timedelta(days=365)
                        update_query = """
                        UPDATE InsuranceContracts 
                        SET ExpirationDate = %s 
                        WHERE ContractID = %s
                        """
                        execute_query(connection, update_query, (new_expiration_date, row['ContractID']))
                st.success("Selected contracts' expiration dates extended by 1 year!")
                st.experimental_rerun()  # Force a page refresh

            # Display the table
            st.dataframe(df_nearing_expiration[['ContractID', 'CustomerName', 'InsuranceName', 'SignDate', 'ExpirationDate']])
        else:
            st.info("No contracts nearing expiration within the next 3 months.")
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

def update_contract(contract_id, customer_id, type_id, sign_date, expiration_date):
    """Update an existing contract in the database"""
    connection = create_connection()
    if connection:
        update_query = """
        UPDATE InsuranceContracts 
        SET CustomerID = %s, InsuranceTypeID = %s, SignDate = %s, ExpirationDate = %s
        WHERE ContractID = %s
        """
        data = (customer_id, type_id, sign_date, expiration_date, contract_id)
        result = execute_query(connection, update_query, data)
        if result is not None:
            st.markdown('<div class="success-msg">Contract updated successfully!</div>', unsafe_allow_html=True)
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
