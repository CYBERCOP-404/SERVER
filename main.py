from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import jwt
import datetime
import os

SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")
ALGORITHM = "HS256"

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

users_db = {
    "NAHIDUL": {
        "username": "NAHIDUL",
        "password": "51535759"
    }
}

sheet_data = []

class LoginData(BaseModel):
    username: str
    password: str

class SheetItem(BaseModel):
    title: str
    content: str

def create_token(username: str):
    payload = {
        "sub": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/login")
def login(data: LoginData):
    user = users_db.get(data.username)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Wrong login")
    token = create_token(data.username)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/sheet/add")
def add_sheet(item: SheetItem, user: str = Depends(get_current_user)):
    sheet_data.append({
        "user": user,
        "title": item.title,
        "content": item.content
    })
    return {"message": "Data added"}

@app.get("/sheet/all")
def get_all(user: str = Depends(get_current_user)):
    return [i for i in sheet_data if i["user"] == user]
