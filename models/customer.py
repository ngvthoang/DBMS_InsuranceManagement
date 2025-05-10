import streamlit as st
import pandas as pd
from database.db_connector import create_connection, execute_query

def display_customer_management():
    """Display the customer management section"""
    st.markdown('<div class="sub-header">Customer Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["View Customers", "Add Customer", "Edit Customer"])
    
    # View Customers Tab
    with tab1:
        display_customers()
    
    # Add Customer Tab
    with tab2:
        add_customer_form()
    
    # Edit Customer Tab
    with tab3:
        edit_customer_form()

def display_customers():
    """Display a table of all customers"""
    connection = create_connection()
    if connection:
        customers = execute_query(connection, "SELECT * FROM Customers")
        if customers:
            df_customers = pd.DataFrame(customers)
            st.dataframe(df_customers, use_container_width=True)
        else:
            st.info("No customers found in the database.")
        connection.close()

def add_customer_form():
    """Display the form to add a new customer"""
    with st.form("add_customer_form"):
        customer_id = st.text_input("Customer ID (e.g., C006)")
        customer_name = st.text_input("Customer Name")
        address = st.text_area("Address")
        phone = st.text_input("Phone Number")
        
        submitted = st.form_submit_button("Add Customer")
        if submitted:
            if customer_id and customer_name and address and phone:
                # Create a connection and insert the new customer
                save_customer(customer_id, customer_name, address, phone)
            else:
                st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)

def save_customer(customer_id, customer_name, address, phone):
    """Save a new customer to the database"""
    connection = create_connection()
    if connection:
        insert_query = """
        INSERT INTO Customers (CustomerID, CustomerName, Address, PhoneNumber) 
        VALUES (%s, %s, %s, %s)
        """
        data = (customer_id, customer_name, address, phone)
        result = execute_query(connection, insert_query, data)
        if result is not None:
            st.markdown('<div class="success-msg">Customer added successfully!</div>', unsafe_allow_html=True)
        connection.close()

def edit_customer_form():
    """Display the form to edit an existing customer"""
    connection = create_connection()
    if connection:
        customers = execute_query(connection, "SELECT CustomerID, CustomerName FROM Customers")
        if customers:
            customer_options = {f"{cust['CustomerID']}: {cust['CustomerName']}" for cust in customers}
            selected_customer = st.selectbox("Select Customer to Edit", options=customer_options)
            
            if selected_customer:
                customer_id = selected_customer.split(':')[0].strip()
                customer_data = execute_query(connection, "SELECT * FROM Customers WHERE CustomerID = %s", (customer_id,))
                
                if customer_data:
                    display_edit_form(customer_id, customer_data[0])
        else:
            st.info("No customers found in the database.")
        connection.close()

def display_edit_form(customer_id, customer):
    """Display the edit form with current customer data"""
    with st.form("edit_customer_form"):
        customer_name = st.text_input("Customer Name", value=customer['CustomerName'])
        address = st.text_area("Address", value=customer['Address'])
        phone = st.text_input("Phone Number", value=customer['PhoneNumber'])
        
        submitted = st.form_submit_button("Update Customer")
        if submitted:
            if customer_name and address and phone:
                update_customer(customer_id, customer_name, address, phone)
            else:
                st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)

def update_customer(customer_id, customer_name, address, phone):
    """Update an existing customer in the database"""
    connection = create_connection()
    if connection:
        update_query = """
        UPDATE Customers 
        SET CustomerName = %s, Address = %s, PhoneNumber = %s
        WHERE CustomerID = %s
        """
        data = (customer_name, address, phone, customer_id)
        result = execute_query(connection, update_query, data)
        if result is not None:
            st.markdown('<div class="success-msg">Customer updated successfully!</div>', unsafe_allow_html=True)
        connection.close()

def get_customers():
    """Get all customers from the database"""
    connection = create_connection()
    if connection:
        customers = execute_query(connection, "SELECT CustomerID, CustomerName FROM Customers")
        connection.close()
        return customers
    return []
