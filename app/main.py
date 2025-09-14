from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import mysql.connector
from dotenv import load_dotenv
import os
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
# Docker config
# db_config = {
#     "host": os.getenv("DB_HOST"),
#     "user": os.getenv("DB_USER"),
#     "password": os.getenv("DB_PASSWORD"),
#     "database": os.getenv("DB_NAME")
# }
# Local config 
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME")
}
def get_db_connection():
    return mysql.connector.connect(**db_config)

class User(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

# CREATE
@app.post("/users")
def create_user(user: User):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
        (user.name, user.email, user.password)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return {"message": F"User {user.name} created!"}

#READ ALL
@app.get("/users")
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, email FROM users;")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    
    if rows is None:
        return {"message": "No users found."}
    return rows

#READ ONE
@app.get("/users/{id}")
def get_user(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (id,))
    rows = cursor.fetchone()

    cursor.close()
    conn.close()

    if rows is None:
        return {"message": F"No user found with id {id}."}
    return rows

#UPDATE
@app.put("/users/{id}")
def update_user(id, user: User):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "UPDATE users SET name=%s, email=%s, password=%s WHERE id = %s",
        (user.name, user.email, user.password, id))
    conn.commit()

    rows = cursor.rowcount

    cursor.close()
    conn.close()
    if rows is None:
        return {"message": F"No user found with id {id}."}
    return {"message": F"{rows} user updated."}

# Delete
@app.delete("/users/{id}")
def delete_user(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("DELETE FROM users WHERE id = %s", (id))
    conn.commit()

    rows = cursor.rowcount

    cursor.close()
    conn.close()

    if rows is None:
        return {"message": F"No user found with id {id}."}
    return {"message": F"user #{id} deleted"}

# If table doesnt exist, create it on startup
def create_db_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(100) NOT NULL
        );
    """)
    conn.commit()

    cursor.close()
    conn.close()

create_db_table()