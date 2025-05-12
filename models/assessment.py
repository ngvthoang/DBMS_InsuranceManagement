import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection, execute_query
from models.contract import get_contracts
from mysql.connector import Error
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

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

def file_claim_form():
    """Display the form to file a new claim"""
    connection = create_connection()
    if connection:
        contracts = get_contracts()
        
        if contracts:
            with st.form("file_claim_form"):
                # Auto-generate next ID
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
                        
                        save_assessment(assessment_id, contract_id, assessment_date, amount, result)
                    else:
                        st.markdown('<div class="error-msg">Please fill in all the required fields and ensure the amount is greater than 0.</div>', unsafe_allow_html=True)
        else:
            st.warning("No contracts found in the database.")
        
        connection.close()

def pending_claims():
    """Display and process pending claims"""
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
                st.experimental_rerun()  # Force a page refresh

            # Display the table
            st.dataframe(df_pending_claims[['AssessmentID', 'ContractID', 'CustomerName', 'AssessmentDate', 'ClaimAmount', 'Action']])
        else:
            st.info("No pending claims found.")
        connection.close()

def save_assessment(assessment_id, contract_id, assessment_date, amount, result):
    """Save a new assessment to the database"""
    connection = create_connection()
    if connection:
        insert_query = """
        INSERT INTO Assessments 
        (AssessmentID, ContractID, AssessmentDate, ClaimAmount, Result) 
        VALUES (%s, %s, %s, %s, %s)
        """
        data = (assessment_id, contract_id, assessment_date, amount, result)
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
