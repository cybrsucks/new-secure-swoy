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
        security_qns TEXT NOT NULL,
        security_ans TEXT NOT NULL,
        admin INTEGER NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS comments(
        comment_id INTEGER PRIMARY KEY,
        content TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        drink_id INTEGER NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS cart(
        user_id INTEGER PRIMARY KEY,
        cart_items TEXT DEFAULT '[]')""")

    cursor.execute("INSERT INTO user(username, email, password, security_qns, security_ans, admin) "
                   "VALUES('testing', 'test@test.com', 'testtest', 'What is the name of your favourite teacher?', 'Ms Tan', 0)")
    cursor.execute("INSERT INTO user(username, email, password, security_qns, security_ans, admin) "
                   "VALUES('Super Admin', 'superadmin@swoy.com', 'admin', 'What is the name of your favourite teacher?', 'Ms Tan', 1)")
    cursor.execute("INSERT INTO user(username, email, password, security_qns, security_ans, admin) "
                   "VALUES('John Doe', 'johndoe@gmail.com', '12345678', 'What is the name of your favourite teacher?', 'Ms Tan', 0)")

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
