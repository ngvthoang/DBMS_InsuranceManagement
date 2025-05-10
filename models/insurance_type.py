import streamlit as st
import pandas as pd
from database.db_connector import create_connection, execute_query

def display_insurance_types():
    """Display the insurance types management section"""
    st.markdown('<div class="sub-header">Insurance Types Management</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Insurance Types", "Add Insurance Type"])
    
    # View Insurance Types Tab
    with tab1:
        display_all_types()
    
    # Add Insurance Type Tab
    with tab2:
        add_type_form()

def display_all_types():
    """Display a table of all insurance types"""
    connection = create_connection()
    if connection:
        insurance_types = execute_query(connection, "SELECT * FROM InsuranceTypes")
        if insurance_types:
            df_types = pd.DataFrame(insurance_types)
            st.dataframe(df_types, use_container_width=True)
        else:
            st.info("No insurance types found in the database.")
        connection.close()

def add_type_form():
    """Display the form to add a new insurance type"""
    with st.form("add_insurance_type_form"):
        type_id = st.text_input("Insurance Type ID (e.g., T006)")
        type_name = st.text_input("Insurance Name")
        description = st.text_area("Description")
        
        submitted = st.form_submit_button("Add Insurance Type")
        if submitted:
            if type_id and type_name and description:
                save_insurance_type(type_id, type_name, description)
            else:
                st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)

def save_insurance_type(type_id, type_name, description):
    """Save a new insurance type to the database"""
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

def get_insurance_types():
    """Get all insurance types from the database"""
    connection = create_connection()
    if connection:
        insurance_types = execute_query(connection, "SELECT InsuranceTypeID, InsuranceName FROM InsuranceTypes")
        connection.close()
        return insurance_types
    return []
