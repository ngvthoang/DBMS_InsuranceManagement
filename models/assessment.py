import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection, execute_query, get_cached_data, execute_write_query
from mysql.connector import Error

def display_claims_management():
    """Display the claims & assessments management section"""
    st.markdown('<div class="sub-header">Claims & Assessments Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["View Claims", "File New Claim", "Pending Claims"])
    
    # View Claims Tab
    with tab1:
        display_claims()
    
    # File New Claim Tab
    with tab2:
        file_claim_form()
        
    # Pending Claims Tab
    with tab3:
        pending_claims()

def display_claims():
    """Display a table of all claims"""
    claims = get_all_assessments()
    if claims:
        df_claims = pd.DataFrame(claims)
        st.dataframe(df_claims, use_container_width=True)
    else:
        st.info("No claims found in the database.")

def file_claim_form():
    """Display the form to file a new claim"""
    contracts = get_active_contracts_dropdown()
    
    if contracts:
        with st.form("file_claim_form"):
            # Auto-generate next ID
            next_id = generate_next_assessment_id()
            
            assessment_id = st.text_input("Assessment ID (e.g., A006)", value=next_id)
            
            selected_contract = st.selectbox("Select Contract", options=list(contracts.keys()))
            
            assessment_date = st.date_input("Assessment Date", value=datetime.date.today())
            
            amount = st.number_input("Claim Amount ($)", min_value=0.0, value=0.0, step=100.0)
            
            result_options = ["Pending", "Approved", "Rejected"]
            result = st.selectbox("Assessment Result", options=result_options)
            
            submitted = st.form_submit_button("File Claim")
            if submitted:
                if assessment_id and selected_contract and amount > 0:
                    contract_id = contracts[selected_contract]
                    
                    add_assessment(assessment_id, contract_id, assessment_date, amount, result)
                    st.markdown('<div class="success-msg">Claim filed successfully!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-msg">Please fill in all the required fields and ensure the amount is greater than 0.</div>', unsafe_allow_html=True)
    else:
        st.warning("No contracts found in the database.")

def pending_claims():
    """Display and process pending claims"""
    pending_claims = get_pending_assessments()
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
                    update_assessment_result(row['AssessmentID'], row['Action'])
            st.success("Pending claims updated successfully!")
            st.experimental_rerun()  # Force a page refresh

        # Display the table
        st.dataframe(df_pending_claims[['AssessmentID', 'ContractID', 'CustomerName', 'AssessmentDate', 'ClaimAmount', 'Action']], use_container_width=True)
    else:
        st.info("No pending claims found.")

@st.cache_data(ttl=300)
def get_all_assessments():
    """Get all assessments with contract and customer information"""
    query = """
        SELECT a.AssessmentID, a.ContractID, c.CustomerID, c.CustomerName, 
               a.AssessmentDate, a.ClaimAmount, a.Result
        FROM Assessments a
        JOIN InsuranceContracts ic ON a.ContractID = ic.ContractID
        JOIN Customers c ON ic.CustomerID = c.CustomerID
        ORDER BY a.AssessmentDate DESC
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_assessment_by_id(assessment_id):
    """Get a specific assessment by ID"""
    query = """
        SELECT a.AssessmentID, a.ContractID, c.CustomerID, c.CustomerName, 
               a.AssessmentDate, a.ClaimAmount, a.Result
        FROM Assessments a
        JOIN InsuranceContracts ic ON a.ContractID = ic.ContractID
        JOIN Customers c ON ic.CustomerID = c.CustomerID
        WHERE a.AssessmentID = %s
    """
    result = get_cached_data(query, (assessment_id,))
    if result and len(result) > 0:
        return result[0]
    return None

@st.cache_data(ttl=300)
def get_assessments_dropdown():
    """Get assessments for dropdown selection"""
    query = """
        SELECT a.AssessmentID, c.CustomerName, a.ClaimAmount
        FROM Assessments a
        JOIN InsuranceContracts ic ON a.ContractID = ic.ContractID
        JOIN Customers c ON ic.CustomerID = c.CustomerID
    """
    assessments = get_cached_data(query)
    if not assessments:
        return {}
    return {f"{a['AssessmentID']}: {a['CustomerName']} - ${float(a['ClaimAmount']):,.2f}": a['AssessmentID'] for a in assessments}

@st.cache_data(ttl=300)
def get_pending_assessments():
    """Get assessments with pending status"""
    query = """
        SELECT a.AssessmentID, a.ContractID, c.CustomerName,
               a.AssessmentDate, a.ClaimAmount, a.Result
        FROM Assessments a
        JOIN InsuranceContracts ic ON a.ContractID = ic.ContractID
        JOIN Customers c ON ic.CustomerID = c.CustomerID
        WHERE a.Result = 'Pending'
        ORDER BY a.AssessmentDate
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_approved_claims():
    """Get assessments with approved status"""
    query = """
        SELECT a.AssessmentID, a.ContractID, c.CustomerName,
               a.AssessmentDate, a.ClaimAmount, a.Result
        FROM Assessments a
        JOIN InsuranceContracts ic ON a.ContractID = ic.ContractID
        JOIN Customers c ON ic.CustomerID = c.CustomerID
        WHERE a.Result = 'Approved'
        ORDER BY a.AssessmentDate DESC
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_active_contracts_dropdown():
    """Get active contracts for dropdown selection"""
    query = """
        SELECT c.ContractID, cust.CustomerName, t.InsuranceName
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        WHERE c.Status = 'Active'
    """
    contracts = get_cached_data(query)
    if not contracts:
        return {}
    return {f"{c['ContractID']}: {c['CustomerName']} - {c['InsuranceName']}": c['ContractID'] for c in contracts}

@st.cache_data(ttl=300)
def get_related_payout(contract_id, claim_amount):
    """Get payout related to an assessment"""
    query = """
        SELECT PayoutID, ContractID, PayoutDate, Amount, Status
        FROM Payouts
        WHERE ContractID = %s AND Amount = %s
    """
    return get_cached_data(query, (contract_id, claim_amount))

@st.cache_data(ttl=300)
def get_related_assessment(contract_id, claim_amount):
    """Get assessment related to a payout"""
    query = """
        SELECT AssessmentID, ContractID, AssessmentDate, ClaimAmount, Result
        FROM Assessments
        WHERE ContractID = %s AND ClaimAmount = %s AND Result = 'Approved'
    """
    return get_cached_data(query, (contract_id, claim_amount))

def generate_next_assessment_id():
    """Generate the next assessment ID"""
    last_assessment = get_cached_data("SELECT AssessmentID FROM Assessments ORDER BY AssessmentID DESC LIMIT 1")
    next_id = "A001"  # Default starting ID if no records exist
    
    if last_assessment and len(last_assessment) > 0:
        last_id = last_assessment[0]['AssessmentID']
        # Extract the numeric part, increment it, and format it back
        try:
            id_num = int(last_id[1:])
            next_id = f"A{(id_num + 1):03d}"
        except (ValueError, IndexError):
            pass  # Use default if parsing fails
    
    return next_id

def add_assessment(assessment_id, contract_id, assessment_date, claim_amount, result):
    """Add a new assessment to the database"""
    query = """
    INSERT INTO Assessments (AssessmentID, ContractID, AssessmentDate, ClaimAmount, Result) 
    VALUES (%s, %s, %s, %s, %s)
    """
    data = (assessment_id, contract_id, assessment_date, claim_amount, result)
    result = execute_write_query(query, data)
    
    # Clear cache for assessment-related functions
    if hasattr(get_all_assessments, 'clear'):
        get_all_assessments.clear()
    if hasattr(get_assessments_dropdown, 'clear'):
        get_assessments_dropdown.clear()
    if hasattr(get_pending_assessments, 'clear'):
        get_pending_assessments.clear()
    if hasattr(get_approved_claims, 'clear'):
        get_approved_claims.clear()
    
    return result

def update_assessment_result(assessment_id, new_result):
    """Update an assessment's result"""
    query = """
    UPDATE Assessments 
    SET Result = %s
    WHERE AssessmentID = %s
    """
    data = (new_result, assessment_id)
    result = execute_write_query(query, data)
    
    # Clear cache for assessment-related functions
    if hasattr(get_all_assessments, 'clear'):
        get_all_assessments.clear()
    if hasattr(get_assessment_by_id, 'clear'):
        get_assessment_by_id.clear()
    if hasattr(get_assessments_dropdown, 'clear'):
        get_assessments_dropdown.clear()
    if hasattr(get_pending_assessments, 'clear'):
        get_pending_assessments.clear()
    if hasattr(get_approved_claims, 'clear'):
        get_approved_claims.clear()
    
    return result
