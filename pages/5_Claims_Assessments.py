import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection
from models.assessment import (
    get_all_assessments,
    get_assessment_by_id,
    get_assessments_dropdown,
    get_active_contracts_dropdown,
    get_pending_assessments,
    get_related_payout,
    generate_next_assessment_id,
    add_assessment,
    update_assessment_result
)

st.set_page_config(page_title="Claims & Assessments", page_icon="🔍", layout="wide")

# Claims & Assessments page
st.markdown('# Claims & Assessments')
st.markdown('Manage insurance claims and assessments')
st.markdown('---')

# Check database connection
conn = create_connection()
if not conn:
    st.error("Could not connect to the database. Please check your connection settings.")
    st.stop()
else:
    conn.close()

# Initialize session state for success messages
if 'claim_filed' not in st.session_state:
    st.session_state.claim_filed = False
if 'claim_updated' not in st.session_state:
    st.session_state.claim_updated = False
if 'show_success' not in st.session_state:
    st.session_state.show_success = False

# Create tabs
tab1, tab2, tab3 = st.tabs(["View Claims", "File New Claim", "Pending Claims"])

# View Claims Tab
with tab1:
    # Show success messages if redirected from other tabs
    if st.session_state.show_success:
        if st.session_state.claim_filed:
            st.success("Claim filed successfully!")
            st.session_state.claim_filed = False
        elif st.session_state.claim_updated:
            st.success("Claim status updated successfully!")
            st.session_state.claim_updated = False
        
        # Reset the success flag after showing
        st.session_state.show_success = False
    
    st.subheader("All Claims")
    
    # Refresh button
    if st.button("🔄 Refresh", key="refresh_claims"):
        st.cache_data.clear()
        st.rerun()
    
    # Get and display claims
    assessments = get_all_assessments()
    if assessments:
        df = pd.DataFrame(assessments)
        df['AssessmentDate'] = pd.to_datetime(df['AssessmentDate']).dt.strftime('%Y-%m-%d')
        df['ClaimAmount'] = df['ClaimAmount'].apply(lambda x: f"${float(x):,.2f}" if x else "$0.00")
        
        st.dataframe(df, use_container_width=True)
        
        # Assessment details section
        st.subheader("Assessment Details")
        
        # Get assessment dropdown options
        assessment_options = get_assessments_dropdown()
        selected_assessment = st.selectbox(
            "Select an assessment to view details:",
            options=list(assessment_options.keys())
        )
        
        if selected_assessment:
            assessment_id = assessment_options[selected_assessment]
            assessment = get_assessment_by_id(assessment_id)
            
            if assessment:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Assessment ID:** {assessment['AssessmentID']}")
                    st.markdown(f"**Contract ID:** {assessment['ContractID']}")
                    st.markdown(f"**Customer:** {assessment['CustomerName']} ({assessment['CustomerID']})")
                
                with col2:
                    st.markdown(f"**Assessment Date:** {assessment['AssessmentDate']}")
                    st.markdown(f"**Claim Amount:** ${float(assessment['ClaimAmount']):,.2f}")
                    st.markdown(f"**Result:** {assessment['Result']}")
                
                # Display related payout if any
                st.subheader("Related Payout")
                
                payout = get_related_payout(assessment['ContractID'], assessment['ClaimAmount'])
                if payout:
                    df_payout = pd.DataFrame(payout)
                    df_payout['PayoutDate'] = pd.to_datetime(df_payout['PayoutDate']).dt.strftime('%Y-%m-%d')
                    df_payout['Amount'] = df_payout['Amount'].apply(lambda x: f"${float(x):,.2f}")
                    st.dataframe(df_payout, use_container_width=True)
                else:
                    st.info("No related payout found for this assessment.")
                
                # Option to update the assessment result
                st.subheader("Update Assessment Result")
                
                with st.form(key=f"update_assessment_{assessment_id}"):
                    new_result = st.selectbox(
                        "Change result to:",
                        options=["Pending", "Approved", "Rejected"],
                        index=["Pending", "Approved", "Rejected"].index(assessment['Result']) if assessment['Result'] in ["Pending", "Approved", "Rejected"] else 0
                    )
                    
                    update_submitted = st.form_submit_button("Update Result")
                    if update_submitted:
                        if new_result != assessment['Result']:
                            if update_assessment_result(assessment_id, new_result):
                                # Set success flag and redirect to view tab
                                st.session_state.claim_updated = True
                                st.rerun()
                            else:
                                st.error("Failed to update assessment result.")
    else:
        st.info("No claims/assessments found in the database.")

