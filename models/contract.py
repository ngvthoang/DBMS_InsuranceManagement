import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection, execute_query, get_cached_data, execute_write_query
from models.customer import get_customers
from models.insurance_type import get_all_insurance_types
from mysql.connector import Error

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
    contracts = get_all_contracts()
    if contracts:
        df_contracts = pd.DataFrame(contracts)
        st.dataframe(df_contracts, use_container_width=True)
    else:
        st.info("No contracts found in the database.")

def create_contract_form():
    """Display the form to create a new contract"""
    # Initialize session state for success message
    if 'contract_created' not in st.session_state:
        st.session_state.contract_created = False
    
    # Show success message if contract was just created
    if st.session_state.contract_created:
        st.success("Contract created successfully!")
        st.session_state.contract_created = False
    
    customers = get_customers()
    insurance_types = get_all_insurance_types()
    
    if customers and insurance_types:
        with st.form("create_contract_form"):
            # Auto-generate next ID
            next_id = generate_next_contract_id()
            
            contract_id = st.text_input("Contract ID (e.g., CT007)", value=next_id)
            
            # Create proper dictionaries for dropdown selections
            customer_options = {f"{cust['CustomerID']}: {cust['CustomerName']}": cust['CustomerID'] for cust in customers}
            selected_customer = st.selectbox("Select Customer", options=list(customer_options.keys()))
            
            type_options = {f"{type_['InsuranceTypeID']}: {type_['InsuranceName']}": type_['InsuranceTypeID'] for type_ in insurance_types}
            selected_type = st.selectbox("Select Insurance Type", options=list(type_options.keys()))
            
            sign_date = st.date_input("Sign Date", value=datetime.date.today())
            
            submitted = st.form_submit_button("Create Contract")
            if submitted:
                if contract_id and selected_customer and selected_type:
                    customer_id = customer_options[selected_customer]
                    type_id = type_options[selected_type]
                    
                    if add_contract(contract_id, customer_id, type_id, sign_date):
                        st.session_state.contract_created = True
                        st.rerun()
                    else:
                        st.error("Failed to create contract.")
                else:
                    st.error("Please fill in all required fields.")
    else:
        st.warning("Customers or Insurance Types are missing in the database. Please add them first.")

def update_contract_form():
    """Display the form to update an existing contract"""
    # Initialize session state for success message
    if 'contract_updated' not in st.session_state:
        st.session_state.contract_updated = False
    
    # Show success message if contract was just updated
    if st.session_state.contract_updated:
        st.success("Contract updated successfully!")
        st.session_state.contract_updated = False
    
    contracts = get_contracts_dropdown()
    if contracts:
        selected_contract = st.selectbox("Select Contract to Edit", options=list(contracts.keys()))

        if selected_contract:
            contract_id = contracts[selected_contract]
            contract = get_contract_by_id(contract_id)

            if contract:
                with st.form("update_contract_form"):
                    customer_id = st.text_input("Customer ID", value=contract['CustomerID'])
                    insurance_type_id = st.text_input("Insurance Type ID", value=contract['InsuranceTypeID'])
                    sign_date = st.date_input("Sign Date", value=contract['SignDate'])
                    expiration_date = st.date_input("Expiration Date", value=contract['ExpirationDate'])

                    submitted = st.form_submit_button("Update Contract")
                    if submitted:
                        if customer_id and insurance_type_id and sign_date and expiration_date:
                            update_contract(contract_id, customer_id, insurance_type_id, sign_date, expiration_date)
                            st.session_state.contract_updated = True
                            st.rerun()
                        else:
                            st.error("Please fill in all required fields.")
    else:
        st.info("No contracts found in the database.")

def extend_contracts():
    """Display the interface for extending contract expiration dates"""
    nearing_expiration_contracts = get_expiring_contracts()
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
                    extend_contract(row['ContractID'], new_expiration_date)
            st.success("Selected contracts' expiration dates extended by 1 year!")
            st.experimental_rerun()  # Force a page refresh

        # Display the table
        st.dataframe(df_nearing_expiration[['ContractID', 'CustomerName', 'InsuranceName', 'SignDate', 'ExpirationDate']], use_container_width=True)
    else:
        st.info("No contracts nearing expiration within the next 3 months.")

