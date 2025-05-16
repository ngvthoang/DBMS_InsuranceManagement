import streamlit as st
import pandas as pd
from database.db_connector import create_connection
from models.insurance_type import (
    get_all_insurance_types,
    get_insurance_type_by_id,
    get_insurance_types_dropdown,
    generate_next_insurance_type_id,
    add_insurance_type,
    update_insurance_type,
    delete_insurance_type
)

# Check the curent user role if they are allowed to access this page
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("Access denied. Please log in to view this page.")
    st.stop()
if "role" not in st.session_state or st.session_state["role"] not in ["Admin", "Insurance Agent"]:
    st.error("Access denied. You do not have permission to view this page.")
    st.stop()

st.set_page_config(page_title="Insurance Types", page_icon="📋", layout="wide")

# Insurance Types page
st.markdown('# Insurance Types')
st.markdown('Manage different types of insurance products')
st.markdown('---')

# Check database connection
conn = create_connection()
if not conn:
    st.error("Could not connect to the database. Please check your connection settings.")
    st.stop()
else:
    conn.close()

# Initialize session state for success messages
if 'type_added' not in st.session_state:
    st.session_state.type_added = False
if 'type_updated' not in st.session_state:
    st.session_state.type_updated = False
if 'type_deleted' not in st.session_state:
    st.session_state.type_deleted = False
if 'show_success' not in st.session_state:
    st.session_state.show_success = False

# Create tabs
tab1, tab2, tab3 = st.tabs(["View Insurance Types", "Add Insurance Type", "Edit Insurance Type"])

# View Insurance Types Tab
with tab1:
    # Show success messages if redirected from other tabs
    if st.session_state.show_success:
        if st.session_state.type_added:
            st.success("Insurance type added successfully!")
            st.session_state.type_added = False
        elif st.session_state.type_updated:
            st.success("Insurance type updated successfully!")
            st.session_state.type_updated = False
        elif st.session_state.type_deleted:
            st.success("Insurance type deleted successfully!")
            st.session_state.type_deleted = False
        
        # Reset the success flag after showing
        st.session_state.show_success = False
    
    st.subheader("All Insurance Types")
    
    # Refresh button
    if st.button("🔄 Refresh", key="refresh_types"):
        st.cache_data.clear()
        st.rerun()
    
    # Get and display insurance types
    insurance_types = get_all_insurance_types()
    if insurance_types:
        df = pd.DataFrame(insurance_types)
        st.dataframe(df, use_container_width=True)
        
        # Insurance type details section
        st.subheader("Insurance Type Details")
        
        # Get insurance type dropdown options
        type_options = get_insurance_types_dropdown()
        selected_type = st.selectbox(
            "Select an insurance type to view details:",
            options=list(type_options.keys())
        )
        
        if selected_type:
            type_id = type_options[selected_type]
            insurance_type = get_insurance_type_by_id(type_id)
            
            if insurance_type:
                st.markdown(f"**Insurance Type ID:** {insurance_type['InsuranceTypeID']}")
                st.markdown(f"**Name:** {insurance_type['InsuranceName']}")
                st.markdown("**Description:**")
                st.write(insurance_type['Description'])
    else:
        st.info("No insurance types found in the database.")

# Add Insurance Type Tab
with tab2:
    st.subheader("Add New Insurance Type")
    
    with st.form("add_insurance_type_form"):
        # Auto-generate insurance type ID
        next_id = generate_next_insurance_type_id()
        
        type_id = st.text_input("Insurance Type ID", value=next_id)
        type_name = st.text_input("Insurance Name")
        description = st.text_area("Description")
        
        submitted = st.form_submit_button("Add Insurance Type")
        if submitted:
            if type_id and type_name and description:
                if add_insurance_type(type_id, type_name, description):
                    # Set success flag
                    st.session_state.type_added = True
                    
                    # Rerun to show the success message
                    st.rerun()
                else:
                    st.error("Failed to add insurance type. Please try again.")
            else:
                st.error("Please fill in all required fields.")
    
    # Show success message if type was just added
    if st.session_state.type_added:
        st.success("Insurance type added successfully!")
        st.session_state.type_added = False
        st.session_state.show_success = True

# Edit Insurance Type Tab
with tab3:
    st.subheader("Edit Insurance Type")
    
    # Get all insurance types for selection
    type_options = get_insurance_types_dropdown()
    if type_options:
        selected_type = st.selectbox(
            "Select insurance type to edit:",
            options=list(type_options.keys()),
            key="edit_type_select"
        )
        
        if selected_type:
            type_id = type_options[selected_type]
            insurance_type = get_insurance_type_by_id(type_id)
            
            if insurance_type:
                with st.form("edit_insurance_type_form"):
                    edit_name = st.text_input("Insurance Name", value=insurance_type['InsuranceName'])
                    edit_description = st.text_area("Description", value=insurance_type['Description'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_button = st.form_submit_button("Update Insurance Type")
                    with col2:
                        delete_button = st.form_submit_button("Delete Insurance Type", type="secondary")
                    
                    if update_button:
                        if edit_name and edit_description:
                            if update_insurance_type(type_id, edit_name, edit_description):
                                # Set success flag
                                st.session_state.type_updated = True
                                st.rerun()
                            else:
                                st.error("Failed to update insurance type. Please try again.")
                        else:
                            st.error("Please fill in all required fields.")
                    
                    if delete_button:
                        # Handle the delete operation outside the form
                        st.session_state['show_delete_confirmation'] = True
                
                # Move delete confirmation outside the form
                if st.session_state.get('show_delete_confirmation', False):
                    st.warning(f"Are you sure you want to delete the insurance type '{insurance_type['InsuranceName']}'? This cannot be undone.")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Yes, Delete Insurance Type", key="confirm_delete_type"):
                            if delete_insurance_type(type_id):
                                # Set success flag for delete and redirect to view tab
                                st.session_state.type_deleted = True
                                st.session_state.show_success = True
                                st.session_state['show_delete_confirmation'] = False
                                # Rerun to refresh the page
                                st.rerun()
                            else:
                                st.error("Failed to delete insurance type. It may be used in existing contracts.")
                    
                    with col2:
                        if st.button("Cancel", key="cancel_delete_type"):
                            # Clear the confirmation state
                            st.session_state['show_delete_confirmation'] = False
                            st.rerun()
    else:
        st.info("No insurance types found in the database.")
    
    # Show success message if type was just updated
    if st.session_state.type_updated:
        st.success("Insurance type updated successfully!")
        st.session_state.type_updated = False
