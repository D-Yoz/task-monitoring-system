from database import get_connection

conn = get_connection()
cursor = conn.cursor(dictionary=True)

cursor.execute("SELECT * FROM users")
users = cursor.fetchall()

for user in users:
    print(user)

cursor.close()
conn.close()
