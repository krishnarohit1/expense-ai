import sqlite3
conn = sqlite3.connect('expense_ai.db')
cur = conn.cursor()
print('Expenses rows:')
for row in cur.execute('SELECT id, user_id, amount, merchant, date FROM expenses'):
    print(row)
print('\nUsers rows:')
for row in cur.execute('SELECT id, email, name FROM users'):
    print(row)
conn.close()
