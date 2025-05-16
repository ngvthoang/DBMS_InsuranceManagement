import streamlit as st
import pandas as pd
from database.db_connector import create_connection
from models.customer import (
    get_all_customers,  
    get_customer_by_id,
    get_customers_dropdown,
    generate_next_customer_id,
    add_customer,
    update_customer,
    delete_customer
)
from models.contract import get_contracts_by_customer

st.set_page_config(page_title="Customer Management", page_icon="👥", layout="wide")

# Customer Management page
st.markdown('# Customer Management')
st.markdown('Add, view, and edit customer information')
st.markdown('---')

# Check database connection
conn = create_connection()
if not conn:
    st.error("Could not connect to the database. Please check your connection settings.")
    st.stop()
else:
    conn.close()

# Initialize session state for success messages
if 'customer_added' not in st.session_state:
    st.session_state.customer_added = False
if 'customer_updated' not in st.session_state:
    st.session_state.customer_updated = False
if 'customer_deleted' not in st.session_state:
    st.session_state.customer_deleted = False
if 'show_success' not in st.session_state:
    st.session_state.show_success = False

# Create tabs
tab1, tab2, tab3 = st.tabs(["View Customers", "Add Customer", "Edit Customer"])

# View Customers Tab
with tab1:
    st.subheader("All Customers")
    
    # Show success messages if redirected from other tabs
    if st.session_state.show_success:
        if st.session_state.customer_added:
            st.success("Customer added successfully!")
            st.session_state.customer_added = False
        elif st.session_state.customer_updated:
            st.success("Customer updated successfully!")
            st.session_state.customer_updated = False
        elif st.session_state.customer_deleted:
            st.success("Customer deleted successfully!")
            st.session_state.customer_deleted = False
        
        # Reset the success flag after showing
        st.session_state.show_success = False
    
    # Refresh button
    if st.button("🔄 Refresh", key="refresh_customers"):
        st.cache_data.clear()
        st.rerun()
    
    # Get and display customers
    customers = get_all_customers()
    if customers:
        df = pd.DataFrame(customers)
        st.dataframe(df, use_container_width=True)
        
        # Customer details section
        st.subheader("Customer Details")
        
        # Get customer dropdown options
        customer_options = get_customers_dropdown()
        selected_customer = st.selectbox(
            "Select a customer to view details:",
            options=list(customer_options.keys())
        )
        
        if selected_customer:
            customer_id = customer_options[selected_customer]
            customer = get_customer_by_id(customer_id)
            
            if customer:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Customer ID:** {customer['CustomerID']}")
                    st.markdown(f"**Name:** {customer['CustomerName']}")
                    st.markdown(f"**Phone:** {customer['PhoneNumber']}")
                    st.markdown(f"**Address:** {customer['Address']}")
                
                with col2:
                    # Show contracts for this customer
                    contracts = get_contracts_by_customer(customer_id)
                    if contracts:
                        st.markdown("**Contracts:**")
                        df_contracts = pd.DataFrame(contracts)
                        if 'SignDate' in df_contracts.columns:
                            df_contracts['SignDate'] = pd.to_datetime(df_contracts['SignDate']).dt.strftime('%Y-%m-%d')
                        if 'ExpirationDate' in df_contracts.columns:
                            df_contracts['ExpirationDate'] = pd.to_datetime(df_contracts['ExpirationDate']).dt.strftime('%Y-%m-%d')
                        st.dataframe(df_contracts, use_container_width=True)
                    else:
                        st.info("No contracts found for this customer.")
    else:
        st.info("No customers found in the database.")

# Add Customer Tab
with tab2:
    st.subheader("Add New Customer")
    
    with st.form("add_customer_form"):
        # Auto-generate customer ID
        next_id = generate_next_customer_id()
        
        customer_id = st.text_input("Customer ID", value=next_id)
        customer_name = st.text_input("Customer Name")
        address = st.text_area("Address")
        phone = st.text_input("Phone Number")
        
        submitted = st.form_submit_button("Add Customer")
        if submitted:
            if customer_id and customer_name and address and phone:
                if add_customer(customer_id, customer_name, address, phone):
                    # Set the success flags
                    st.session_state.customer_added = True
                    
                    # Rerun to show the success message
                    st.rerun()
                else:
                    st.error("Failed to add customer. Please try again.")
            else:
                st.error("Please fill in all required fields.")
    
    # show success message if customer was just added and clear the form
    if st.session_state.customer_added:
        st.success("Customer added successfully!")
        st.session_state.customer_added = False
        st.session_state.show_success = True


# Edit Customer Tab
with tab3:
    st.subheader("Edit Customer")
    
    # Get all customers for selection
    customer_options = get_customers_dropdown()
    if customer_options:
        selected_customer = st.selectbox(
            "Select customer to edit:",
            options=list(customer_options.keys()),
            key="edit_customer_select"
        )
        
        if selected_customer:
            customer_id = customer_options[selected_customer]
            customer = get_customer_by_id(customer_id)
            
            if customer:
                with st.form("edit_customer_form"):
                    edit_name = st.text_input("Customer Name", value=customer['CustomerName'])
                    edit_address = st.text_area("Address", value=customer['Address'])
                    edit_phone = st.text_input("Phone Number", value=customer['PhoneNumber'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_button = st.form_submit_button("Update Customer")
                    with col2:
                        delete_button = st.form_submit_button("Delete Customer", type="secondary")
                    
                    if update_button:
                        if edit_name and edit_address and edit_phone:
                            if update_customer(customer_id, edit_name, edit_address, edit_phone):
                                # Set success flag for update
                                st.session_state.customer_updated = True
                                st.rerun()
                            else:
                                st.error("Failed to update customer. Please try again.")
                        else:
                            st.error("Please fill in all required fields.")
                    
                    if delete_button:
                        # Handle the delete operation outside the form
                        st.session_state['show_delete_confirmation'] = True
                
                # Move delete confirmation outside the form
                if st.session_state.get('show_delete_confirmation', False):
                    st.warning("Are you sure you want to delete this customer? This cannot be undone.")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Yes, Delete Customer", key="confirm_delete"):
                            if delete_customer(customer_id):
                                # Set success flag for delete and redirect to view tab
                                st.session_state.customer_deleted = True
                                st.session_state.show_success = True
                                st.session_state['show_delete_confirmation'] = False
                                # Change tab index to view customers (tab1)
                                st.rerun()
                            else:
                                st.error("Failed to delete customer. This customer may have associated contracts.")
                    
                    with col2:
                        if st.button("Cancel", key="cancel_delete"):
                            # Clear the confirmation state
                            st.session_state['show_delete_confirmation'] = False
                            st.rerun()
    else:
        st.info("No customers found in the database.")
