import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection, execute_query
from models.contract import get_contracts

def display_claims_management():
    """Display the claims & assessments management section"""
    st.markdown('<div class="sub-header">Claims & Assessments Management</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Claims", "File New Claim"])
    
    # View Claims Tab
    with tab1:
        display_claims()
    
    # File New Claim Tab
    with tab2:
        file_claim_form()

def display_claims():
    """Display a table of all claims"""
    connection = create_connection()
    if connection:
        claims = execute_query(connection, """
            SELECT a.AssessmentID, c.ContractID, cust.CustomerName, 
                   a.AssessmentDate, a.Result
            FROM Assessments a
            JOIN InsuranceContracts c ON a.ContractID = c.ContractID
            JOIN Customers cust ON c.CustomerID = cust.CustomerID
            ORDER BY a.AssessmentDate DESC
        """)
        if claims:
            df_claims = pd.DataFrame(claims)
            st.dataframe(df_claims, use_container_width=True)
        else:
            st.info("No claims found in the database.")
        connection.close()

def file_claim_form():
    """Display the form to file a new claim"""
    connection = create_connection()
    if connection:
        contracts = get_contracts()
        
        if contracts:
            with st.form("file_claim_form"):
                assessment_id = st.text_input("Assessment ID (e.g., A006)")
                
                contract_options = {f"{contract['ContractID']}: {contract['CustomerName']} - {contract['InsuranceName']}" for contract in contracts}
                selected_contract = st.selectbox("Select Contract", options=contract_options)
                
                assessment_date = st.date_input("Assessment Date", value=datetime.date.today())
                
                result_options = ["Pending", "Approved", "Rejected"]
                result = st.selectbox("Assessment Result", options=result_options)
                
                submitted = st.form_submit_button("File Claim")
                if submitted:
                    if assessment_id and selected_contract:
                        contract_id = selected_contract.split(':')[0].strip()
                        
                        save_assessment(assessment_id, contract_id, assessment_date, result)
                    else:
                        st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)
        else:
            st.warning("No contracts found in the database.")
        
        connection.close()

def save_assessment(assessment_id, contract_id, assessment_date, result):
    """Save a new assessment to the database"""
    connection = create_connection()
    if connection:
        insert_query = """
        INSERT INTO Assessments 
        (AssessmentID, ContractID, AssessmentDate, Result) 
        VALUES (%s, %s, %s, %s)
        """
        data = (assessment_id, contract_id, assessment_date, result)
        result_exec = execute_query(connection, insert_query, data)
        if result_exec is not None:
            st.markdown('<div class="success-msg">Claim filed successfully!</div>', unsafe_allow_html=True)
        connection.close()

def get_approved_claims():
    """Get all approved claims without payouts from the database"""
    connection = create_connection()
    if connection:
        claims = execute_query(connection, """
            SELECT a.ContractID, cust.CustomerName, a.AssessmentDate
            FROM Assessments a
            JOIN InsuranceContracts c ON a.ContractID = c.ContractID
            JOIN Customers cust ON c.CustomerID = cust.CustomerID
            WHERE a.Result = 'Approved' AND a.ContractID NOT IN (SELECT ContractID FROM Payouts)
        """)
        connection.close()
        return claims
    return []
