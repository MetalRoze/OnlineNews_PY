# app/main.py
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.my_code import process_article
import os
import uvicorn
from app.my_code import get_token,cal_similarity
import logging
import requests

app = FastAPI()

origins = [
        "http://myeongbo.site",
        "http://localhost:5173",  # 로컬 개발 환경
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


@app.get("/pyapi/run-my-code/{article_id}")
def run_my_code(article_id: int):
    try:
        result = process_article(article_id)  # my_code.py의 process_article 함수 호출
        return {"keywords": result}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/pyapi/calculate/{token}")
def calculate(token: str):
    try:
        logging.info(f"Received token: {token}")

        # 코사인 유사도 계산
        similarity_result = cal_similarity(token)

        return {"status": "success", "data": similarity_result}

    except ValueError as ve:
        logging.error(f"Validation error: {ve}")
        return Response(
            content=f'{{"status": "error", "message": "{str(ve)}"}}',
            status_code=400,
            media_type="application/json"
        )

    except requests.RequestException as re:
        logging.error(f"Request error: {re}")
        return Response(
            content='{"status": "error", "message": "Failed to communicate with external API."}',
            status_code=502,
            media_type="application/json"
        )

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return Response(
            content='{"status": "error", "message": "Internal server error."}',
            status_code=500,
            media_type="application/json"
        )



if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
    

