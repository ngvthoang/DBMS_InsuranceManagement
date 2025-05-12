import streamlit as st
import pandas as pd
from database.db_connector import create_connection, execute_query
from mysql.connector import Error
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

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
            
            # Configure AgGrid
            gb = GridOptionsBuilder.from_dataframe(df_types)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_side_bar()
            gb.configure_default_column(editable=True, filter=True)
            grid_options = gb.build()

            # Display the interactive table
            AgGrid(
                df_types,
                gridOptions=grid_options,
                enable_enterprise_modules=True,
                theme="blue",
                height=400,
                fit_columns_on_grid_load=True,
            )
        else:
            st.info("No insurance types found in the database.")
        connection.close()

def add_type_form():
    """Display the form to add a new insurance type"""
    with st.form("add_insurance_type_form"):
        # Auto-generate next ID
        connection = create_connection()
        if connection:
            next_id = "T001"  # Default starting ID if no records exist
            try:
                last_type = execute_query(connection, "SELECT InsuranceTypeID FROM InsuranceTypes ORDER BY InsuranceTypeID DESC LIMIT 1")
                if last_type:
                    last_id = last_type[0]['InsuranceTypeID']
                    next_id = f"T{int(last_id[1:]) + 1:03d}"
            except Error as e:
                st.error(f"Error fetching last insurance type ID: {e}")
            finally:
                connection.close()
                
        type_id = st.text_input("Insurance Type ID (e.g., T006)", value=next_id)
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
