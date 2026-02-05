from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
import jwt
import datetime
import os

# Secret key
SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")
ALGORITHM = "HS256"

app = FastAPI(title="NAHIDUL Sheet API")

# Users DB (learning phase)
users_db = {
    "NAHIDUL": {
        "username": "NAHIDUL",
        "password": "51535759"
    }
}

sheet_data = []

# Schemas
class LoginData(BaseModel):
    username: str
    password: str

class SheetItem(BaseModel):
    title: str
    content: str

# Create JWT token
def create_token(username: str):
    payload = {
        "sub": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Get current user from token
def get_current_user(authorization: str = Header(...)):
    try:
        # Expect header: Authorization: Bearer <token>
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token header")
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# Login route
@app.post("/login")
def login(data: LoginData):
    user = users_db.get(data.username)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Wrong login")
    token = create_token(data.username)
    return {"access_token": token, "token_type": "bearer"}

# Add sheet
@app.post("/sheet/add")
def add_sheet(item: SheetItem, user: str = Depends(get_current_user)):
    sheet_data.append({
        "user": user,
        "title": item.title,
        "content": item.content
    })
    return {"message": "Data added"}

# Get all sheets for current user
@app.get("/sheet/all")
def get_all(user: str = Depends(get_current_user)):
    return [i for i in sheet_data if i["user"] == user]
