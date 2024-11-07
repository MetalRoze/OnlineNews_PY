# app/main.py
from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

app = FastAPI()

# favicon.ico 파일을 제공할 경로 설정
@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join("app", "static", "favicon.ico"))

@app.get("/")
def read_root():
    return {"message": "Welcome to the root endpoint!"}
