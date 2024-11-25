# app/main.py
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.my_code import process_article
import os
import uvicorn

app = FastAPI()

origins = [
        "http://myeongbo.site",
]

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처
    allow_credentials=True,  # 쿠키 허용 여부
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)


# favicon.ico 파일을 제공할 경로 설정
@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join("app", "static", "favicon.ico"))

@app.get("/")
def read_root():
    return {"message": "Welcome to the root endpoint!"}

@app.put("/userlike")
def user():
    return {"hi!"}


@app.get("/run-my-code/{article_id}")
def run_my_code(article_id: int):
    try:
        result = process_article(article_id)  # my_code.py의 process_article 함수 호출
        return {"keywords": result}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
    

