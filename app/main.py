from fastapi import FastAPI, HTTPException
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
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}
# Local config 
# db_config = {
#     "host": os.getenv("DB_HOST"),
#     "user": os.getenv("DB_USER"),
#     "password": os.getenv("DB_PASSWORD"),
#     "port": os.getenv("DB_PORT"),
#     "database": os.getenv("DB_NAME"),
# }

def get_db_connection():
    return mysql.connector.connect(**db_config)

class User(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

# CREATE
@app.post("/users")
def create_user(user: User):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (user.name, user.email, user.password)
        )
        conn.commit()
        return {"message": F"User {user.name} created!"}

    except mysql.connector.Error as error:
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        cursor.close()
        conn.close()

#READ ALL
@app.get("/users")
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, name, email FROM users;")
        users = cursor.fetchall()
        return users

    except mysql.connector.Error as error:
        raise HTTPException(status_code=404, detail=str(error))

    finally:
        cursor.close()
        conn.close()

#READ ONE
@app.get("/users/{id}")
def get_user(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (id,))
        user = cursor.fetchone()
        if user is None:
            return {"Message": F"No user found with ID: {id}"}
        return user

    except mysql.connector.Error as error:
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        cursor.close()
        conn.close()

#UPDATE
@app.put("/users/{id}")
def update_user(id, user: User):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE users SET name=%s, email=%s, password=%s WHERE id = %s",
            (user.name, user.email, user.password, id))
        conn.commit()

        updatedUser = cursor.rowcount
        if updatedUser == 0:
            return {"message": F"No user found with id {id}"}
        return {"message": F"{updatedUser} user updated."}
    
    except mysql.connector.Error as error:
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        cursor.close()
        conn.close()


# Delete
@app.delete("/users/{id}")
def delete_user(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (id,))
        conn.commit()

        deletedUser = cursor.rowcount
        if deletedUser == 0:
            return {"message": F"No user found with id {id}."}
        return {"message": F"user #{id} deleted"}
    
    except mysql.connector.Error as error:
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        cursor.close()
        conn.close()

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