import mysql.connector
from mysql.connector import Error

# Database configuration
db_config = {
    'host': '127.0.0.1',  # Update with your database host
    'user': 'root',  # Update with your MySQL username
    'password': 'Vaibhav@2504',  # Update with your MySQL password
    'database': 'newdata',  # Update with your database name
}

# Sample data
data = {
    "01": {
        "name": "Vaibhav Gupta",
        "major": "AI",
        "starting_year": 2024,
        "total_attendance": 1,
        "year": 2,
        "last_attendance_time": "2024-12-11 00:54:34",
    },
    "02": {
        "name": "Suryansh Kumar",
        "major": "Web Dev",
        "starting_year": 2024,
        "total_attendance": 1,
        "year": 2,
        "last_attendance_time": "2024-12-11 00:54:34",
    },
    "03": {
        "name": "Praveen Chaudhary",
        "major": "Cyber",
        "starting_year": 2024,
        "total_attendance": 1,
        "year": 2,
        "last_attendance_time": "2024-12-11 00:54:34",
    },
    "04": {
        "name": "Nandini Porwal",
        "major": "Business",
        "starting_year": 2024,
        "total_attendance": 1,
        "year": 2,
        "last_attendance_time": "2024-12-11 00:54:34",
    },
    "05": {
        "name": "Vansh Tiwari",
        "major": "CSE",
        "starting_year": 2024,
        "total_attendance": 1,
        "year": 2,
        "last_attendance_time": "2024-12-11 00:54:34",
    },
}

# Establish database connection
try:
    connection = mysql.connector.connect(**db_config)
    if connection.is_connected():
        print("Connected to MySQL database")
        cursor = connection.cursor()

        # Ensure table exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Students (
            id VARCHAR(10) PRIMARY KEY,
            name VARCHAR(100),
            major VARCHAR(100),
            starting_year INT,
            total_attendance INT,
            year INT,
            last_attendance_time DATETIME
        )
        """)

        # Insert data into the table
        for key, value in data.items():
            cursor.execute(
                """
                INSERT INTO Students (id, name, major, starting_year, total_attendance, year, last_attendance_time)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    major = VALUES(major),
                    starting_year = VALUES(starting_year),
                    total_attendance = VALUES(total_attendance),
                    year = VALUES(year),
                    last_attendance_time = NOW()
                """,
                (
                    key,
                    value["name"],
                    value["major"],
                    value["starting_year"],
                    value["total_attendance"],
                    value["year"],
                ),
            )
        # Commit the changes
        connection.commit()
        print("Data inserted successfully")

except Error as e:
    print(f"Error: {e}")

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection closed")