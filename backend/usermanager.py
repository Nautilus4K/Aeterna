# Local user data viewer and modifier
from db import DatabaseManager
from psycopg import sql
import psycopg
import getpass
import bcrypt
import prettytable
from utils import authenticate_user

db = DatabaseManager()
db.initdb()

if __name__ == "__main__":
    while True:
        data = db.execute_all(sql.SQL("SELECT * FROM users"))
        # print(data)

        table = prettytable.PrettyTable()
        table.field_names = ["username", "password_hash", "bio", "gender", "created", "birthday"]
        for row in data:
            formatted_row = list(row)
            formatted_row[1] = formatted_row[1].decode('utf-8')
            # if len(formatted_row[1]) > 15: formatted_row[1] = formatted_row[1][:13] + "..."
            if len(formatted_row[2]) > 15: formatted_row[2] = formatted_row[2][:13] + "..."

            formatted_row[3] = "F" if formatted_row[3] else "M"

            table.add_row(formatted_row)

        print(table)

        action = str(input("[A]dd, [M]odify, [D]elete, [I]nspect, [C]heck, E[X]it: ")).lower()

        if action == "x":
            break
        elif action == "a":
            username = str(input("New username: "))
            password = getpass.getpass("Password: ")
            confirm_password = getpass.getpass("Confirm Password: ")
            if confirm_password != password:
                continue

            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            print("> Hashed: " + hashed.decode('utf-8'))

            try:
                db.add_user(username, hashed)
            except psycopg.errors.UniqueViolation:
                print("/// FAIL ///  UNIQUE VIOLATION  /// FAIL ///")
        elif action == "m":
            username = str(input("Target username: "))
            password = getpass.getpass("New Password: ")
            if password != "":
                confirm_password = getpass.getpass("Confirm Password: ")
                if confirm_password != password:
                    continue

                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
                print("> Hashed: " + hashed.decode('utf-8'))

                db.change_user_passwd(username, hashed)
            else:
                bio = str(input("Bio: "))
                gender = (str(input("Gender: [M]ale, [F]emale: ")) == "F")

                db.modify_user(username, bio, gender)
        elif action == "d":
            username = str(input("Target username: "))
            db.delete_user(username)
        elif action == "i":
            username = str(input("Target username: "))
            password = db.get_user_password_hash(username)
            data = db.get_user_data(username)

            print("> Password:", password.decode('utf-8'))
            print("> Bio:", data[0])
            print("> Gender:", "F" if data[1] else "M")
            print("> Created:", data[2])
            print("> Birthday:", data[3])

            input("Enter to continue...")
        elif action == "c":
            username = str(input("Username: "))
            password = getpass.getpass("Password: ")

            print("OK" if authenticate_user(db, username, password) else "FAIL")