# File New Claim Tab
with tab2:
    st.subheader("File New Claim")
    
    with st.form("file_claim_form"):
        # Auto-generate assessment ID
        assessment_id = st.text_input("Assessment ID", value=generate_next_assessment_id())
        
        # Get contract options
        contract_options = get_active_contracts_dropdown()
        if not contract_options:
            st.warning("No active contracts found. Please create contracts first.")
            contract_id = None
        else:
            selected_contract = st.selectbox("Select Contract", options=list(contract_options.keys()))
            contract_id = contract_options[selected_contract] if selected_contract else None
        
        assessment_date = st.date_input("Assessment Date", value=datetime.date.today())
        
        claim_amount = st.number_input("Claim Amount ($)", min_value=0.0, step=100.0, format="%.2f")
        
        result = st.selectbox("Initial Assessment Result", options=["Pending", "Approved", "Rejected"], index=0)
        
        notes = st.text_area("Assessment Notes", placeholder="Enter any notes about this claim...")
        
        submitted = st.form_submit_button("File Claim")
        if submitted:
            if assessment_id and contract_id and claim_amount > 0:
                if add_assessment(assessment_id, contract_id, assessment_date, claim_amount, result):
                    # Set success flag
                    st.session_state.claim_filed = True
                    
                    # Rerun to show the success message
                    st.rerun()
                else:
                    st.error("Failed to file claim.")
            else:
                if not contract_id:
                    st.error("No contract selected. Please create a contract first.")
                else:
                    st.error("Please fill in all required fields and ensure claim amount is greater than zero.")
    
    # Show success message if claim was just filed
    if st.session_state.claim_filed:
        st.success("Claim filed successfully!")
        st.session_state.claim_filed = False
        st.session_state.show_success = True

# Pending Claims Tab
with tab3:
    st.subheader("Pending Claims")
    
    # Show success message if a claim was just updated
    if st.session_state.claim_updated and not st.session_state.show_success:
        st.success("Claim status updated successfully!")
        st.session_state.claim_updated = False
    
    # Add refresh button
    if st.button("🔄 Refresh Pending Claims", key="refresh_pending"):
        st.cache_data.clear()
        st.rerun()
    
    # Get pending claims
    pending_assessments = get_pending_assessments()
    
    if pending_assessments:
        st.write("The following claims are pending assessment:")
        
        # Create a DataFrame to display the pending claims
        df = pd.DataFrame(pending_assessments)
        df['AssessmentDate'] = pd.to_datetime(df['AssessmentDate']).dt.strftime('%Y-%m-%d')
        df['ClaimAmount'] = df['ClaimAmount'].apply(lambda x: f"${float(x):,.2f}")
        
        # Display the table of pending claims
        st.dataframe(df, use_container_width=True)
        
        # Create a form for bulk actions
        with st.form("process_pending_claims"):
            st.subheader("Process Selected Claims")
            
            # Create a multiselect for choosing claims
            assessment_options = {f"{a['AssessmentID']}: {a['CustomerName']} - ${float(a['ClaimAmount']):,.2f}": a['AssessmentID'] for a in pending_assessments}
            selected_assessments = st.multiselect(
                "Select claims to process:",
                options=list(assessment_options.keys())
            )
            
            # Action selection
            action = st.selectbox(
                "Action to take:",
                options=["Approve", "Reject"]
            )
            
            # Submit button
            submitted = st.form_submit_button("Process Claims")
            if submitted:
                if selected_assessments:
                    success_count = 0
                    for selection in selected_assessments:
                        assessment_id = assessment_options[selection]
                        if update_assessment_result(assessment_id, "Approved" if action == "Approve" else "Rejected"):
                            success_count += 1
                    
                    if success_count > 0:
                        # Set success flag and redirect to view tab
                        st.session_state.claim_updated = True
                        st.session_state.show_success = True
                        st.rerun()
                    else:
                        st.error("Failed to update claims.")
                else:
                    st.warning("Please select at least one claim to process.")
    else:
        st.info("No pending claims found.")
