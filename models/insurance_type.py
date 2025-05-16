import streamlit as st
import pandas as pd
from mysql.connector import Error
from database.db_connector import get_cached_data, execute_write_query

def get_all_insurance_types():
    """Get all insurance types from database with caching"""
    return get_cached_data("SELECT * FROM InsuranceTypes")

def get_insurance_type_by_id(type_id):
    """Get a specific insurance type by ID"""
    result = get_cached_data("SELECT * FROM InsuranceTypes WHERE InsuranceTypeID = %s", (type_id,))
    if result and len(result) > 0:
        return result[0]
    return None

def get_insurance_types_dropdown():
    """Get insurance types for dropdown selection"""
    types = get_cached_data("SELECT InsuranceTypeID, InsuranceName FROM InsuranceTypes")
    if not types:
        return {}
    return {f"{t['InsuranceTypeID']}: {t['InsuranceName']}": t['InsuranceTypeID'] for t in types}

def generate_next_insurance_type_id():
    """Generate the next insurance type ID"""
    last_type = get_cached_data("SELECT InsuranceTypeID FROM InsuranceTypes ORDER BY InsuranceTypeID DESC LIMIT 1")
    next_id = "T001"  # Default starting ID if no records exist
    
    if last_type and len(last_type) > 0:
        last_id = last_type[0]['InsuranceTypeID']
        # Extract the numeric part, increment it, and format it back
        try:
            id_num = int(last_id[1:])
            next_id = f"T{(id_num + 1):03d}"
        except (ValueError, IndexError):
            pass  # Use default if parsing fails
    
    return next_id

def add_insurance_type(type_id, type_name, description):
    """Add a new insurance type to the database"""
    query = """
    INSERT INTO InsuranceTypes (InsuranceTypeID, InsuranceName, Description) 
    VALUES (%s, %s, %s)
    """
    data = (type_id, type_name, description)
    return execute_write_query(query, data)

def update_insurance_type(type_id, type_name, description):
    """Update an existing insurance type in the database"""
    query = """
    UPDATE InsuranceTypes 
    SET InsuranceName = %s, Description = %s
    WHERE InsuranceTypeID = %s
    """
    data = (type_name, description, type_id)
    return execute_write_query(query, data)

def delete_insurance_type(type_id):
    """Delete an insurance type from the database"""
    query = "DELETE FROM InsuranceTypes WHERE InsuranceTypeID = %s"
    return execute_write_query(query, (type_id,))
