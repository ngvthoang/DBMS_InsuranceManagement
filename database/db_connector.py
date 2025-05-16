import os
import streamlit as st
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_connection():
    """Create a database connection to MySQL server"""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "prj_insurance"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            connect_timeout=10  # Add connect timeout
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

@st.cache_data(ttl=300)  # Cache data for 5 minutes
def get_cached_data(query, params=None):
    """Execute a SELECT query and cache the results"""
    connection = create_connection()
    if not connection:
        st.warning("Database connection failed. Please check your connection settings.")
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        result = cursor.fetchall()
        return result
    except Error as e:
        st.error(f"Error executing query: {e}")
        st.code(query, language="sql")  # Show the query for debugging
        return None
    finally:
        if connection:
            if connection.is_connected():
                cursor.close()
                connection.close()

def execute_query(connection, query, data=None):
    """Execute SQL query and return result if it's a SELECT query"""
    if not connection:
        return None
        
    cursor = connection.cursor(dictionary=True)
    try:
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        
        if query.lower().strip().startswith("select"):
            result = cursor.fetchall()
            return result
        else:
            connection.commit()
            return cursor.lastrowid
    except Error as e:
        st.error(f"Error executing query: {e}")
        return None
    finally:
        cursor.close()

def execute_write_query(query, data=None):
    """Execute non-SELECT queries (INSERT, UPDATE, DELETE) and handle connection"""
    connection = create_connection()
    if not connection:
        st.warning("Database connection failed. Please check your connection settings.")
        return False
    
    try:
        cursor = connection.cursor()
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        
        connection.commit()
        success = True
    except Error as e:
        st.error(f"Error executing query: {e}")
        st.code(query, language="sql")  # Show the query for debugging
        if data:
            st.write(f"Parameters: {data}")  # Show parameters for debugging
        success = False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
    
    # Clear cache after write operations
    if success:
        get_cached_data.clear()
    
    return success
