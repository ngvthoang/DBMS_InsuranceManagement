import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection, execute_query, get_cached_data, execute_write_query
from models.customer import get_customers
from models.insurance_type import get_all_insurance_types
from mysql.connector import Error

@st.cache_data(ttl=300)
def get_all_contracts():
    """Get all contracts with customer and insurance type information"""
    query = """
        SELECT c.ContractID, c.CustomerID, cust.CustomerName, c.InsuranceTypeID, 
               t.InsuranceName, c.SignDate, c.ExpirationDate, c.Status
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_contract_by_id(contract_id):
    """Get a specific contract by ID"""
    query = """
        SELECT c.ContractID, c.CustomerID, cust.CustomerName, c.InsuranceTypeID, 
               t.InsuranceName, c.SignDate, c.ExpirationDate, c.Status
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        WHERE c.ContractID = %s
    """
    result = get_cached_data(query, (contract_id,))
    if result and len(result) > 0:
        return result[0]
    return None

@st.cache_data(ttl=300)
def get_contracts_dropdown():
    """Get contracts for dropdown selection"""
    query = """
        SELECT c.ContractID, cust.CustomerName, t.InsuranceName
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
    """
    contracts = get_cached_data(query)
    if not contracts:
        return {}
    return {f"{c['ContractID']}: {c['CustomerName']} - {c['InsuranceName']}": c['ContractID'] for c in contracts}

@st.cache_data(ttl=300)
def get_contracts_by_customer(customer_id):
    """Get all contracts for a specific customer"""
    query = """
        SELECT c.ContractID, t.InsuranceName, c.SignDate, c.ExpirationDate, c.Status
        FROM InsuranceContracts c
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        WHERE c.CustomerID = %s
        ORDER BY c.SignDate DESC
    """
    return get_cached_data(query, (customer_id,))

@st.cache_data(ttl=300)
def get_expiring_contracts():
    """Get contracts that are expiring within 3 months or have expired"""
    query = """
        SELECT c.ContractID, cust.CustomerName, t.InsuranceName, c.SignDate, c.ExpirationDate, c.Status
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        WHERE c.ExpirationDate BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 MONTH)
        OR (c.ExpirationDate < CURDATE() AND c.Status = 'Expired')
        ORDER BY c.ExpirationDate
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_contract_assessments(contract_id):
    """Get all assessments for a specific contract"""
    query = """
        SELECT AssessmentID, AssessmentDate, ClaimAmount, Result
        FROM Assessments
        WHERE ContractID = %s
        ORDER BY AssessmentDate DESC
    """
    return get_cached_data(query, (contract_id,))

@st.cache_data(ttl=300)
def get_contract_payouts(contract_id):
    """Get all payouts for a specific contract"""
    query = """
        SELECT PayoutID, PayoutDate, Amount, Status
        FROM Payouts
        WHERE ContractID = %s
        ORDER BY PayoutDate DESC
    """
    return get_cached_data(query, (contract_id,))

def generate_next_contract_id():
    """Generate the next contract ID"""
    last_contract = get_cached_data("SELECT ContractID FROM InsuranceContracts ORDER BY ContractID DESC LIMIT 1")
    next_id = "CT001"  # Default starting ID if no records exist
    
    if last_contract and len(last_contract) > 0:
        last_id = last_contract[0]['ContractID']
        # Extract the numeric part, increment it, and format it back
        try:
            id_num = int(last_id[2:])
            next_id = f"CT{(id_num + 1):03d}"
        except (ValueError, IndexError):
            pass  # Use default if parsing fails
    
    return next_id

def add_contract(contract_id, customer_id, insurance_type_id, sign_date):
    """Add a new contract to the database"""
    query = """
    INSERT INTO InsuranceContracts (ContractID, CustomerID, InsuranceTypeID, SignDate) 
    VALUES (%s, %s, %s, %s)
    """
    data = (contract_id, customer_id, insurance_type_id, sign_date)
    result = execute_write_query(query, data)
    
    # Clear cache for contract-related functions
    if hasattr(get_all_contracts, 'clear'):
        get_all_contracts.clear()
    if hasattr(get_contracts_dropdown, 'clear'):
        get_contracts_dropdown.clear()
    if hasattr(get_contracts_by_customer, 'clear'):
        get_contracts_by_customer.clear()
    if hasattr(get_expiring_contracts, 'clear'):
        get_expiring_contracts.clear()
    
    return result

def update_contract(contract_id, customer_id, insurance_type_id, sign_date, expiration_date):
    """Update an existing contract in the database"""
    query = """
    UPDATE InsuranceContracts 
    SET CustomerID = %s, InsuranceTypeID = %s, SignDate = %s, ExpirationDate = %s
    WHERE ContractID = %s
    """
    data = (customer_id, insurance_type_id, sign_date, expiration_date, contract_id)
    result = execute_write_query(query, data)
    
    # Clear cache for contract-related functions
    if hasattr(get_all_contracts, 'clear'):
        get_all_contracts.clear()
    if hasattr(get_contract_by_id, 'clear'):
        get_contract_by_id.clear()
    if hasattr(get_contracts_dropdown, 'clear'):
        get_contracts_dropdown.clear()
    if hasattr(get_contracts_by_customer, 'clear'):
        get_contracts_by_customer.clear()
    if hasattr(get_expiring_contracts, 'clear'):
        get_expiring_contracts.clear()
    
    return result

def extend_contract(contract_id, new_expiration_date):
    """Extend a contract's expiration date"""
    # Format the date properly for MySQL - this is critical
    if isinstance(new_expiration_date, datetime.date):
        formatted_date = new_expiration_date.strftime('%Y-%m-%d')
    else:
        formatted_date = str(new_expiration_date)
    
    query = """
    UPDATE InsuranceContracts 
    SET ExpirationDate = %s, Status = 'Active'
    WHERE ContractID = %s
    """
    data = (formatted_date, contract_id)
    
    # Force clear cache before executing the query
    st.cache_data.clear()
    
    # Execute the update query
    result = execute_write_query(query, data)
    
    # Clear individual function caches if they exist
    try:
        if hasattr(get_all_contracts, 'clear'):
            get_all_contracts.clear()
        if hasattr(get_contract_by_id, 'clear'):
            get_contract_by_id.clear()
        if hasattr(get_contracts_dropdown, 'clear'):
            get_contracts_dropdown.clear()
        if hasattr(get_contracts_by_customer, 'clear'):
            get_contracts_by_customer.clear()
        if hasattr(get_expiring_contracts, 'clear'):
            get_expiring_contracts.clear()
    except Exception as e:
        print(f"Error clearing cache: {e}")

    return result