@st.cache_data(ttl=300)
def get_all_contracts():
    """Get all contracts with customer and insurance type information"""
    query = """
        SELECT c.ContractID, c.CustomerID, cust.CustomerName, c.InsuranceTypeID, 
               t.InsuranceName, c.SignDate, c.ExpirationDate, c.Status
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_contract_by_id(contract_id):
    """Get a specific contract by ID"""
    query = """
        SELECT c.ContractID, c.CustomerID, cust.CustomerName, c.InsuranceTypeID, 
               t.InsuranceName, c.SignDate, c.ExpirationDate, c.Status
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        WHERE c.ContractID = %s
    """
    result = get_cached_data(query, (contract_id,))
    if result and len(result) > 0:
        return result[0]
    return None

@st.cache_data(ttl=300)
def get_contracts_dropdown():
    """Get contracts for dropdown selection"""
    query = """
        SELECT c.ContractID, cust.CustomerName, t.InsuranceName
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
    """
    contracts = get_cached_data(query)
    if not contracts:
        return {}
    return {f"{c['ContractID']}: {c['CustomerName']} - {c['InsuranceName']}": c['ContractID'] for c in contracts}

@st.cache_data(ttl=300)
def get_contracts_by_customer(customer_id):
    """Get all contracts for a specific customer"""
    query = """
        SELECT c.ContractID, t.InsuranceName, c.SignDate, c.ExpirationDate, c.Status
        FROM InsuranceContracts c
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        WHERE c.CustomerID = %s
        ORDER BY c.SignDate DESC
    """
    return get_cached_data(query, (customer_id,))

@st.cache_data(ttl=300)
def get_expiring_contracts():
    """Get contracts that are expiring within 3 months or have expired"""
    query = """
        SELECT c.ContractID, cust.CustomerName, t.InsuranceName, c.SignDate, c.ExpirationDate, c.Status
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        WHERE c.ExpirationDate BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 MONTH)
        OR (c.ExpirationDate < CURDATE() AND c.Status = 'Expired')
        ORDER BY c.ExpirationDate
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_contract_assessments(contract_id):
    """Get all assessments for a specific contract"""
    query = """
        SELECT AssessmentID, AssessmentDate, ClaimAmount, Result
        FROM Assessments
        WHERE ContractID = %s
        ORDER BY AssessmentDate DESC
    """
    return get_cached_data(query, (contract_id,))

@st.cache_data(ttl=300)
def get_contract_payouts(contract_id):
    """Get all payouts for a specific contract"""
    query = """
        SELECT PayoutID, PayoutDate, Amount, Status
        FROM Payouts
        WHERE ContractID = %s
        ORDER BY PayoutDate DESC
    """
    return get_cached_data(query, (contract_id,))

def generate_next_contract_id():
    """Generate the next contract ID"""
    last_contract = get_cached_data("SELECT ContractID FROM InsuranceContracts ORDER BY ContractID DESC LIMIT 1")
    next_id = "CT001"  # Default starting ID if no records exist
    
    if last_contract and len(last_contract) > 0:
        last_id = last_contract[0]['ContractID']
        # Extract the numeric part, increment it, and format it back
        try:
            id_num = int(last_id[2:])
            next_id = f"CT{(id_num + 1):03d}"
        except (ValueError, IndexError):
            pass  # Use default if parsing fails
    
    return next_id

def add_contract(contract_id, customer_id, insurance_type_id, sign_date):
    """Add a new contract to the database"""
    query = """
    INSERT INTO InsuranceContracts (ContractID, CustomerID, InsuranceTypeID, SignDate) 
    VALUES (%s, %s, %s, %s)
    """
    data = (contract_id, customer_id, insurance_type_id, sign_date)
    result = execute_write_query(query, data)
    
    # Clear cache for contract-related functions
    if hasattr(get_all_contracts, 'clear'):
        get_all_contracts.clear()
    if hasattr(get_contracts_dropdown, 'clear'):
        get_contracts_dropdown.clear()
    if hasattr(get_contracts_by_customer, 'clear'):
        get_contracts_by_customer.clear()
    if hasattr(get_expiring_contracts, 'clear'):
        get_expiring_contracts.clear()
    
    return result

def update_contract(contract_id, customer_id, insurance_type_id, sign_date, expiration_date):
    """Update an existing contract in the database"""
    query = """
    UPDATE InsuranceContracts 
    SET CustomerID = %s, InsuranceTypeID = %s, SignDate = %s, ExpirationDate = %s
    WHERE ContractID = %s
    """
    data = (customer_id, insurance_type_id, sign_date, expiration_date, contract_id)
    result = execute_write_query(query, data)
    
    # Clear cache for contract-related functions
    if hasattr(get_all_contracts, 'clear'):
        get_all_contracts.clear()
    if hasattr(get_contract_by_id, 'clear'):
        get_contract_by_id.clear()
    if hasattr(get_contracts_dropdown, 'clear'):
        get_contracts_dropdown.clear()
    if hasattr(get_contracts_by_customer, 'clear'):
        get_contracts_by_customer.clear()
    if hasattr(get_expiring_contracts, 'clear'):
        get_expiring_contracts.clear()
    
    return result

def extend_contract(contract_id, new_expiration_date):
    """Extend a contract's expiration date"""
    query = """
    UPDATE InsuranceContracts 
    SET ExpirationDate = %s, Status = 'Active'
    WHERE ContractID = %s
    """
    data = (new_expiration_date, contract_id)
    result = execute_write_query(query, data)
    
    # Clear cache for contract-related functions
    if hasattr(get_all_contracts, 'clear'):
        get_all_contracts.clear()
    if hasattr(get_contract_by_id, 'clear'):
        get_contract_by_id.clear()
    if hasattr(get_contracts_dropdown, 'clear'):
        get_contracts_dropdown.clear()
    if hasattr(get_contracts_by_customer, 'clear'):
        get_contracts_by_customer.clear()
    if hasattr(get_expiring_contracts, 'clear'):
        get_expiring_contracts.clear()
    
    return result
