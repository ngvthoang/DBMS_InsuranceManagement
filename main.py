import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import datetime
from PIL import Image

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
        active_contracts = execute_query(connection, "SELECT COUNT(*) AS count FROM InsuranceContracts WHERE Status = 'Active'")
        if active_contracts:
            col2.metric("Active Contracts", active_contracts[0]['count'])
        
        # Pending Claims
        pending_claims = execute_query(connection, "SELECT COUNT(*) AS count FROM Assessments WHERE Status = 'Pending'")
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
            SELECT c.ContractID, cust.FirstName, cust.LastName, c.StartDate, c.EndDate, c.Status, t.TypeName
            FROM InsuranceContracts c
            JOIN Customers cust ON c.CustomerID = cust.CustomerID
            JOIN InsuranceTypes t ON c.TypeID = t.TypeID
            ORDER BY c.StartDate DESC LIMIT 5
        """)
        if recent_contracts:
            df_contracts = pd.DataFrame(recent_contracts)
            df_contracts['Customer'] = df_contracts['FirstName'] + ' ' + df_contracts['LastName']
            df_contracts['Period'] = df_contracts['StartDate'].astype(str) + ' to ' + df_contracts['EndDate'].astype(str)
            st.dataframe(df_contracts[['ContractID', 'Customer', 'TypeName', 'Period', 'Status']], use_container_width=True)
        
        # Recent claims chart
        st.markdown('<div class="sub-header">Claims by Insurance Type</div>', unsafe_allow_html=True)
        claims_by_type = execute_query(connection, """
            SELECT t.TypeName, COUNT(a.AssessmentID) as ClaimCount
            FROM Assessments a
            JOIN InsuranceContracts c ON a.ContractID = c.ContractID
            JOIN InsuranceTypes t ON c.TypeID = t.TypeID
            GROUP BY t.TypeName
        """)
        if claims_by_type:
            df_claims = pd.DataFrame(claims_by_type)
            fig = px.pie(df_claims, values='ClaimCount', names='TypeName', title='Claims Distribution by Insurance Type')
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
                st.dataframe(df_customers, use_container_width=True)
            else:
                st.info("No customers found in the database.")
            connection.close()
    
    # Add Customer Tab
    with tab2:
        with st.form("add_customer_form"):
            col1, col2 = st.columns(2)
            first_name = col1.text_input("First Name")
            last_name = col2.text_input("Last Name")
            
            col1, col2 = st.columns(2)
            email = col1.text_input("Email")
            phone = col2.text_input("Phone")
            
            col1, col2 = st.columns(2)
            address = col1.text_area("Address")
            date_of_birth = col2.date_input("Date of Birth", min_value=datetime.date(1920, 1, 1))
            
            submitted = st.form_submit_button("Add Customer")
            if submitted:
                if first_name and last_name and email and phone and address:
                    connection = create_connection()
                    if connection:
                        insert_query = """
                        INSERT INTO Customers (FirstName, LastName, Email, Phone, Address, DateOfBirth) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        data = (first_name, last_name, email, phone, address, date_of_birth)
                        result = execute_query(connection, insert_query, data)
                        if result:
                            st.markdown('<div class="success-msg">Customer added successfully!</div>', unsafe_allow_html=True)
                        connection.close()
                else:
                    st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
    
    # Edit Customer Tab
    with tab3:
        connection = create_connection()
        if connection:
            customers = execute_query(connection, "SELECT CustomerID, FirstName, LastName, Email FROM Customers")
            if customers:
                customer_options = {f"{cust['CustomerID']}: {cust['FirstName']} {cust['LastName']}" for cust in customers}
                selected_customer = st.selectbox("Select Customer to Edit", options=customer_options)
                
                if selected_customer:
                    customer_id = int(selected_customer.split(':')[0])
                    customer_data = execute_query(connection, "SELECT * FROM Customers WHERE CustomerID = %s", (customer_id,))
                    
                    if customer_data:
                        customer = customer_data[0]
                        with st.form("edit_customer_form"):
                            col1, col2 = st.columns(2)
                            first_name = col1.text_input("First Name", value=customer['FirstName'])
                            last_name = col2.text_input("Last Name", value=customer['LastName'])
                            
                            col1, col2 = st.columns(2)
                            email = col1.text_input("Email", value=customer['Email'])
                            phone = col2.text_input("Phone", value=customer['Phone'])
                            
                            col1, col2 = st.columns(2)
                            address = col1.text_area("Address", value=customer['Address'])
                            date_of_birth = col2.date_input("Date of Birth", 
                                                         value=customer['DateOfBirth'] if 'DateOfBirth' in customer else datetime.date.today(),
                                                         min_value=datetime.date(1920, 1, 1))
                            
                            submitted = st.form_submit_button("Update Customer")
                            if submitted:
                                if first_name and last_name and email and phone and address:
                                    update_query = """
                                    UPDATE Customers 
                                    SET FirstName = %s, LastName = %s, Email = %s, Phone = %s, Address = %s, DateOfBirth = %s
                                    WHERE CustomerID = %s
                                    """
                                    data = (first_name, last_name, email, phone, address, date_of_birth, customer_id)
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
                st.dataframe(df_types, use_container_width=True)
            else:
                st.info("No insurance types found in the database.")
            connection.close()
    
    # Add Insurance Type Tab
    with tab2:
        with st.form("add_insurance_type_form"):
            type_name = st.text_input("Type Name")
            description = st.text_area("Description")
            coverage_details = st.text_area("Coverage Details")
            premium_rate = st.number_input("Premium Rate (%)", min_value=0.0, max_value=100.0, step=0.1)
            
            submitted = st.form_submit_button("Add Insurance Type")
            if submitted:
                if type_name and description and coverage_details and premium_rate:
                    connection = create_connection()
                    if connection:
                        insert_query = """
                        INSERT INTO InsuranceTypes (TypeName, Description, CoverageDetails, PremiumRate) 
                        VALUES (%s, %s, %s, %s)
                        """
                        data = (type_name, description, coverage_details, premium_rate)
                        result = execute_query(connection, insert_query, data)
                        if result:
                            st.markdown('<div class="success-msg">Insurance Type added successfully!</div>', unsafe_allow_html=True)
                        connection.close()
                else:
                    st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)

