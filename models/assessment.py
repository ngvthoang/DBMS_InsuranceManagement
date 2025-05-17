import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection, execute_query, get_cached_data, execute_write_query
from mysql.connector import Error

@st.cache_data(ttl=300)
def get_all_assessments():
    """Get all assessments with contract and customer information"""
    query = """
        SELECT a.AssessmentID, a.ContractID, c.CustomerID, c.CustomerName, 
               a.AssessmentDate, a.ClaimAmount, a.Result
        FROM Assessments a
        JOIN InsuranceContracts ic ON a.ContractID = ic.ContractID
        JOIN Customers c ON ic.CustomerID = c.CustomerID
        ORDER BY a.AssessmentDate DESC
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_assessment_by_id(assessment_id):
    """Get a specific assessment by ID"""
    query = """
        SELECT a.AssessmentID, a.ContractID, c.CustomerID, c.CustomerName, 
               a.AssessmentDate, a.ClaimAmount, a.Result
        FROM Assessments a
        JOIN InsuranceContracts ic ON a.ContractID = ic.ContractID
        JOIN Customers c ON ic.CustomerID = c.CustomerID
        WHERE a.AssessmentID = %s
    """
    result = get_cached_data(query, (assessment_id,))
    if result and len(result) > 0:
        return result[0]
    return None

@st.cache_data(ttl=300)
def get_assessments_dropdown():
    """Get assessments for dropdown selection"""
    query = """
        SELECT a.AssessmentID, c.CustomerName, a.ClaimAmount
        FROM Assessments a
        JOIN InsuranceContracts ic ON a.ContractID = ic.ContractID
        JOIN Customers c ON ic.CustomerID = c.CustomerID
    """
    assessments = get_cached_data(query)
    if not assessments:
        return {}
    return {f"{a['AssessmentID']}: {a['CustomerName']} - ${float(a['ClaimAmount']):,.2f}": a['AssessmentID'] for a in assessments}

@st.cache_data(ttl=300)
def get_pending_assessments():
    """Get assessments with pending status"""
    query = """
        SELECT a.AssessmentID, a.ContractID, c.CustomerName,
               a.AssessmentDate, a.ClaimAmount, a.Result
        FROM Assessments a
        JOIN InsuranceContracts ic ON a.ContractID = ic.ContractID
        JOIN Customers c ON ic.CustomerID = c.CustomerID
        WHERE a.Result = 'Pending'
        ORDER BY a.AssessmentDate
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_approved_claims():
    """Get assessments with approved status"""
    query = """
        SELECT a.AssessmentID, a.ContractID, c.CustomerName,
               a.AssessmentDate, a.ClaimAmount, a.Result
        FROM Assessments a
        JOIN InsuranceContracts ic ON a.ContractID = ic.ContractID
        JOIN Customers c ON ic.CustomerID = c.CustomerID
        WHERE a.Result = 'Approved'
        ORDER BY a.AssessmentDate DESC
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_active_contracts_dropdown():
    """Get active contracts for dropdown selection"""
    query = """
        SELECT c.ContractID, cust.CustomerName, t.InsuranceName
        FROM InsuranceContracts c
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        WHERE c.Status = 'Active'
    """
    contracts = get_cached_data(query)
    if not contracts:
        return {}
    return {f"{c['ContractID']}: {c['CustomerName']} - {c['InsuranceName']}": c['ContractID'] for c in contracts}

@st.cache_data(ttl=300)
def get_related_payout(contract_id, claim_amount):
    """Get payout related to an assessment"""
    query = """
        SELECT PayoutID, ContractID, PayoutDate, Amount, Status
        FROM Payouts
        WHERE ContractID = %s AND Amount = %s
    """
    return get_cached_data(query, (contract_id, claim_amount))

@st.cache_data(ttl=300)
def get_related_assessment(contract_id, claim_amount):
    """Get assessment related to a payout"""
    query = """
        SELECT AssessmentID, ContractID, AssessmentDate, ClaimAmount, Result
        FROM Assessments
        WHERE ContractID = %s AND ClaimAmount = %s AND Result = 'Approved'
    """
    return get_cached_data(query, (contract_id, claim_amount))

def generate_next_assessment_id():
    """Generate the next assessment ID"""
    last_assessment = get_cached_data("SELECT AssessmentID FROM Assessments ORDER BY AssessmentID DESC LIMIT 1")
    next_id = "A001"  # Default starting ID if no records exist
    
    if last_assessment and len(last_assessment) > 0:
        last_id = last_assessment[0]['AssessmentID']
        # Extract the numeric part, increment it, and format it back
        try:
            id_num = int(last_id[1:])
            next_id = f"A{(id_num + 1):03d}"
        except (ValueError, IndexError):
            pass  # Use default if parsing fails
    
    return next_id

def add_assessment(assessment_id, contract_id, assessment_date, claim_amount, result):
    """Add a new assessment to the database"""
    query = """
    INSERT INTO Assessments (AssessmentID, ContractID, AssessmentDate, ClaimAmount, Result) 
    VALUES (%s, %s, %s, %s, %s)
    """
    data = (assessment_id, contract_id, assessment_date, claim_amount, result)
    result = execute_write_query(query, data)
    
    # Clear cache for assessment-related functions
    if hasattr(get_all_assessments, 'clear'):
        get_all_assessments.clear()
    if hasattr(get_assessments_dropdown, 'clear'):
        get_assessments_dropdown.clear()
    if hasattr(get_pending_assessments, 'clear'):
        get_pending_assessments.clear()
    if hasattr(get_approved_claims, 'clear'):
        get_approved_claims.clear()
    
    return result

def update_assessment_result(assessment_id, new_result):
    """Update an assessment's result"""
    query = """
    UPDATE Assessments 
    SET Result = %s
    WHERE AssessmentID = %s
    """
    data = (new_result, assessment_id)
    result = execute_write_query(query, data)
    
    # Clear cache for assessment-related functions
    if hasattr(get_all_assessments, 'clear'):
        get_all_assessments.clear()
    if hasattr(get_assessment_by_id, 'clear'):
        get_assessment_by_id.clear()
    if hasattr(get_assessments_dropdown, 'clear'):
        get_assessments_dropdown.clear()
    if hasattr(get_pending_assessments, 'clear'):
        get_pending_assessments.clear()
    if hasattr(get_approved_claims, 'clear'):
        get_approved_claims.clear()
    
    return result
