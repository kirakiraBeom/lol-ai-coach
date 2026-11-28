import os
import httpx 

from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote
from database import (
    initialize_database,
    get_cached_match,
    save_match,
    get_cached_timeline,
    save_timeline
)

# 환경 변수 설정
load_dotenv(Path(__file__).with_name(".env"))

API_KEY = os.getenv("RIOT_API_KEY")
REGION = os.getenv("RIOT_REGION", "kr")
ROUTING = os.getenv("RIOT_ROUTING", "asia")

# 공통 API 요청 함수
def request_api(url, params=None): # DRY(Dont Repeat Yourself) 원칙 적용 : 반복되는 코드를 함수로 묶어 재사용
    
    if not API_KEY:
        raise ValueError("RIOT_API_KEY가 설정되지 않았습니다.")

    headers = {
        "X-Riot-Token": API_KEY
    }
    response = httpx.get(
        url,
        headers=headers,
        params=params,
        timeout=10.0
    )

    response.raise_for_status()  # 요청 실패 시 예외 발생

    return response.json()

# 1. 라이엇 계정 조회
def get_account(game_name, tag):

    url = (
        f"https://{ROUTING}.api.riotgames.com"
        f"/riot/account/v1/accounts/by-riot-id"
        f"/{quote(game_name, safe='')}"
        f"/{quote(tag, safe='')}"
    )

    return request_api(url)

# 2. 랭크 정보 조회
def get_rank(puuid):

    url = (
        f"https://{REGION}.api.riotgames.com"
        f"/lol/league/v4/entries/by-puuid/{puuid}"
    )

    return request_api(url)

# 3. 최근 경기 ID 목록 조회
def get_match_ids(puuid, count=20):

    url = (
        f"https://{ROUTING}.api.riotgames.com"
        f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
    )

    params = {
        "start": 0,
        "count": count,
        "queue": "420"  # 솔로 랭크 게임만 조회
    }

    return request_api(url, params)

# 4. 경기 상세 정보 조회
def get_match_detail(match_id, use_cache=True):

    initialize_database()

    # 1. 캐시 데이터 조회
    if use_cache:

        cached_data = get_cached_match(match_id)

        if cached_data is not None:

            print (f"[CACHE HIT] Match: {match_id}")

            return cached_data

    # 2. API 요청
    print(f"[API REQUEST] Match: {match_id}")

    url = (
        f"https://{ROUTING}.api.riotgames.com"
        f"/lol/match/v5/matches/{match_id}"
    )

    data = request_api(url)

    # 3. 데이터베이스 저장
    save_match(match_id, data)

    # 4. 경기 데이터 반환
    return data

# 5. 경기 타임라인 조회
def get_match_timeline(match_id, use_cache=True):

    initialize_database()

    # 1. 캐시 데이터 조회
    if use_cache:

        cached_data = get_cached_timeline(match_id)

        if cached_data is not None:
            print(f"[CACHE HIT] Timeline: {match_id}")

            return cached_data

    # 2. API 요청
    print(f"[API REQUEST] Timeline: {match_id}")

    url = (
        f"https://{ROUTING}.api.riotgames.com"
        f"/lol/match/v5/matches/{match_id}/timeline"
    )

    data = request_api(url)

    # 3. 데이터베이스 저장
    save_timeline(match_id, data)

    # 4. 타임라인 데이터 반환
    return data