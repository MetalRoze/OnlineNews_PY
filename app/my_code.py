import requests
from .extract import TextRank, RawTagger
import logging
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jwt
import time

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

def cal_similarity(token):
    try:
        logging.info(f"Access token used for request: {token}")

        # 토큰 유효성 검사
        if not is_token_valid(token):
            logging.info("Access token expired. Attempting to reissue...")
            _, refresh_token = get_token()
            token = reissue_token(refresh_token)  # 새 accessToken 발급

        # 전체 기사 키워드 가져오기
        ARTICLE_KEYWORD_URL = "http://3.35.255.194:8080/api/article/keywords"
        response = requests.get(ARTICLE_KEYWORD_URL)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch article keywords. Status code: {response.status_code}")

        article_keywords = response.json()

        # 사용자 키워드 가져오기
        USER_KEYWORD_URL = "http://3.35.255.194:8080/api/user/keywords"
        headers = {"Authorization": f"Bearer {token}"}

        keywords_response = requests.get(USER_KEYWORD_URL, headers=headers)

        if keywords_response.status_code == 200:
            user_keywords = keywords_response.json()
            logging.info(f"User keywords response: {user_keywords}")  # 응답 출력

            # 리스트 형식으로 직접 사용
            if isinstance(user_keywords, list):
                user_keywords_list = user_keywords
            else:
                raise Exception("User keywords response is not a list")

            return rank_articles_by_similarity(article_keywords, user_keywords_list)
        else:
            raise Exception(f"Failed to fetch user keywords. Status code: {keywords_response.status_code}")

    except Exception as e:
        logging.error(f"Error in cal_similarity: {e}")
        raise


    
    
def rank_articles_by_similarity(article_keywords, user_keywords_list):
    user_keywords_str = " ".join(user_keywords_list)
    similarities = {}
    
    for article_id, keywords in article_keywords.items():
        article_keywords_str = " ".join(keywords)
        texts = [user_keywords_str, article_keywords_str]
        
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        similarities[article_id] = sim[0][0]
    
    sorted_article_ids = sorted(similarities, key=similarities.get, reverse=True)
    return sorted_article_ids


    
def get_token():
    LOGIN_URL = "http://3.35.255.194:8080/api/user/login"
    login_payload = {
        "email" : "aaa@gmail.com",
        "password" : "asdf"
    }
    headers = {
        "Content-Type": "application/json" 
    }
    
    login_response = requests.post(LOGIN_URL, json = login_payload, headers = headers)
    
    if login_response.status_code == 200:
        tokens = login_response.json()
        access_token = tokens.get("accessToken")
        refresh_token = tokens.get("refreshToken")  # 리프레시 토큰도 저장

        return access_token, refresh_token

    else:
        logging.error(f"Failed to login. Status code: {login_response.status_code}, Response: {login_response.text}")
        raise Exception("Failed to login")

    
    
#토큰 만료 시    
def reissue_token(refresh_token):
    """
    리프레시 토큰을 사용하여 새 액세스 토큰을 재발급받습니다.
    """
    try:
        REISSUE_URL = "http://3.35.255.194:8080/api/token/reissue"
        
        # 요청 본문에 리프레시 토큰을 "json" 형태로 전달
        response = requests.post(REISSUE_URL, json={"refreshToken": refresh_token}, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            # 새 access token 반환
            new_access_token = response.json().get("accessToken")
            if not new_access_token:
                raise Exception("Missing accessToken in response")
            logging.info(f"Reissued Token: {new_access_token}")
            return new_access_token
        else:
            logging.error(f"Failed to reissue token. Status: {response.status_code}, Response: {response.text}")
            raise Exception(f"Failed to reissue token: {response.status_code}")
    except Exception as e:
        logging.error(f"Error in reissue_token: {e}")
        raise



import base64

def decode_token(token):
    try:
        # 토큰을 bytes 형식으로 변환
        token_bytes = token.encode('utf-8')
        
        decoded = jwt.decode(token_bytes, options={"verify_signature": False})
        logging.info(f"Decoded Token: {decoded}")
        return decoded
    except Exception as e:
        logging.error(f"Error decoding token: {e}")
        raise


def is_token_valid(token):
    """
    토큰 유효성 검사
    """
    try:
        # Ensure the token is a string
        if isinstance(token, bytes):
            token = token.decode("utf-8")  # Convert bytes to string
        
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_time = decoded.get("exp")  # 만료 시간
        current_time = int(time.time())
        return current_time < exp_time
    except Exception as e:
        logging.error(f"Error decoding token: {e}")
        return False
