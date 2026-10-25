import psycopg
import psycopg_pool
from psycopg import sql
from consts import CREDENTIALS_PATH
import json
import atexit
import datetime

from logger import *

console = ConsoleLogger(True, "DB")

cred_data = {}
try:
    with open(CREDENTIALS_PATH, "r", encoding='utf-8') as f:
        cred_data = json.load(f)
except FileNotFoundError:
    cred_data = {
        "dbname": "aeterna",
        "postgres_user": "postgres",
        "postgres_password": "pkrsl"
    }
    with open(CREDENTIALS_PATH, "w", encoding='utf-8') as f:
        json.dump(cred_data, f)

dbname = "aeterna"
# print(cred_data)
global_conn_info = f"host=localhost dbname=postgres user={cred_data["postgres_user"]} password={cred_data["postgres_password"]}"

class DatabaseManager:
    def __init__(self):
        self.conn_info = f"host=localhost dbname={dbname} user={cred_data["postgres_user"]} password={cred_data["postgres_password"]}"
        self.pool: psycopg_pool.ConnectionPool | None = None
        self.userlist: set[str] = set()
        self._open = False

    # Database initialization logic
    # This function will checks existence of required databases and servers
    def initdb(self):
        console.log("Initializing database manager")
        # Making sure the database exists
        with psycopg.connect(global_conn_info) as conn:
            console.log("Making sure database and user exists")
            with conn.cursor() as cur:
                # Query the system catalog for the database name
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (dbname,))
                
                # If fetchone() returns data, the database exists
                db_exists = cur.fetchone() is not None

        if not db_exists:
            # Database doesn't exist. Open a separate session with autocommit to create database
            console.logwarn("Database does not exist. Creating")
            with psycopg.connect(global_conn_info) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
                    console.logok(f"Database '{dbname}' created successfully!")

        missing_tables = False
        with psycopg.connect(self.conn_info) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_tables WHERE schemaname = %s AND tablename = %s", ("public", "users"))

                if cur.fetchone() is None:
                    console.logwarn("User table does not exist. Creating")
                    # Creating a users table. Each user has:
                    # - Username (string, 50 chars max, not empty, not duplicate)
                    # - Password hash (bytes, not empty) // bcrypt hash
                    # - Biography/Description (text)
                    # - Gender (bool, default false, not empty) // 0: male, 1: female
                    # - Created date (timestamp with time zone, defaults to current time)
                    # - Birthday (timestamp with time zone, defaults to NULL)
                    cur.execute("""--sql
                        CREATE TABLE users (
                            username VARCHAR(50) NOT NULL UNIQUE,
                            realname VARCHAR(100) NOT NULL,
                            password_hash BYTEA NOT NULL,
                            bio VARCHAR(500) DEFAULT '' NOT NULL,
                            gender BOOL DEFAULT FALSE NOT NULL,
                            created TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                            birthday TIMESTAMPTZ DEFAULT NULL,
                            linked_docs JSONB DEFAULT '[]'::jsonb
                        )
                    """)
                    missing_tables = True


                # Add some other stuffs
                users_data = cur.execute("SELECT username FROM users").fetchall()
                for user in users_data:
                    self.userlist.add(user[0])
        
            conn.commit()
            if missing_tables: console.logok("Added missing tables")

        self.pool = psycopg_pool.ConnectionPool(self.conn_info, min_size=2, max_size=20, open=False)
        self.pool.open()
        self._open = True

        # Hook close
        self.pool.wait()
        atexit.register(self.close)

    def close(self):
        assert self.pool is not None
        if self._open:
            self._open = False
            self.pool.close()

    def execute_one(self, query: sql.SQL):
        assert self.pool is not None
        with self.pool.connection() as conn:
            return conn.execute(query).fetchone()

    def execute_all(self, query: sql.SQL):
        assert self.pool is not None
        with self.pool.connection() as conn:
            return conn.execute(query).fetchall()

    def add_user(self, username: str, password_hash: bytes):
        assert self.pool is not None
        with self.pool.connection() as conn:
            conn.execute("INSERT INTO users (username, realname, password_hash) VALUES (%s, %s, %s)", (username, username, password_hash))
            conn.commit()

        self.userlist.add(username)

    def modify_user(self, username: str, realname: str = "", bio: str = "", gender: bool = False, birthday: datetime.datetime | None = None):
        assert self.pool is not None
        with self.pool.connection() as conn:
            if realname == "": realname = username
            conn.execute("""--sql
                UPDATE users SET realname = %s, bio = %s, gender = %s, birthday = %s WHERE username = %s
            """, (realname, bio, gender, birthday, username))
            conn.commit()

    def change_user_passwd(self, username: str, password_hash: bytes):
        assert self.pool is not None
        with self.pool.connection() as conn:
            conn.execute("UPDATE users SET password_hash = %s WHERE username = %s", (password_hash, username))
            conn.commit()

    def delete_user(self, username: str):
        assert self.pool is not None
        with self.pool.connection() as conn:
            conn.execute("DELETE FROM users WHERE username = %s", (username, ))
            conn.commit()

        self.userlist.discard(username)

    def get_user_password_hash(self, username: str) -> bytes:
        assert self.pool is not None
        with self.pool.connection() as conn:
            data = conn.execute("SELECT password_hash FROM users WHERE username = %s", (username, )).fetchone()
            assert data is not None
            return data[0]

    def get_user_data(self, username: str) -> tuple:
        """`realname, bio, gender, created, birthday, linked_docs`"""
        assert self.pool is not None
        with self.pool.connection() as conn:
            data = conn.execute("SELECT realname, bio, gender, created, birthday, linked_docs FROM users WHERE username = %s", (username, )).fetchone()
            assert data is not None
            return data

    def user_exists(self, username: str) -> bool:
        return username in self.userlist