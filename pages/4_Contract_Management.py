import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection
from models.contract import (
    get_all_contracts,
    get_contract_by_id,
    get_contracts_dropdown,
    get_expiring_contracts,
    generate_next_contract_id,
    add_contract,
    update_contract,
    extend_contract,
    get_contract_assessments,
    get_contract_payouts
)
from models.customer import get_customers_dropdown
from models.insurance_type import get_insurance_types_dropdown

st.set_page_config(page_title="Contract Management", page_icon="📝", layout="wide")

# Contract Management page
st.markdown('# Contract Management')
st.markdown('Create and manage insurance contracts')
st.markdown('---')

# Check database connection
conn = create_connection()
if not conn:
    st.error("Could not connect to the database. Please check your connection settings.")
    st.stop()
else:
    conn.close()

# Initialize session state for success messages
if 'contract_created' not in st.session_state:
    st.session_state.contract_created = False
if 'contract_updated' not in st.session_state:
    st.session_state.contract_updated = False
if 'contract_extended' not in st.session_state:
    st.session_state.contract_extended = False
if 'show_success' not in st.session_state:
    st.session_state.show_success = False

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["View Contracts", "Create Contract", "Update Contract", "Contract Extension"])

# View Contracts Tab
with tab1:
    # Show success messages if redirected from other tabs
    if st.session_state.show_success:
        if st.session_state.contract_created:
            st.success("Contract created successfully!")
            st.session_state.contract_created = False
        elif st.session_state.contract_updated:
            st.success("Contract updated successfully!")
            st.session_state.contract_updated = False
        elif st.session_state.contract_extended:
            st.success("Contract(s) extended successfully!")
            st.session_state.contract_extended = False
        
        # Reset the success flag after showing
        st.session_state.show_success = False
    
    st.subheader("All Contracts")
        
    # Refresh button
    if st.button("🔄 Refresh", key="refresh_contracts"):
        st.cache_data.clear()
        st.rerun()
    
    # Get and display contracts
    contracts = get_all_contracts()
    if contracts:
        df = pd.DataFrame(contracts)
        if 'SignDate' in df.columns:
            df['SignDate'] = pd.to_datetime(df['SignDate']).dt.strftime('%Y-%m-%d')
        if 'ExpirationDate' in df.columns:
            df['ExpirationDate'] = pd.to_datetime(df['ExpirationDate']).dt.strftime('%Y-%m-%d')
        
        st.dataframe(df, use_container_width=True)
        
        # Contract details section
        st.subheader("Contract Details")
        
        # Get contract dropdown options
        contract_options = get_contracts_dropdown()
        selected_contract = st.selectbox(
            "Select a contract to view details:",
            options=list(contract_options.keys())
        )
        
        if selected_contract:
            contract_id = contract_options[selected_contract]
            contract = get_contract_by_id(contract_id)
            
            if contract:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Contract ID:** {contract['ContractID']}")
                    st.markdown(f"**Customer:** {contract['CustomerName']} ({contract['CustomerID']})")
                    st.markdown(f"**Insurance Type:** {contract['InsuranceName']} ({contract['InsuranceTypeID']})")
                
                with col2:
                    st.markdown(f"**Sign Date:** {contract['SignDate']}")
                    st.markdown(f"**Expiration Date:** {contract['ExpirationDate']}")
                    st.markdown(f"**Status:** {contract['Status']}")
                
                # Display Assessments for this contract
                st.subheader("Assessments")
                assessments = get_contract_assessments(contract_id)
                if assessments:
                    df_assessments = pd.DataFrame(assessments)
                    df_assessments['AssessmentDate'] = pd.to_datetime(df_assessments['AssessmentDate']).dt.strftime('%Y-%m-%d')
                    if 'ClaimAmount' in df_assessments.columns:
                        df_assessments['ClaimAmount'] = df_assessments['ClaimAmount'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
                    st.dataframe(df_assessments, use_container_width=True)
                else:
                    st.info("No assessments found for this contract.")
                
                # Display Payouts for this contract
                st.subheader("Payouts")
                payouts = get_contract_payouts(contract_id)
                if payouts:
                    df_payouts = pd.DataFrame(payouts)
                    df_payouts['PayoutDate'] = pd.to_datetime(df_payouts['PayoutDate']).dt.strftime('%Y-%m-%d')
                    if 'Amount' in df_payouts.columns:
                        df_payouts['Amount'] = df_payouts['Amount'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
                    st.dataframe(df_payouts, use_container_width=True)
                else:
                    st.info("No payouts found for this contract.")
    else:
        st.info("No contracts found in the database.")

# Create Contract Tab
with tab2:
    st.subheader("Create New Contract")
    
    with st.form("create_contract_form"):
        # Auto-generate contract ID
        next_id = generate_next_contract_id()
        
        contract_id = st.text_input("Contract ID", value=next_id)
        
        # Get customer options
        customer_options = get_customers_dropdown()
        if not customer_options:
            st.warning("No customers found. Please add customers first.")
            selected_customer = None
        else:
            selected_customer = st.selectbox("Select Customer", options=list(customer_options.keys()))
        
        # Get insurance type options
        insurance_options = get_insurance_types_dropdown()
        if not insurance_options:
            st.warning("No insurance types found. Please add insurance types first.")
            selected_insurance = None
        else:
            selected_insurance = st.selectbox("Select Insurance Type", options=list(insurance_options.keys()))
        
        sign_date = st.date_input("Sign Date", value=datetime.date.today())
        
        submitted = st.form_submit_button("Create Contract")
        if submitted:
            if contract_id and selected_customer and selected_insurance and sign_date:
                customer_id = customer_options[selected_customer]
                insurance_id = insurance_options[selected_insurance]
                
                if add_contract(contract_id, customer_id, insurance_id, sign_date):
                    # Set success flag
                    st.session_state.contract_created = True
                    
                    # Rerun to show the success message
                    st.rerun()
                else:
                    st.error("Failed to create contract. Please try again.")
            else:
                st.error("Please fill in all required fields.")
    
    # Show success message if contract was just created
    if st.session_state.contract_created:
        st.success("Contract created successfully!")
        st.session_state.contract_created = False
        st.session_state.show_success = True

# Update Contract Tab
with tab3:
    st.subheader("Update Contract")
    
    # Get contract dropdown options
    contract_options = get_contracts_dropdown()
    if not contract_options:
        st.info("No contracts found in the database.")
    else:
        selected_contract = st.selectbox(
            "Select contract to update:",
            options=list(contract_options.keys()),
            key="update_contract_select"
        )
        
        if selected_contract:
            contract_id = contract_options[selected_contract]
            contract = get_contract_by_id(contract_id)
            
            if contract:
                with st.form("update_contract_form"):
                    # Get customer options
                    customer_options = get_customers_dropdown()
                    customer_list = list(customer_options.keys())
                    default_customer = next((item for item in customer_list if contract['CustomerID'] in item), None)
                    
                    # Get insurance type options
                    insurance_options = get_insurance_types_dropdown()
                    insurance_list = list(insurance_options.keys())
                    default_insurance = next((item for item in insurance_list if contract['InsuranceTypeID'] in item), None)
                    
                    selected_customer = st.selectbox(
                        "Customer", 
                        options=customer_list,
                        index=customer_list.index(default_customer) if default_customer else 0
                    )
                    
                    selected_insurance = st.selectbox(
                        "Insurance Type", 
                        options=insurance_list,
                        index=insurance_list.index(default_insurance) if default_insurance else 0
                    )
                    
                    sign_date = st.date_input("Sign Date", value=contract['SignDate'])
                    expiration_date = st.date_input("Expiration Date", value=contract['ExpirationDate'])
                    
                    submitted = st.form_submit_button("Update Contract")
                    if submitted:
                        if selected_customer and selected_insurance:
                            customer_id = customer_options[selected_customer]
                            insurance_id = insurance_options[selected_insurance]
                            
                            if update_contract(contract_id, customer_id, insurance_id, sign_date, expiration_date):
                                # Set success flag
                                st.session_state.contract_updated = True
                                st.rerun()
                            else:
                                st.error("Failed to update contract. Please try again.")
                        else:
                            st.error("Please fill in all required fields.")
    
    # Show success message if contract was just updated
    if st.session_state.contract_updated:
        st.success("Contract updated successfully!")
        st.session_state.contract_updated = False
        st.session_state.show_success = True

# Contract Extension Tab
with tab4:
    st.subheader("Contract Extension")
    
    # Show success message if contracts were just extended
    if st.session_state.contract_extended and not st.session_state.show_success:
        st.success("Contract(s) extended successfully!")
        st.session_state.contract_extended = False
    
    # Get contracts nearing expiration
    expiring_contracts = get_expiring_contracts()
    
    if expiring_contracts:
        st.write("The following contracts are expiring in the next 3 months or have already expired:")
        
        df = pd.DataFrame(expiring_contracts)
        df['SignDate'] = pd.to_datetime(df['SignDate']).dt.strftime('%Y-%m-%d')
        df['ExpirationDate'] = pd.to_datetime(df['ExpirationDate']).dt.strftime('%Y-%m-%d')
        st.dataframe(df, use_container_width=True)
        
        with st.form("extend_contracts_form"):
            # Change from set to dictionary for contract options
            contract_options = {f"{c['ContractID']}: {c['CustomerName']} - Expires: {c['ExpirationDate']}": c['ContractID'] for c in expiring_contracts}
            selected_contracts = st.multiselect(
                "Select contracts to extend:",
                options=list(contract_options.keys())
            )
            
            extension_period = st.selectbox("Extension Period:", ["6 Months", "1 Year", "2 Years"], index=1)
            
            submitted = st.form_submit_button("Extend Selected Contracts")
            if submitted:
                if selected_contracts:
                    # Map extension period to days
                    period_map = {
                        "6 Months": 182,
                        "1 Year": 365,
                        "2 Years": 730
                    }
                    days = period_map[extension_period]
                    
                    # Process each selected contract
                    success_count = 0
                    for selection in selected_contracts:
                        # Get contract ID from the dictionary using the selection as key
                        contract_id = contract_options[selection]
                        
                        # Get contract details
                        contract_info = next((c for c in expiring_contracts if c['ContractID'] == contract_id), None)
                        if contract_info:
                            # Determine extension base date
                            if contract_info['Status'] == 'Expired':
                                base_date = datetime.date.today()
                            else:
                                base_date = contract_info['ExpirationDate']
                            
                            # Calculate new expiration date
                            new_exp_date = base_date + datetime.timedelta(days=days)
                            
                            if extend_contract(contract_id, new_exp_date):
                                success_count += 1
                    
                    if success_count > 0:
                        # Set success flag and redirect to view tab
                        st.session_state.contract_extended = True
                        st.session_state.show_success = True
                        st.rerun()
                    else:
                        st.error("Failed to extend contracts.")
                else:
                    st.warning("Please select at least one contract to extend.")
    else:
        st.info("No contracts are nearing expiration or have expired.")
