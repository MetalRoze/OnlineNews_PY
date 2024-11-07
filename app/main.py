from fastapi import FastAPI
from app.my_code import my_function  # 실행하고 싶은 파이썬 코드

app = FastAPI()

@app.get("/run_code")
def run_code():
    result = my_function()  # 외부 파이썬 코드 실행
    return {"result": result}
