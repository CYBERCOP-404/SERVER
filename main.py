from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List
from jose import jwt, JWTError
from passlib.context import CryptContext
import sqlite3
import datetime
import os

# ----------------------------
# Config
# ----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")
ALGORITHM = "HS256"

DB_FILE = "database.db"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI(title="NAHIDUL Sheet API (Database Version)")

# ----------------------------
# Models
# ----------------------------
class RegisterData(BaseModel):
    username: str
    password: str

class LoginData(BaseModel):
    username: str
    password: str

class SheetItem(BaseModel):
    title: str
    content: str

# ----------------------------
# Database helper
# ----------------------------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    # Sheets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ----------------------------
# Auth helpers
# ----------------------------
def create_token(user_id: int):
    payload = {
        "sub": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ----------------------------
# API Routes
# ----------------------------

# Register new user
@app.post("/register")
def register(data: RegisterData):
    hashed_password = pwd_context.hash(data.password)
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                       (data.username, hashed_password))
        conn.commit()
        return {"message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

# Login
@app.post("/login")
def login(data: LoginData):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username = ?", (data.username,))
    row = cursor.fetchone()
    conn.close()
    if row is None or not pwd_context.verify(data.password, row["password"]):
        raise HTTPException(status_code=401, detail="Wrong login")
    token = create_token(row["id"])
    return {"access_token": token, "token_type": "bearer"}

# Add sheet
@app.post("/sheet/add")
def add_sheet(item: SheetItem, user_id: int = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sheets (user_id, title, content) VALUES (?, ?, ?)",
                   (user_id, item.title, item.content))
    conn.commit()
    conn.close()
    return {"message": "Sheet added"}

# Get all sheets for current user
@app.get("/sheet/all", response_model=List[SheetItem])
def get_all(user_id: int = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT title, content FROM sheets WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"title": r["title"], "content": r["content"]} for r in rows]
