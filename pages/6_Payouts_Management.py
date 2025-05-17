import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection
from models.payout import (
    get_all_payouts,
    get_payout_by_id,
    get_payouts_dropdown,
    get_pending_payouts,
    get_total_approved_payouts,
    get_payout_counts_by_status,
    generate_next_payout_id,
    add_payout,
    update_payout_status
)
from models.assessment import get_approved_claims, get_related_assessment

# Check the curent user role if they are allowed to access this page
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("Access denied. Please log in to view this page.")
    st.stop()
if "role" not in st.session_state or st.session_state["role"] not in ["Admin", "Claim Accessor"]:
    st.error("Access denied. You do not have permission to view this page.")
    st.stop()

st.set_page_config(page_title="Payouts Management", page_icon="💰", layout="wide")

# Initialize session state for success messages
if 'payout_processed' not in st.session_state:
    st.session_state.payout_processed = False
if 'payout_updated' not in st.session_state:
    st.session_state.payout_updated = False
if 'show_success' not in st.session_state:
    st.session_state.show_success = False

# Payouts Management page
st.markdown('# Payouts Management')
st.markdown('Manage insurance claim payouts')
st.markdown('---')

# Check database connection
conn = create_connection()
if not conn:
    st.error("Could not connect to the database. Please check your connection settings.")
    st.stop()
else:
    conn.close()

# Create tabs
tab1, tab2, tab3 = st.tabs(["View Payouts", "Process New Payout", "Pending Payouts"])

# View Payouts Tab
with tab1:
    st.subheader("All Payouts")
    
    # Refresh button
    if st.button("🔄 Refresh", key="refresh_payouts"):
        st.cache_data.clear()
        st.rerun()
    
    # Get and display payouts
    payouts = get_all_payouts()
    if payouts:
        df = pd.DataFrame(payouts)
        df['PayoutDate'] = pd.to_datetime(df['PayoutDate']).dt.strftime('%Y-%m-%d')
        df['Amount'] = df['Amount'].apply(lambda x: f"${float(x):,.2f}" if x else "$0.00")
        
        st.dataframe(df, use_container_width=True)
        
        # Payout details section
        st.subheader("Payout Details")
        
        # Get payout dropdown options
        payout_options = get_payouts_dropdown()
        selected_payout = st.selectbox(
            "Select a payout to view details:",
            options=list(payout_options.keys())
        )
        
        if selected_payout:
            payout_id = payout_options[selected_payout]
            payout = get_payout_by_id(payout_id)
            
            if payout:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Payout ID:** {payout['PayoutID']}")
                    st.markdown(f"**Contract ID:** {payout['ContractID']}")
                    st.markdown(f"**Customer:** {payout['CustomerName']} ({payout['CustomerID']})")
                
                with col2:
                    st.markdown(f"**Payout Date:** {payout['PayoutDate']}")
                    st.markdown(f"**Amount:** ${float(payout['Amount']):,.2f}")
                    st.markdown(f"**Status:** {payout['Status']}")
                
                # Display related assessment
                st.subheader("Related Assessment")
                
                assessment = get_related_assessment(payout['ContractID'], payout['Amount'])
                if assessment:
                    df_assessment = pd.DataFrame(assessment)
                    df_assessment['AssessmentDate'] = pd.to_datetime(df_assessment['AssessmentDate']).dt.strftime('%Y-%m-%d')
                    df_assessment['ClaimAmount'] = df_assessment['ClaimAmount'].apply(lambda x: f"${float(x):,.2f}")
                    st.dataframe(df_assessment, use_container_width=True)
                else:
                    st.info("No related assessment found for this payout.")
                
                # Option to update the payout status
                st.subheader("Update Payout Status")
                
                with st.form(key=f"update_payout_{payout_id}"):
                    new_status = st.selectbox(
                        "Change status to:",
                        options=["Pending", "Approved", "Rejected", "Completed"],
                        index=["Pending", "Approved", "Rejected", "Completed"].index(payout['Status']) if payout['Status'] in ["Pending", "Approved", "Rejected", "Completed"] else 0
                    )
                    
                    update_submitted = st.form_submit_button("Update Status")
                    if update_submitted:
                        if new_status != payout['Status']:
                            if update_payout_status(payout_id, new_status):
                                st.success(f"Payout status updated to {new_status}!")
                                st.rerun()
                            else:
                                st.error("Failed to update payout status.")
    else:
        st.info("No payouts found in the database.")

