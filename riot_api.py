import os
import httpx 

from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote

# 1. 환경 변수 불러오기
load_dotenv(Path(__file__).with_name(".env"))

api_key = os.getenv("RIOT_API_KEY")
routing = os.getenv("RIOT_ROUTING", "asia")

if not api_key:
    raise ValueError("RIOT_API_KEY가 설정되지 않았습니다.")

# 2. 사용자 정보 입력
game_name = input("라이엇 닉네임: ")
tag_line = input("태그(# 제외): ")

# 3. API 요청 주소 생성
url = (
    f"https://{routing}.api.riotgames.com" # 문자열 앞에 f를 붙이면 중괄호 안에 변수나 표현식을 넣을 수 있다.
    f"/riot/account/v1/accounts/by-riot-id"
    f"/{quote(game_name, safe='')}"
    f"/{quote(tag_line, safe='')}"
)

# 4. HTTP Header 설정
headers = {
    "X-Riot-Token": api_key
}

# 5. API 요청
response = httpx.get(
    url, 
    headers=headers, 
    timeout=10.0
)

# 6. 응답 결과 확인
print("상태 코드: ", response.status_code)

if response.status_code == 200:
    data = response.json()
    
    print("닉네임: ", data["gameName"])
    print("태그: ", data["tagLine"])
    print("PUUID: ", data["puuid"])

else:
    print("API 요청 실패: ")
    print(response.text)