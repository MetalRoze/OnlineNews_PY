import requests
from .extract import TextRank, RawTagger
import logging
import random

# def my_function():
#     # 여기서 원하는 코드 로직을 실행
#     return "Hello from Python!"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_article(article_id):
    url = f"http://3.35.255.194:8080/api/article/select?id={article_id}"
    response = requests.get(url)

    logging.info(f"응답 상태 코드: {response.status_code}")

    if response.status_code == 200:
        article_data = response.json()
        # logging.info(f"응답 데이터: {article_data}")
        if isinstance(article_data, list) and article_data:
            logging.info(article_data[0].get("content"))
            return article_data[0].get("content")
        else:
            raise Exception("No content found in the article data.")
    else:
        raise Exception("Failed to fetch article")


def save_keywords(article_id, keywords):
    logging.info(keywords)
    url = f"http://3.35.255.194:8080/api/article/{article_id}/keywords"
    payload = {
        "articleId": article_id,
        "keyword": keywords  # 'keyword'로 변경
    }
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        logging.info("키워드 저장 성공")
    else:
        logging.error(f"응답 상태 코드: {response.status_code}, 응답 데이터: {response.text}")
        raise Exception("Failed to save keywords")


def process_article(article_id):
    # 1. 기사 내용 가져오기
    article_content = get_article(article_id)

    # 2. TextRank를 사용해 키워드 추출
    tr = TextRank(window=5, coef=1)
    stopword = set([('있', 'VV'), ('하', 'VV'), ('되', 'VV'), ('없', 'VV')])
    tr.load(RawTagger(article_content), lambda w: w not in stopword and (w[1] in ('NNG', 'NNP', 'VV', 'VA')))
    tr.build()
    keywords = tr.extract(0.1)
    
    if len(keywords) > 3:
        keywords = random.sample(keywords, 3)

    # 3. 키워드 저장
    save_keywords(article_id, keywords)

    # 4. 결과 반환
    return keywords