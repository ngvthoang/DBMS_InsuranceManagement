import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import datetime
from PIL import Image
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

# Load environment variables
load_dotenv() 

# Database Configuration
def create_connection():
    """Create a database connection to MySQL server"""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "insurance_management"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "")
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

def execute_query(connection, query, data=None):
    """Execute SQL query and return result if it's a SELECT query"""
    cursor = connection.cursor()
    try:
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        
        if query.lower().strip().startswith("select"):
            columns = [column[0] for column in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return result
        else:
            connection.commit()
            return cursor.lastrowid
    except Error as e:
        st.error(f"Error executing query: {e}")
        return None
    finally:
        cursor.close()

# Set page config
st.set_page_config(
    page_title="Insurance Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 36px;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 24px;
        font-weight: bold;
        color: #2563EB;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .card {
        background-color: #EFF6FF;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .success-msg {
        background-color: #DCFCE7;
        color: #166534;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    .error-msg {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.markdown("# Insurance Management System 🏥")
st.sidebar.markdown("---")

# Navigation options
nav_option = st.sidebar.radio(
    "Navigate to:",
    [
        "Dashboard",
        "Customer Management",
        "Insurance Types",
        "Contract Management",
        "Claims & Assessments",
        "Payouts Management",
        "Reports"
    ]
)

# Main header
st.markdown('<div class="main-header">Insurance Management System</div>', unsafe_allow_html=True)

# Dashboard
if nav_option == "Dashboard":
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
        
        # Recent contracts
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

            # Configure AgGrid
            gb = GridOptionsBuilder.from_dataframe(df_contracts[['ContractID', 'CustomerName', 'InsuranceName', 'Period']])
            gb.configure_pagination(paginationAutoPageSize=True)  # Enable pagination
            gb.configure_side_bar()  # Enable a sidebar for filtering
            gb.configure_default_column(editable=True, filter=True)  # Enable filtering and editing
            grid_options = gb.build()

            # Display the interactive table
            AgGrid(
                df_contracts[['ContractID', 'CustomerName', 'InsuranceName', 'Period']],
                gridOptions=grid_options,
                enable_enterprise_modules=True,
                theme="blue",  # Theme options: "streamlit", "light", "dark", "blue", "fresh", "material"
                height=400,
                fit_columns_on_grid_load=True,
            )
        
        # Recent claims chart
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
        
        connection.close()

# Customer Management
elif nav_option == "Customer Management":
    st.markdown('<div class="sub-header">Customer Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["View Customers", "Add Customer", "Edit Customer"])
    
    # View Customers Tab
    with tab1:
        connection = create_connection()
        if connection:
            customers = execute_query(connection, "SELECT * FROM Customers")
            if customers:
                df_customers = pd.DataFrame(customers)

                # Configure AgGrid
                gb = GridOptionsBuilder.from_dataframe(df_customers)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_side_bar()
                gb.configure_default_column(editable=True, filter=True)
                grid_options = gb.build()

                # Display the interactive table
                AgGrid(
                    df_customers,
                    gridOptions=grid_options,
                    enable_enterprise_modules=True,
                    theme="blue",
                    height=400,
                    fit_columns_on_grid_load=True,
                )
            else:
                st.info("No customers found in the database.")
            connection.close()
    
    # Add Customer Tab
    with tab2:
        with st.form("add_customer_form"):
            connection = create_connection()
            if connection:
                next_id = "C001"  # Default starting ID if no records exist
                try:
                    last_customer = execute_query(connection, "SELECT CustomerID FROM Customers ORDER BY CustomerID DESC LIMIT 1")
                    if last_customer:
                        last_id = last_customer[0]['CustomerID']
                        next_id = f"C{int(last_id[1:]) + 1:03d}"
                except Error as e:
                    st.error(f"Error fetching last customer ID: {e}")
                finally:
                    connection.close()
            customer_id = st.text_input("Customer ID (e.g., C006)", value=next_id)
            customer_name = st.text_input("Customer Name")
            address = st.text_area("Address")
            phone = st.text_input("Phone Number")
            
            submitted = st.form_submit_button("Add Customer")
            if submitted:
                if customer_id and customer_name and address and phone:
                    connection = create_connection()
                    if connection:
                        insert_query = """
                        INSERT INTO Customers (CustomerID, CustomerName, Address, PhoneNumber) 
                        VALUES (%s, %s, %s, %s)
                        """
                        data = (customer_id, customer_name, address, phone)
                        result = execute_query(connection, insert_query, data)
                        if result is not None:
                            st.markdown('<div class="success-msg">Customer added successfully!</div>', unsafe_allow_html=True)
                        connection.close()
                else:
                    st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
    
    # Edit Customer Tab
    with tab3:
        connection = create_connection()
        if connection:
            customers = execute_query(connection, "SELECT CustomerID, CustomerName FROM Customers")
            if customers:
                customer_options = {f"{cust['CustomerID']}: {cust['CustomerName']}" for cust in customers}
                selected_customer = st.selectbox("Select Customer to Edit", options=customer_options)
                
                if selected_customer:
                    customer_id = selected_customer.split(':')[0].strip()
                    customer_data = execute_query(connection, "SELECT * FROM Customers WHERE CustomerID = %s", (customer_id,))
                    
                    if customer_data:
                        customer = customer_data[0]
                        with st.form("edit_customer_form"):
                            customer_name = st.text_input("Customer Name", value=customer['CustomerName'])
                            address = st.text_area("Address", value=customer['Address'])
                            phone = st.text_input("Phone Number", value=customer['PhoneNumber'])
                            
                            submitted = st.form_submit_button("Update Customer")
                            if submitted:
                                if customer_name and address and phone:
                                    update_query = """
                                    UPDATE Customers 
                                    SET CustomerName = %s, Address = %s, PhoneNumber = %s
                                    WHERE CustomerID = %s
                                    """
                                    data = (customer_name, address, phone, customer_id)
                                    result = execute_query(connection, update_query, data)
                                    if result is not None:
                                        st.markdown('<div class="success-msg">Customer updated successfully!</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
            else:
                st.info("No customers found in the database.")
            connection.close()

# Insurance Types
elif nav_option == "Insurance Types":
    st.markdown('<div class="sub-header">Insurance Types Management</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Insurance Types", "Add Insurance Type"])
    
    # View Insurance Types Tab
    with tab1:
        connection = create_connection()
        if connection:
            insurance_types = execute_query(connection, "SELECT * FROM InsuranceTypes")
            if insurance_types:
                df_types = pd.DataFrame(insurance_types)

                # Configure AgGrid
                gb = GridOptionsBuilder.from_dataframe(df_types)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_side_bar()
                gb.configure_default_column(editable=True, filter=True)
                grid_options = gb.build()

                # Display the interactive table
                AgGrid(
                    df_types,
                    gridOptions=grid_options,
                    enable_enterprise_modules=True,
                    theme="blue",
                    height=400,
                    fit_columns_on_grid_load=True,
                )
            else:
                st.info("No insurance types found in the database.")
            connection.close()
    
    # Add Insurance Type Tab
    with tab2:
        with st.form("add_insurance_type_form"):
            connection = create_connection()
            if connection:
                next_id = "T001"  # Default starting ID if no records exist
                try:
                    last_type = execute_query(connection, "SELECT InsuranceTypeID FROM InsuranceTypes ORDER BY InsuranceTypeID DESC LIMIT 1")
                    if last_type:
                        last_id = last_type[0]['InsuranceTypeID']
                        next_id = f"T{int(last_id[1:]) + 1:03d}"
                except Error as e:
                    st.error(f"Error fetching last insurance type ID: {e}")
                finally:
                    connection.close()
            type_id = st.text_input("Insurance Type ID (e.g., T006)", value=next_id)
            type_name = st.text_input("Insurance Name")
            description = st.text_area("Description")
            
            submitted = st.form_submit_button("Add Insurance Type")
            if submitted:
                if type_id and type_name and description:
                    connection = create_connection()
                    if connection:
                        insert_query = """
                        INSERT INTO InsuranceTypes (InsuranceTypeID, InsuranceName, Description) 
                        VALUES (%s, %s, %s)
                        """
                        data = (type_id, type_name, description)
                        result = execute_query(connection, insert_query, data)
                        if result is not None:
                            st.markdown('<div class="success-msg">Insurance Type added successfully!</div>', unsafe_allow_html=True)
                        connection.close()
                else:
                    st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)

# Contract Management
elif nav_option == "Contract Management":
    st.markdown('<div class="sub-header">Contract Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["View Contracts", "Create Contract", "Update Contract", "Contract Extension"])
    
    # View Contracts Tab
    with tab1:
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
    
    # Create Contract Tab
    with tab2:
        connection = create_connection()
        if connection:
            customers = execute_query(connection, "SELECT CustomerID, CustomerName FROM Customers")
            insurance_types = execute_query(connection, "SELECT InsuranceTypeID, InsuranceName FROM InsuranceTypes")
            
            if customers and insurance_types:
                with st.form("create_contract_form"):
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
                            
                            insert_query = """
                            INSERT INTO InsuranceContracts 
                            (ContractID, CustomerID, InsuranceTypeID, SignDate) 
                            VALUES (%s, %s, %s, %s)
                            """
                            data = (contract_id, customer_id, type_id, sign_date)
                            result = execute_query(connection, insert_query, data)
                            if result is not None:
                                st.markdown('<div class="success-msg">Contract created successfully!</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
            else:
                st.warning("Customers or Insurance Types are missing in the database. Please add them first.")
            
            connection.close()

    #Update the contract
    with tab3:
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
                                    update_query = """
                                    UPDATE InsuranceContracts 
                                    SET CustomerID = %s, InsuranceTypeID = %s, SignDate = %s, ExpirationDate = %s
                                    WHERE ContractID = %s
                                    """
                                    data = (customer_id, insurance_type_id, sign_date, expiration_date, contract_id)
                                    result = execute_query(connection, update_query, data)
                                    if result is not None:
                                        st.markdown('<div class="success-msg">Contract updated successfully!</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
            else:
                st.info("No contracts found in the database.")
            connection.close()
    
    # Contract Extension Tab
    with tab4:
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
                    st.session_state["refresh_contracts"] = True  # Set the refresh flag

                # Display the table
                st.dataframe(df_nearing_expiration[['ContractID', 'CustomerName', 'InsuranceName', 'SignDate', 'ExpirationDate']])
            else:
                st.info("No contracts nearing expiration within the next 3 months.")
            connection.close()

        # Check the refresh flag at the beginning of the tab
        if "refresh_contracts" in st.session_state and st.session_state["refresh_contracts"]:
            st.session_state["refresh_contracts"] = False  # Clear the refresh flag


# Claims & Assessments
elif nav_option == "Claims & Assessments":
    st.markdown('<div class="sub-header">Claims & Assessments Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["View Claims", "File New Claim", "Pending Claims"])
    
    # View Claims Tab
    with tab1:
        connection = create_connection()
        if connection:
            claims = execute_query(connection, """
                SELECT a.AssessmentID, c.ContractID, cust.CustomerName, 
                       a.AssessmentDate, a.Result, a.ClaimAmount
                FROM Assessments a
                JOIN InsuranceContracts c ON a.ContractID = c.ContractID
                JOIN Customers cust ON c.CustomerID = cust.CustomerID
                ORDER BY a.AssessmentDate DESC
            """)
            if claims:
                df_claims = pd.DataFrame(claims)

                # Configure AgGrid
                gb = GridOptionsBuilder.from_dataframe(df_claims)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_side_bar()
                gb.configure_default_column(editable=True, filter=True)
                grid_options = gb.build()

                # Display the interactive table
                AgGrid(
                    df_claims,
                    gridOptions=grid_options,
                    enable_enterprise_modules=True,
                    theme="blue",
                    height=400,
                    fit_columns_on_grid_load=True,
                )
            else:
                st.info("No claims found in the database.")
            connection.close()
    
    # File New Claim Tab
    with tab2:
        connection = create_connection()
        if connection:
            contracts = execute_query(connection, """
                SELECT c.ContractID, cust.CustomerName, t.InsuranceName
                FROM InsuranceContracts c
                JOIN Customers cust ON c.CustomerID = cust.CustomerID
                JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
            """)
            
            if contracts:
                with st.form("file_claim_form"):
                    next_id = "A001"  # Default starting ID if no records exist
                    try:
                        last_assessment = execute_query(connection, "SELECT AssessmentID FROM Assessments ORDER BY AssessmentID DESC LIMIT 1")
                        if last_assessment:
                            last_id = last_assessment[0]['AssessmentID']
                            next_id = f"A{int(last_id[1:]) + 1:03d}"
                    except Error as e:
                        st.error(f"Error fetching last assessment ID: {e}")
                    
                    assessment_id = st.text_input("Assessment ID (e.g., A006)", value=next_id)
                    
                    contract_options = {f"{contract['ContractID']}: {contract['CustomerName']} - {contract['InsuranceName']}" for contract in contracts}
                    selected_contract = st.selectbox("Select Contract", options=contract_options)
                    
                    assessment_date = st.date_input("Assessment Date", value=datetime.date.today())
                    
                    amount = st.number_input("Claim Amount ($)", min_value=0.0, value=0.0, step=100.0)
                
                    result_options = ["Pending", "Approved", "Rejected"]
                    result = st.selectbox("Assessment Result", options=result_options)
                    
                    submitted = st.form_submit_button("File Claim")
                    if submitted:
                        if assessment_id and selected_contract and amount > 0:
                            contract_id = selected_contract.split(':')[0].strip()
                            
                            insert_query = """
                            INSERT INTO Assessments 
                            (AssessmentID, ContractID, AssessmentDate, ClaimAmount, Result) 
                            VALUES (%s, %s, %s, %s, %s)
                            """
                            data = (assessment_id, contract_id, assessment_date, amount, result)
                            result_exec = execute_query(connection, insert_query, data)
                            if result_exec is not None:
                                st.markdown('<div class="success-msg">Claim filed successfully!</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="error-msg">Please fill in all the required fields and ensure the amount is greater than 0.</div>', unsafe_allow_html=True)
            else:
                st.warning("No contracts found in the database.")
            
            connection.close()
    # Claim need to action
    # Pending Claims Tab
    with tab3:
        connection = create_connection()
        if connection:
            pending_claims = execute_query(connection, """
                SELECT a.AssessmentID, c.ContractID, cust.CustomerName, 
                       a.AssessmentDate, a.ClaimAmount, a.Result
                FROM Assessments a
                JOIN InsuranceContracts c ON a.ContractID = c.ContractID
                JOIN Customers cust ON c.CustomerID = cust.CustomerID
                WHERE a.Result = 'Pending'
            """)
            if pending_claims:
                df_pending_claims = pd.DataFrame(pending_claims)

                # Add a dropdown for each row to adjust the result
                df_pending_claims['Action'] = df_pending_claims['AssessmentID'].apply(
                    lambda x: st.selectbox(f"Action for {x}", ["Pending", "Approved", "Rejected"], key=f"action_{x}")
                )

                # Submit button to update the database
                if st.button("Update Results"):
                    for index, row in df_pending_claims.iterrows():
                        if row['Action'] != "Pending":
                            update_query = """
                            UPDATE Assessments 
                            SET Result = %s 
                            WHERE AssessmentID = %s
                            """
                            execute_query(connection, update_query, (row['Action'], row['AssessmentID']))
                    st.success("Pending claims updated successfully!")
                    st.query_params = {"updated": "true"}  # Simulate a refresh

                # Display the table
                st.dataframe(df_pending_claims[['AssessmentID', 'ContractID', 'CustomerName', 'AssessmentDate', 'ClaimAmount', 'Action']])
            else:
                st.info("No pending claims found.")
            connection.close()

# Payouts Management
elif nav_option == "Payouts Management":
    st.markdown('<div class="sub-header">Payouts Management</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Payouts", "Process New Payout"])
    
    # View Payouts Tab
    with tab1:
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
    
    # Process New Payout Tab
    with tab2:
        connection = create_connection()
        if connection:
            approved_claims = execute_query(connection, """
                SELECT a.ContractID, cust.CustomerName, a.AssessmentDate
                FROM Assessments a
                JOIN InsuranceContracts c ON a.ContractID = c.ContractID
                JOIN Customers cust ON c.CustomerID = cust.CustomerID
                WHERE a.Result = 'Approved' AND a.ContractID NOT IN (SELECT ContractID FROM Payouts)
            """)
            
            if approved_claims:
                with st.form("process_payout_form"):
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
                            
                            insert_query = """
                            INSERT INTO Payouts 
                            (PayoutID, ContractID, Amount, PayoutDate) 
                            VALUES (%s, %s, %s, %s)
                            """
                            data = (payout_id, contract_id, amount, payout_date)
                            result = execute_query(connection, insert_query, data)
                            if result is not None:
                                st.markdown('<div class="success-msg">Payout processed successfully!</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
            else:
                st.warning("No approved claims without payouts found in the database.")
            
            connection.close()

# Reports
elif nav_option == "Reports":
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
            
        elif report_type == "Claims Analysis":
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
            
        elif report_type == "Payout Summary":
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
            
        elif report_type == "Customer Activity":
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
        
        connection.close()
