import streamlit as st
import pandas as pd
from mysql.connector import Error
from database.db_connector import get_cached_data, execute_write_query

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
    customers = get_all_customers()
    if customers:
        df_customers = pd.DataFrame(customers)
        st.dataframe(df_customers, use_container_width=True)
    else:
        st.info("No customers found in the database.")

def add_customer_form():
    """Display the form to add a new customer"""
    with st.form("add_customer_form"):
        # Auto-generate next ID
        next_id = generate_next_customer_id()
                
        customer_id = st.text_input("Customer ID (e.g., C006)", value=next_id)
        customer_name = st.text_input("Customer Name")
        address = st.text_area("Address")
        phone = st.text_input("Phone Number")
        
        submitted = st.form_submit_button("Add Customer")
        if submitted:
            if customer_id and customer_name and address and phone:
                # Insert the new customer
                result = add_customer(customer_id, customer_name, address, phone)
                if result:
                    st.markdown('<div class="success-msg">Customer added successfully!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-msg">Failed to add customer.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)

def edit_customer_form():
    """Display the form to edit an existing customer"""
    customer_options = get_customers_dropdown()
    if customer_options:
        selected_customer = st.selectbox("Select Customer to Edit", options=list(customer_options.keys()))
        
        if selected_customer:
            customer_id = customer_options[selected_customer]
            customer_data = get_customer_by_id(customer_id)
            
            if customer_data:
                display_edit_form(customer_id, customer_data)
    else:
        st.info("No customers found in the database.")

def display_edit_form(customer_id, customer):
    """Display the edit form with current customer data"""
    with st.form("edit_customer_form"):
        customer_name = st.text_input("Customer Name", value=customer['CustomerName'])
        address = st.text_area("Address", value=customer['Address'])
        phone = st.text_input("Phone Number", value=customer['PhoneNumber'])
        
        submitted = st.form_submit_button("Update Customer")
        if submitted:
            if customer_name and address and phone:
                result = update_customer(customer_id, customer_name, address, phone)
                if result:
                    st.markdown('<div class="success-msg">Customer updated successfully!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-msg">Failed to update customer.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-msg">Please fill in all the required fields.</div>', unsafe_allow_html=True)

def get_all_customers():
    """Get all customers from database with caching"""
    return get_cached_data("SELECT * FROM Customers")

def get_customer_by_id(customer_id):
    """Get a specific customer by ID"""
    result = get_cached_data("SELECT * FROM Customers WHERE CustomerID = %s", (customer_id,))
    if result and len(result) > 0:
        return result[0]
    return None

def get_customers_dropdown():
    """Get customers for dropdown selection"""
    customers = get_cached_data("SELECT CustomerID, CustomerName FROM Customers")
    if not customers:
        return {}
    return {f"{cust['CustomerID']}: {cust['CustomerName']}": cust['CustomerID'] for cust in customers}

def generate_next_customer_id():
    """Generate the next customer ID"""
    last_customer = get_cached_data("SELECT CustomerID FROM Customers ORDER BY CustomerID DESC LIMIT 1")
    next_id = "C001"  # Default starting ID if no records exist
    
    if last_customer and len(last_customer) > 0:
        last_id = last_customer[0]['CustomerID']
        # Extract the numeric part, increment it, and format it back
        try:
            id_num = int(last_id[1:])
            next_id = f"C{(id_num + 1):03d}"
        except (ValueError, IndexError):
            pass  # Use default if parsing fails
    
    return next_id

def add_customer(customer_id, customer_name, address, phone):
    """Add a new customer to the database"""
    query = """
    INSERT INTO Customers (CustomerID, CustomerName, Address, PhoneNumber) 
    VALUES (%s, %s, %s, %s)
    """
    data = (customer_id, customer_name, address, phone)
    return execute_write_query(query, data)

def update_customer(customer_id, customer_name, address, phone):
    """Update an existing customer in the database"""
    query = """
    UPDATE Customers 
    SET CustomerName = %s, Address = %s, PhoneNumber = %s
    WHERE CustomerID = %s
    """
    data = (customer_name, address, phone, customer_id)
    return execute_write_query(query, data)

def delete_customer(customer_id):
    """Delete a customer from the database"""
    query = "DELETE FROM Customers WHERE CustomerID = %s"
    result = execute_write_query(query, (customer_id,))
    
    # Clear cache specifically for customer data
    if hasattr(get_all_customers, 'clear'):
        get_all_customers.clear()
    if hasattr(get_customers_dropdown, 'clear'):
        get_customers_dropdown.clear()
    
    return result

def get_customers():
    """Get all customers from database - alias for get_all_customers"""
    return get_all_customers()
