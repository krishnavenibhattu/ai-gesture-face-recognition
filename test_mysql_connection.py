import mysql.connector
from mysql.connector import Error

try:
    connection = mysql.connector.connect(
        host='127.0.0.1',     # or 'localhost'
        user='root',
        password='Vaibhav@2504',
        database='newdata'
    )

    if connection.is_connected():
        print("✅ Connected to MySQL!")
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES;")
        for table in cursor.fetchall():
            print(table)

except Error as e:
    print("❌ Error while connecting:", e)

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("🔌 Connection closed.")
