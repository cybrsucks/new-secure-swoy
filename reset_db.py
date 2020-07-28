# Please delete existing swoy.db before executing this .py file

import sqlite3


with sqlite3.connect("swoy.db") as conn:
    cursor = conn.cursor()
    # cursor.execute("""CREATE TABLE IF NOT EXISTS drinks(
    #     drink_id INTEGER PRIMARY KEY,
    #     name TEXT NOT NULL,
    #     price REAL NOT NULL,
    #     thumbnail TEXT NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS user(
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        admin INTEGER NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS comments(
        comment_id INTEGER PRIMARY KEY,
        content TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        drink_id INTEGER NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS cart(
        user_id INTEGER PRIMARY KEY,
        cart_items TEXT DEFAULT '[]')""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS delivery_order(
        order_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        address TEXT NOT NULL,
        delivery_date TEXT NOT NULL,
        delivery_time TEXT NOT NULL,
        order_items TEXT NOT NULL,
        delivered INTEGER DEFAULT 0)""")

    # Passwords:
    # testing: Password!1
    # Super Admin: $uperAdm1n
    # John Doe: Password!2
    cursor.execute("INSERT INTO user(username, email, password, admin) "
                   "VALUES('testing', 'test@test.com', 'be6fded9eba153d774245490f8f4120cebe2a6d3a5467603eca3343de90d6275', 0)")
    cursor.execute("INSERT INTO user(username, email, password, admin) "
                   "VALUES('Super Admin', 'superadmin@swoy.com', '9c9b477f56f1ed5fc4b1d857e11f86664be481e9e7ea5555916448dd72c649ff', 1)")
    cursor.execute("INSERT INTO user(username, email, password, admin) "
                   "VALUES('John Doe', 'johndoe@gmail.com', '7ab048ba3931ced4c81ddc169a632642b38dbc3701ab5b9e616ad83a0eedbcb1', 0)")

    # cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
    #                "VALUES('Chocolate Milk', 5, 'Chocolate Boba.jpeg')")
    # cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
    #                "VALUES('Earl Grey Tea', 4, 'Earl Grey Boba.jpeg')")
    # cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
    #                "VALUES('Green Tea', 4, 'Green Tea Boba.jpg')")
    # cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
    #                "VALUES('Mango', 5, 'Mango Boba.jpg')")
    # cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
    #                "VALUES('Passionfruit', 5, 'Passionfruit Boba.jpg')")
    # cursor.execute("INSERT INTO drinks(name, price, thumbnail)"
    #                "VALUES('Strawberry Milk', 5, 'Strawberry Boba.jpeg')")

    cursor.execute("INSERT INTO comments(content, user_id, drink_id)"
                   "VALUES ('I love it!', 3, 1)")
    cursor.execute("INSERT INTO comments(content, user_id, drink_id)"
                   "VALUES ('This is our special!', 2, 1)")
    cursor.execute("INSERT INTO comments(content, user_id, drink_id)"
                   "VALUES ('Classic taste!', 1, 2)")
    cursor.execute("INSERT INTO comments(content, user_id, drink_id)"
                   "VALUES ('Pretty bland.. disappointed :(', 3, 2)")

    cursor.execute("SELECT * FROM user")
    print(f"User table : {cursor.fetchall()}")
    # cursor.execute("SELECT * FROM drinks")
    # print(f"Drinks table : {cursor.fetchall()}")
    cursor.execute("SELECT * FROM comments")
    print(f"Comments table : {cursor.fetchall()}")
    conn.commit()
