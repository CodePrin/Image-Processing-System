import sqlite3

conn = sqlite3.connect('image_data.db')
cursor = conn.cursor()

# Check requests
cursor.execute("SELECT * FROM requests")
print(cursor.fetchall())

# Check products
cursor.execute("SELECT * FROM products")
print(cursor.fetchall())

conn.close()