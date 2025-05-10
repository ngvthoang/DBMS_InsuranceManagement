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
            password=os.getenv("DB_PASSWORD", "")
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

def execute_query(connection, query, data=None):
    """Execute SQL query and return result if it's a SELECT query"""
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
