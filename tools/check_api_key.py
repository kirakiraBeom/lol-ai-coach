
import httpx

from getpass import getpass
from pathlib import Path
from urllib.parse import quote
from dotenv import dotenv_values


# 프로젝트 루트 디렉터리 설정
ROOT_DIR = Path(__file__).resolve().parent.parent


def main():

    print("===== Riot API 인증 진단 =====")

    # 1. API 키 입력
    api_key = getpass("Riot API Key: ").strip()

    if not api_key:
        print("API 키가 입력되지 않았습니다.")
        return

    # 2. .env 파일의 API 키 비교
    env_path = ROOT_DIR / ".env"

    if env_path.exists():

        env_key = dotenv_values(env_path).get("RIOT_API_KEY")

        print(".env API 키 일치 여부:", api_key == env_key)

    else:
        print(".env 파일을 찾을 수 없습니다.")

    # 3. 라이엇 계정 정보 입력
    game_name = input("라이엇 닉네임: ").strip()
    tag_line = input("태그(# 제외): ").strip()

    # 4. 테스트할 API 목록
    urls = {
        "LOL-STATUS-V4": (
            "https://kr.api.riotgames.com"
            "/lol/status/v4/platform-data"
        ),
        "ACCOUNT-V1": (
            "https://asia.api.riotgames.com"
            "/riot/account/v1/accounts/by-riot-id"
            f"/{quote(game_name, safe='')}"
            f"/{quote(tag_line, safe='')}"
        )
    }

    # 5. API 요청 및 결과 확인
    for name, url in urls.items():

        print(f"\n===== {name} =====")

        try:

            response = httpx.get(
                url,
                headers={"X-Riot-Token": api_key},
                timeout=10.0
            )

            status = response.status_code

            print("상태 코드:", status)

            if status == 200:
                print("API 요청 성공")

            elif status == 401:
                print("API 키 인증 실패")

            elif status == 403:
                print("API 접근 권한 또는 요청 경로 확인 필요")

            elif status == 404:
                print("요청한 데이터를 찾을 수 없습니다.")

            elif status == 429:
                print("API 요청 한도를 초과했습니다.")

            else:
                print("기타 API 오류")

            if status != 200:
                print("응답 내용:", response.text)

        except httpx.TimeoutException:
            print("서버 응답 시간이 초과되었습니다.")

        except httpx.RequestError:
            print("네트워크 연결에 실패했습니다.")


if __name__ == "__main__":
    main()