# Contract Management
elif nav_option == "Contract Management":
    st.markdown('<div class="sub-header">Contract Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["View Contracts", "Create Contract", "Update Contract Status"])
    
    # View Contracts Tab
    with tab1:
        connection = create_connection()
        if connection:
            contracts = execute_query(connection, """
                SELECT c.ContractID, CONCAT(cust.FirstName, ' ', cust.LastName) AS CustomerName, 
                       t.TypeName, c.StartDate, c.EndDate, c.PremiumAmount, c.Status
                FROM InsuranceContracts c
                JOIN Customers cust ON c.CustomerID = cust.CustomerID
                JOIN InsuranceTypes t ON c.TypeID = t.TypeID
            """)
            if contracts:
                df_contracts = pd.DataFrame(contracts)
                st.dataframe(df_contracts, use_container_width=True)
            else:
                st.info("No contracts found in the database.")
            connection.close()
    
    # Create Contract Tab
    with tab2:
        connection = create_connection()
        if connection:
            customers = execute_query(connection, "SELECT CustomerID, CONCAT(FirstName, ' ', LastName) AS CustomerName FROM Customers")
            insurance_types = execute_query(connection, "SELECT TypeID, TypeName FROM InsuranceTypes")
            
            if customers and insurance_types:
                with st.form("create_contract_form"):
                    customer_options = {f"{cust['CustomerID']}: {cust['CustomerName']}" for cust in customers}
                    selected_customer = st.selectbox("Select Customer", options=customer_options)
                    
                    type_options = {f"{type_['TypeID']}: {type_['TypeName']}" for type_ in insurance_types}
                    selected_type = st.selectbox("Select Insurance Type", options=type_options)
                    
                    col1, col2 = st.columns(2)
                    start_date = col1.date_input("Start Date", min_value=datetime.date.today())
                    # Default end date is one year from start
                    default_end = datetime.date.today() + datetime.timedelta(days=365)
                    end_date = col2.date_input("End Date", value=default_end, min_value=start_date)
                    
                    premium_amount = st.number_input("Premium Amount ($)", min_value=0.0, step=10.0)
                    
                    status_options = ["Active", "Pending", "Expired", "Cancelled"]
                    status = st.selectbox("Status", options=status_options, index=0)
                    
                    coverage_amount = st.number_input("Coverage Amount ($)", min_value=0.0, step=1000.0)
                    
                    terms_conditions = st.text_area("Terms and Conditions")
                    
                    submitted = st.form_submit_button("Create Contract")
                    if submitted:
                        if selected_customer and selected_type and premium_amount > 0 and coverage_amount > 0:
                            customer_id = int(selected_customer.split(':')[0])
                            type_id = int(selected_type.split(':')[0])
                            
                            insert_query = """
                            INSERT INTO InsuranceContracts 
                            (CustomerID, TypeID, StartDate, EndDate, PremiumAmount, CoverageAmount, Status, TermsConditions) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            data = (customer_id, type_id, start_date, end_date, premium_amount, coverage_amount, status, terms_conditions)
                            result = execute_query(connection, insert_query, data)
                            if result:
                                st.markdown('<div class="success-msg">Contract created successfully!</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
            else:
                st.warning("Customers or Insurance Types are missing in the database. Please add them first.")
            
            connection.close()
    
    # Update Contract Status Tab
    with tab3:
        connection = create_connection()
        if connection:
            contracts = execute_query(connection, """
                SELECT c.ContractID, CONCAT(cust.FirstName, ' ', cust.LastName) AS CustomerName, 
                       t.TypeName, c.Status
                FROM InsuranceContracts c
                JOIN Customers cust ON c.CustomerID = cust.CustomerID
                JOIN InsuranceTypes t ON c.TypeID = t.TypeID
            """)
            
            if contracts:
                contract_options = {f"{contract['ContractID']}: {contract['CustomerName']} - {contract['TypeName']}" for contract in contracts}
                selected_contract = st.selectbox("Select Contract to Update", options=contract_options)
                
                if selected_contract:
                    contract_id = int(selected_contract.split(':')[0])
                    current_status = next((c['Status'] for c in contracts if c['ContractID'] == contract_id), None)
                    
                    status_options = ["Active", "Pending", "Expired", "Cancelled"]
                    new_status = st.selectbox("New Status", options=status_options, index=status_options.index(current_status) if current_status in status_options else 0)
                    
                    if st.button("Update Status"):
                        update_query = """
                        UPDATE InsuranceContracts 
                        SET Status = %s
                        WHERE ContractID = %s
                        """
                        data = (new_status, contract_id)
                        result = execute_query(connection, update_query, data)
                        if result is not None:
                            st.markdown('<div class="success-msg">Contract status updated successfully!</div>', unsafe_allow_html=True)
            else:
                st.info("No contracts found in the database.")
            
            connection.close()

# Claims & Assessments
elif nav_option == "Claims & Assessments":
    st.markdown('<div class="sub-header">Claims & Assessments Management</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Claims", "File New Claim"])
    
    # View Claims Tab
    with tab1:
        connection = create_connection()
        if connection:
            claims = execute_query(connection, """
                SELECT a.AssessmentID, c.ContractID, CONCAT(cust.FirstName, ' ', cust.LastName) AS CustomerName, 
                       a.ClaimDate, a.DamageDescription, a.ClaimAmount, a.Status
                FROM Assessments a
                JOIN InsuranceContracts c ON a.ContractID = c.ContractID
                JOIN Customers cust ON c.CustomerID = cust.CustomerID
                ORDER BY a.ClaimDate DESC
            """)
            if claims:
                df_claims = pd.DataFrame(claims)
                st.dataframe(df_claims, use_container_width=True)
            else:
                st.info("No claims found in the database.")
            connection.close()
    
    # File New Claim Tab
    with tab2:
        connection = create_connection()
        if connection:
            contracts = execute_query(connection, """
                SELECT c.ContractID, CONCAT(cust.FirstName, ' ', cust.LastName) AS CustomerName, 
                       t.TypeName
                FROM InsuranceContracts c
                JOIN Customers cust ON c.CustomerID = cust.CustomerID
                JOIN InsuranceTypes t ON c.TypeID = t.TypeID
                WHERE c.Status = 'Active'
            """)
            
            if contracts:
                with st.form("file_claim_form"):
                    contract_options = {f"{contract['ContractID']}: {contract['CustomerName']} - {contract['TypeName']}" for contract in contracts}
                    selected_contract = st.selectbox("Select Contract", options=contract_options)
                    
                    claim_date = st.date_input("Claim Date", value=datetime.date.today(), max_value=datetime.date.today())
                    
                    damage_description = st.text_area("Damage Description")
                    
                    claim_amount = st.number_input("Claim Amount ($)", min_value=0.0, step=100.0)
                    
                    status_options = ["Pending", "Under Review", "Approved", "Rejected"]
                    status = st.selectbox("Claim Status", options=status_options, index=0)
                    
                    assessor_notes = st.text_area("Assessor Notes (optional)")
                    
                    submitted = st.form_submit_button("File Claim")
                    if submitted:
                        if selected_contract and damage_description and claim_amount > 0:
                            contract_id = int(selected_contract.split(':')[0])
                            
                            insert_query = """
                            INSERT INTO Assessments 
                            (ContractID, ClaimDate, DamageDescription, ClaimAmount, Status, AssessorNotes) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """
                            data = (contract_id, claim_date, damage_description, claim_amount, status, assessor_notes)
                            result = execute_query(connection, insert_query, data)
                            if result:
                                st.markdown('<div class="success-msg">Claim filed successfully!</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
            else:
                st.warning("No active contracts found in the database.")
            
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
                SELECT p.PayoutID, a.AssessmentID, CONCAT(cust.FirstName, ' ', cust.LastName) AS CustomerName, 
                       p.PayoutDate, p.Amount, p.Status
                FROM Payouts p
                JOIN Assessments a ON p.AssessmentID = a.AssessmentID
                JOIN InsuranceContracts c ON a.ContractID = c.ContractID
                JOIN Customers cust ON c.CustomerID = cust.CustomerID
                ORDER BY p.PayoutDate DESC
            """)
            if payouts:
                df_payouts = pd.DataFrame(payouts)
                st.dataframe(df_payouts, use_container_width=True)
            else:
                st.info("No payouts found in the database.")
            connection.close()
    
    # Process New Payout Tab
    with tab2:
        connection = create_connection()
        if connection:
            approved_claims = execute_query(connection, """
                SELECT a.AssessmentID, CONCAT(cust.FirstName, ' ', cust.LastName) AS CustomerName, 
                       a.ClaimDate, a.ClaimAmount
                FROM Assessments a
                JOIN InsuranceContracts c ON a.ContractID = c.ContractID
                JOIN Customers cust ON c.CustomerID = cust.CustomerID
                WHERE a.Status = 'Approved' AND a.AssessmentID NOT IN (SELECT AssessmentID FROM Payouts)
            """)
            
            if approved_claims:
                with st.form("process_payout_form"):
                    claim_options = {f"{claim['AssessmentID']}: {claim['CustomerName']} - ${claim['ClaimAmount']}" for claim in approved_claims}
                    selected_claim = st.selectbox("Select Approved Claim", options=claim_options)
                    
                    payout_date = st.date_input("Payout Date", value=datetime.date.today())
                    
                    # Default amount is the claim amount
                    if selected_claim:
                        assessment_id = int(selected_claim.split(':')[0])
                        default_amount = next((c['ClaimAmount'] for c in approved_claims if c['AssessmentID'] == assessment_id), 0)
                    else:
                        default_amount = 0
                        
                    amount = st.number_input("Payout Amount ($)", min_value=0.0, value=default_amount, step=100.0)
                    
                    status_options = ["Processed", "Pending", "Completed"]
                    status = st.selectbox("Payout Status", options=status_options, index=0)
                    
                    payment_method_options = ["Bank Transfer", "Check", "Direct Deposit"]
                    payment_method = st.selectbox("Payment Method", options=payment_method_options)
                    
                    notes = st.text_area("Notes (optional)")
                    
                    submitted = st.form_submit_button("Process Payout")
                    if submitted:
                        if selected_claim and amount > 0:
                            assessment_id = int(selected_claim.split(':')[0])
                            
                            insert_query = """
                            INSERT INTO Payouts 
                            (AssessmentID, PayoutDate, Amount, Status, PaymentMethod, Notes) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """
                            data = (assessment_id, payout_date, amount, status, payment_method, notes)
                            result = execute_query(connection, insert_query, data)
                            if result:
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
            "Customer Activity",
            "Revenue Analysis"
        ]
    )
    
    connection = create_connection()
    if connection:
        if report_type == "Contracts Summary":
            st.markdown('<div class="sub-header">Contracts Summary Report</div>', unsafe_allow_html=True)
            
            # Status distribution
            status_data = execute_query(connection, """
                SELECT Status, COUNT(*) as Count
                FROM InsuranceContracts
                GROUP BY Status
            """)
            if status_data:
                df_status = pd.DataFrame(status_data)
                fig1 = px.pie(df_status, values='Count', names='Status', title='Contract Status Distribution')
                st.plotly_chart(fig1, use_container_width=True)
            
            # Contracts by insurance type
            type_data = execute_query(connection, """
                SELECT t.TypeName, COUNT(*) as Count
                FROM InsuranceContracts c
                JOIN InsuranceTypes t ON c.TypeID = t.TypeID
                GROUP BY t.TypeName
            """)
            if type_data:
                df_type = pd.DataFrame(type_data)
                fig2 = px.bar(df_type, x='TypeName', y='Count', title='Contracts by Insurance Type')
                st.plotly_chart(fig2, use_container_width=True)
            
            # Monthly contract trends
            date_data = execute_query(connection, """
                SELECT DATE_FORMAT(StartDate, '%Y-%m') as Month, COUNT(*) as Count
                FROM InsuranceContracts
                GROUP BY DATE_FORMAT(StartDate, '%Y-%m')
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
                SELECT Status, COUNT(*) as Count
                FROM Assessments
                GROUP BY Status
            """)
            if status_data:
                df_status = pd.DataFrame(status_data)
                fig1 = px.pie(df_status, values='Count', names='Status', title='Claim Status Distribution')
                st.plotly_chart(fig1, use_container_width=True)
            
            # Claims by insurance type
            type_data = execute_query(connection, """
                SELECT t.TypeName, COUNT(*) as Count, AVG(a.ClaimAmount) as AvgAmount
                FROM Assessments a
                JOIN InsuranceContracts c ON a.ContractID = c.ContractID
                JOIN InsuranceTypes t ON c.TypeID = t.TypeID
                GROUP BY t.TypeName
            """)
            if type_data:
                df_type = pd.DataFrame(type_data)
                fig2 = px.bar(df_type, x='TypeName', y=['Count', 'AvgAmount'], 
                             title='Claims Count and Average Amount by Insurance Type',
                             barmode='group')
                st.plotly_chart(fig2, use_container_width=True)
            
            # Monthly claim trends
            date_data = execute_query(connection, """
                SELECT DATE_FORMAT(ClaimDate, '%Y-%m') as Month, COUNT(*) as Count, SUM(ClaimAmount) as TotalAmount
                FROM Assessments
                GROUP BY DATE_FORMAT(ClaimDate, '%Y-%m')
                ORDER BY Month
            """)
            if date_data:
                df_date = pd.DataFrame(date_data)
                fig3 = px.line(df_date, x='Month', y=['Count', 'TotalAmount'], 
                              title='Monthly Claim Trend', markers=True)
                st.plotly_chart(fig3, use_container_width=True)
            
        elif report_type == "Payout Summary":
            st.markdown('<div class="sub-header">Payout Summary Report</div>', unsafe_allow_html=True)
            
            # Payout by status
            status_data = execute_query(connection, """
                SELECT Status, COUNT(*) as Count, SUM(Amount) as TotalAmount
                FROM Payouts
                GROUP BY Status
            """)
            if status_data:
                df_status = pd.DataFrame(status_data)
                col1, col2 = st.columns(2)
                fig1 = px.pie(df_status, values='Count', names='Status', title='Payout Status Distribution')
                col1.plotly_chart(fig1, use_container_width=True)
                
                fig2 = px.pie(df_status, values='TotalAmount', names='Status', title='Payout Amount by Status')
                col2.plotly_chart(fig2, use_container_width=True)
            
            # Payouts by payment method
            method_data = execute_query(connection, """
                SELECT PaymentMethod, COUNT(*) as Count, SUM(Amount) as TotalAmount
                FROM Payouts
                GROUP BY PaymentMethod
            """)
            if method_data:
                df_method = pd.DataFrame(method_data)
                fig3 = px.bar(df_method, x='PaymentMethod', y=['Count', 'TotalAmount'], 
                             title='Payouts by Payment Method',
                             barmode='group')
                st.plotly_chart(fig3, use_container_width=True)
            
            # Monthly payout trends
            date_data = execute_query(connection, """
                SELECT DATE_FORMAT(PayoutDate, '%Y-%m') as Month, SUM(Amount) as TotalAmount
                FROM Payouts
                GROUP BY DATE_FORMAT(PayoutDate, '%Y-%m')
                ORDER BY Month
            """)
            if date_data:
                df_date = pd.DataFrame(date_data)
                fig4 = px.line(df_date, x='Month', y='TotalAmount', 
                              title='Monthly Payout Trend', markers=True)
                st.plotly_chart(fig4, use_container_width=True)
            
        elif report_type == "Customer Activity":
            st.markdown('<div class="sub-header">Customer Activity Report</div>', unsafe_allow_html=True)
            
            # Top customers by number of contracts
            top_customers_contracts = execute_query(connection, """
                SELECT CONCAT(cust.FirstName, ' ', cust.LastName) AS CustomerName, 
                       COUNT(c.ContractID) as ContractCount
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
            
            # Top customers by claim amount
            top_customers_claims = execute_query(connection, """
                SELECT CONCAT(cust.FirstName, ' ', cust.LastName) AS CustomerName, 
                       SUM(a.ClaimAmount) as TotalClaimAmount
                FROM Customers cust
                JOIN InsuranceContracts c ON cust.CustomerID = c.CustomerID
                JOIN Assessments a ON c.ContractID = a.ContractID
                GROUP BY cust.CustomerID
                ORDER BY TotalClaimAmount DESC
                LIMIT 10
            """)
            if top_customers_claims:
                df_top_claims = pd.DataFrame(top_customers_claims)
                fig2 = px.bar(df_top_claims, x='CustomerName', y='TotalClaimAmount', 
                             title='Top Customers by Total Claim Amount')
                st.plotly_chart(fig2, use_container_width=True)
            
        elif report_type == "Revenue Analysis":
            st.markdown('<div class="sub-header">Revenue Analysis Report</div>', unsafe_allow_html=True)
            
            # Premium revenue by insurance type
            premium_by_type = execute_query(connection, """
                SELECT t.TypeName, SUM(c.PremiumAmount) as TotalPremium
                FROM InsuranceContracts c
                JOIN InsuranceTypes t ON c.TypeID = t.TypeID
                GROUP BY t.TypeID
                ORDER BY TotalPremium DESC
            """)
            if premium_by_type:
                df_premium = pd.DataFrame(premium_by_type)
                fig1 = px.bar(df_premium, x='TypeName', y='TotalPremium', 
                             title='Premium Revenue by Insurance Type')
                st.plotly_chart(fig1, use_container_width=True)
            
            # Monthly premium vs payout
            revenue_trends = execute_query(connection, """
                SELECT DATE_FORMAT(c.StartDate, '%Y-%m') as Month, 
                       SUM(c.PremiumAmount) as TotalPremium,
                       IFNULL((SELECT SUM(p.Amount) 
                               FROM Payouts p 
                               JOIN Assessments a ON p.AssessmentID = a.AssessmentID
                               WHERE DATE_FORMAT(p.PayoutDate, '%Y-%m') = DATE_FORMAT(c.StartDate, '%Y-%m')), 0) as TotalPayout
                FROM InsuranceContracts c
                GROUP BY DATE_FORMAT(c.StartDate, '%Y-%m')
                ORDER BY Month
            """)
            if revenue_trends:
                df_revenue = pd.DataFrame(revenue_trends)
                df_revenue['NetRevenue'] = df_revenue['TotalPremium'] - df_revenue['TotalPayout']
                
                fig2 = px.line(df_revenue, x='Month', y=['TotalPremium', 'TotalPayout', 'NetRevenue'], 
                              title='Monthly Premium vs Payout', markers=True)
                st.plotly_chart(fig2, use_container_width=True)
            
            # Profitability by insurance type
            profitability = execute_query(connection, """
                SELECT t.TypeName,
                       SUM(c.PremiumAmount) as TotalPremium,
                       IFNULL((SELECT SUM(p.Amount) 
                               FROM Payouts p 
                               JOIN Assessments a ON p.AssessmentID = a.AssessmentID
                               JOIN InsuranceContracts ic ON a.ContractID = ic.ContractID
                               WHERE ic.TypeID = t.TypeID), 0) as TotalPayout
                FROM InsuranceTypes t
                LEFT JOIN InsuranceContracts c ON t.TypeID = c.TypeID
                GROUP BY t.TypeID
            """)
            if profitability:
                df_profitability = pd.DataFrame(profitability)
                df_profitability['NetRevenue'] = df_profitability['TotalPremium'] - df_profitability['TotalPayout']
                df_profitability['ProfitMargin'] = (df_profitability['NetRevenue'] / df_profitability['TotalPremium']) * 100
                
                fig3 = px.bar(df_profitability, x='TypeName', y='ProfitMargin', 
                             title='Profitability by Insurance Type (%)')
                st.plotly_chart(fig3, use_container_width=True)
        
        connection.close()