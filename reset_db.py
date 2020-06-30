# Please delete existing swoy.db before executing this .py file

import sqlite3


with sqlite3.connect("swoy.db") as conn:
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS drinks(
        drink_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        thumbnail TEXT NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS user(
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        admin INTEGER NOT NULL)""")

    cursor.execute("INSERT INTO user(username, email, password, admin) "
                   "VALUES('testing', 'test@test.com', 'testtest', False)")
    cursor.execute("INSERT INTO user(username, email, password, admin) "
                   "VALUES('Super Admin', 'superadmin@swoy.com', 'swoyadmin', True)")
    cursor.execute("INSERT INTO user(username, email, password, admin) "
                   "VALUES('John Doe', 'johndoe@gmail.com', '12345678', False)")

    cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
                   "VALUES('Chocolate Milk', 5, 'Chocolate Boba.jpeg')")
    cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
                   "VALUES('Earl Grey Tea', 4, 'Earl Grey Boba.jpeg')")
    cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
                   "VALUES('Green Tea', 4, 'Green Tea Boba.jpg')")
    cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
                   "VALUES('Mango', 5, 'Mango Boba.jpg')")
    cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
                   "VALUES('Passionfruit', 5, 'Passionfruit Boba.jpg')")
    cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
                   "VALUES('Strawberry Milk', 5, 'Strawberry Boba.jpeg')")

    cursor.execute("SELECT * FROM user")
    print(f"User table : {cursor.fetchall()}")
    cursor.execute("SELECT * FROM drinks")
    print(f"Drinks table : {cursor.fetchall()}")
    conn.commit()