# Process New Payout Tab
with tab2:
    st.subheader("Process New Payout")
    
    # Get approved claims without payouts
    approved_claims = get_approved_claims()
    
    if approved_claims:
        st.write("The following approved claims are eligible for payout:")
        
        # Create a DataFrame to show the approved claims
        df = pd.DataFrame(approved_claims)
        df['AssessmentDate'] = pd.to_datetime(df['AssessmentDate']).dt.strftime('%Y-%m-%d')
        df['ClaimAmount'] = df['ClaimAmount'].apply(lambda x: f"${float(x):,.2f}")
        st.dataframe(df, use_container_width=True)
        
        with st.form("process_payout_form"):
            # Auto-generate payout ID
            payout_id = st.text_input("Payout ID", value=generate_next_payout_id())
            
            # Create options for approved claims
            claim_options = {
                f"{a['AssessmentID']}: {a['CustomerName']} - {a['ClaimAmount']}": (a['ContractID'], a['ClaimAmount']) 
                for a in approved_claims
            }
            
            if claim_options:
                selected_claim = st.selectbox("Select Approved Claim", options=list(claim_options.keys()))
                
                payout_date = st.date_input("Payout Date", value=datetime.date.today())
                
                if selected_claim:
                    contract_id, claim_amount = claim_options[selected_claim]
                    
                    # Convert claim_amount to float directly without string manipulation
                    # since it's already a Decimal object
                    amount = float(claim_amount)
                    
                    # Display the amount from the assessment
                    st.markdown(f"**Amount from assessment: ${amount:,.2f}**")
                    
                    # Allow a custom amount (with the assessment amount as default)
                    custom_amount = st.number_input("Custom Amount (if different)", min_value=0.0, value=amount, step=100.0, format="%.2f")
                    
                    status = st.selectbox("Initial Status", options=["Pending", "Approved", "Completed"], index=1)
                    
                    submitted = st.form_submit_button("Process Payout")
                    if submitted:
                        # Validate inputs
                        if payout_id and contract_id and custom_amount > 0:
                            # Process the payout
                            if add_payout(payout_id, contract_id, custom_amount, payout_date, status):
                                # Set success flag
                                st.session_state.payout_processed = True
                                
                                # Rerun to show the success message
                                st.rerun()
                            else:
                                st.error("Failed to process payout.")
                        else:
                            st.error("Please fill in all required fields and ensure amount is greater than zero.")
            else:
                st.warning("Please select an approved claim to process.")
    else:
        st.info("No approved claims without payouts found.")
    
    # Show success message if payout was just processed
    if st.session_state.payout_processed:
        st.success("Payout processed successfully!")
        st.session_state.payout_processed = False
        st.session_state.show_success = True

# Pending Payouts Tab
with tab3:
    st.subheader("Pending Payouts")
    
    # Get pending payouts
    pending_payouts = get_pending_payouts()
    
    if pending_payouts:
        st.write("The following payouts are pending approval:")
        
        # Create a DataFrame to display the pending payouts
        df = pd.DataFrame(pending_payouts)
        df['PayoutDate'] = pd.to_datetime(df['PayoutDate']).dt.strftime('%Y-%m-%d')
        df['Amount'] = df['Amount'].apply(lambda x: f"${float(x):,.2f}")
        
        # Process each pending payout
        for index, row in df.iterrows():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Payout ID:** {row['PayoutID']} | **Contract:** {row['ContractID']} | **Customer:** {row['CustomerName']} | **Amount:** {row['Amount']} | **Date:** {row['PayoutDate']}")
            
            with col2:
                action = st.selectbox(
                    "Action",
                    options=["Select Action", "Approve", "Reject"],
                    key=f"action_{row['PayoutID']}"
                )
                
                if action in ["Approve", "Reject"]:
                    status = "Approved" if action == "Approve" else "Rejected"
                    
                    # Update the payout status
                    if update_payout_status(row['PayoutID'], status):
                        st.success(f"Payout {row['PayoutID']} {status.lower()}!")
                        st.rerun()
                    else:
                        st.error(f"Failed to update payout {row['PayoutID']}.")
        
        # Add a button to refresh the pending payouts
        if st.button("Refresh Pending Payouts"):
            st.rerun()
    else:
        st.info("No pending payouts found.")

    # Show payout statistics
    st.subheader("Payout Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_payouts = get_total_approved_payouts()
        st.metric("Total Approved Payouts", f"${total_payouts:,.2f}")
    
    with col2:
        payout_counts = get_payout_counts_by_status()
        if payout_counts:
            counts_df = pd.DataFrame(payout_counts)
            statuses = {row['Status']: row['count'] for _, row in counts_df.iterrows()}
            
            st.metric("Pending Payouts", statuses.get('Pending', 0))
            st.metric("Approved Payouts", statuses.get('Approved', 0) + statuses.get('Completed', 0))
            st.metric("Rejected Payouts", statuses.get('Rejected', 0))
        else:
            st.metric("Pending Payouts", 0)
            st.metric("Approved Payouts", 0)
            st.metric("Rejected Payouts", 0)
