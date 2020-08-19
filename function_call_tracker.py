import sqlite3
import datetime


def create_call_db():

    with sqlite3.connect("function_call.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS functions(
            function_id INTEGER PRIMARY KEY,
            function_name TEXT NOT NULL,
            call_count INTEGER NOT NULL,
            call_daily_limit INTEGER NOT NULL,
            last_called TEXT NULL)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS user_call(
            user_id INTEGER NOT NULL,
            function_id INTEGER NOT NULL,
            call_count INTEGER NOT NULL,
            last_called TEXT NULL)""")

        # Global functions (all accounts share the same call_count and last_called)
        cursor.execute("INSERT INTO functions(function_name, call_count, call_daily_limit) "
                       "VALUES('Delete drink', 0, 3)")
        cursor.execute("INSERT INTO functions(function_name, call_count, call_daily_limit) "
                       "VALUES('Delete topping', 0, 3)")
        cursor.execute("INSERT INTO functions(function_name, call_count, call_daily_limit) "
                       "VALUES('Delete admin', 0, 2)")

        # Local functions (all accounts use their own call_count and last_called)
        cursor.execute("INSERT INTO functions(function_name, call_count, call_daily_limit) "
                       "VALUES('Add comment', 0, 5)")
        cursor.execute("INSERT INTO functions(function_name, call_count, call_daily_limit) "
                       "VALUES('Add order', 0, 5)")
        cursor.execute("INSERT INTO functions(function_name, call_count, call_daily_limit) "
                       "VALUES('Change username', 0, 2)")
        cursor.execute("INSERT INTO functions(function_name, call_count, call_daily_limit) "
                       "VALUES('Change password', 0, 2)")

        conn.commit()

        cursor.execute("SELECT * FROM functions")
        print(cursor.fetchall())


def function_call(func_id, user_id=None):

    with sqlite3.connect("function_call.db") as conn:
        cursor = conn.cursor()

        if user_id is None:  # Global
            cursor.execute("SELECT * FROM functions WHERE function_id = ?", (func_id,))
            function = cursor.fetchone()  # [id, name, call_count, limit, last_called]
            time_called = datetime.datetime.now()
            if function[4] is not None:
                last_called = datetime.datetime.strptime(function[4], '%Y-%m-%d %H:%M:%S.%f')
                difference = time_called - last_called
                if difference.days >= 1:
                    call_count = 1
                else:
                    call_count = function[2] + 1
            else:
                call_count = 1

            if call_count > function[3]:
                limit_reached = True
            else:
                limit_reached = False

            if not limit_reached:
                cursor.execute("UPDATE functions SET call_count = ?, last_called = ? WHERE function_id = ?",
                               (call_count, time_called, func_id))

        else:  # Local
            cursor.execute("SELECT * FROM user_call WHERE user_id = ? and function_id = ?", (user_id, func_id))
            user_call = cursor.fetchone()  # [user_id, func_id, call_count, last_called]

            if user_call:
                cursor.execute("SELECT * FROM functions WHERE function_id = ?", (func_id,))
                function = cursor.fetchone()  # [id, name, call_count, limit, last_called]
                time_called = datetime.datetime.now()
                if user_call[3] is not None:
                    last_called = datetime.datetime.strptime(user_call[3], '%Y-%m-%d %H:%M:%S.%f')
                    difference = time_called - last_called
                    if difference.days >= 1:
                        call_count = 1
                    else:
                        call_count = user_call[2] + 1
                else:
                    call_count = 1

                if call_count > function[3]:
                    limit_reached = True
                else:
                    limit_reached = False

                if not limit_reached:
                    cursor.execute("UPDATE user_call SET call_count = ?, last_called = ? WHERE function_id = ? AND user_id = ?",
                                   (call_count, time_called, func_id, user_id))
            else:
                limit_reached = False
                time_called = datetime.datetime.now()
                cursor.execute("INSERT INTO user_call VALUES(?, ?, 1, ?)", (user_id, func_id, time_called))

        conn.commit()

        return limit_reached


def test1():
    with sqlite3.connect("function_call.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM functions")
        print(cursor.fetchall())


def test2():
    with sqlite3.connect("function_call.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM functions WHERE function_id = 7")
        print(cursor.fetchall())
        cursor.execute("SELECT * FROM user_call WHERE function_id = 7")
        print(cursor.fetchall())


if __name__ == "__main__":
    create_call_db()
    # test1()
    # test2()
    pass
