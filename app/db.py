import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get the database password from environment variables
DB_PASSWORD = os.getenv('DB_PASSWORD')

def create_table_if_not_exists():
    # Connect to MySQL/MariaDB
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', '')
    )
    cursor = connection.cursor()

    # Create the transactions table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            amount DECIMAL(10, 2) NOT NULL,
            type ENUM('income', 'expense') NOT NULL,
            category VARCHAR(50),
            description TEXT,
            user VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    connection.commit()
    #cursor.close()
    #connection.close()

    # Create the users table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            userid VARCHAR(15),
            mobile BIGINT,
            otp VARCHAR(15),
            otpexp TIMESTAMP NULL,
            UNIQUE (mobile, userid)
        );
    """)
    connection.commit()
    cursor.close()
    connection.close()

# Call the function to ensure the table is created
create_table_if_not_exists()

# Function to get a connection to the MariaDB database
def get_db_connection():
    return mysql.connector.connect(
        host="mariadb",  # Database service name in Docker Compose
        user="root",
        password=DB_PASSWORD,  # Use password from environment variables
        database="finance_tracker"
    )

# Function to save data to the database
def save_data_to_db(amount, transaction_type, category, description, username):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO transactions (amount, type, category, description, user) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, (amount, transaction_type, category, description, username))
    conn.commit()
    cursor.close()
    conn.close()

# Function to get Transactions
def get_transactions_by_period(start_date, end_date):
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()

    query = """
        SELECT amount, type, category, user, timestamp, description
        FROM transactions
        WHERE DATE(timestamp) BETWEEN %s AND %s
        ORDER BY timestamp ASC
    """
    cursor.execute(query, (start_date, end_date))
    result = cursor.fetchall()

    cursor.close()
    conn.close()
    return result

# Create admin user if not exists
def create_admin_account():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO users (userid, mobile, otp, otpexp) VALUES ('admin', '0', 'admin', NULL)"
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()
