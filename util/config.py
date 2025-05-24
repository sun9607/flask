import os

import mysql.connector


def get_db_connection():
    try:
        config = {
            "user": os.getenv("SQL_USER"),
            "password": os.getenv("SQL_PASSWORD"),
            "host": "localhost",
            "database": "invitationcard_db"
        }
        return mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


def query_data(query):
    conn = get_db_connection()
    if conn is not None and conn.is_connected():
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    return None


def insert_data(query, value=None):
    conn = get_db_connection()
    if conn is not None and conn.is_connected():
        cursor = conn.cursor()
        if value is None:
            cursor.execute(query)
        else:
            cursor.execute(query, value)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False
