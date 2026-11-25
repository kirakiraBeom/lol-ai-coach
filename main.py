import httpx

from riot_api import(
    get_account, # riot_api.py에서 작성한 get_~~ 함수를 현재 파일에서 불러오기
    get_rank,
    get_match_ids,
    get_match_detail
)

from analyzer import is_remake

def main():
    game_name = input("라이엇 닉네임: ").strip()
    tag_line = input("태그(# 제외): ").strip()

    try:

        # 1. 계정 조회
        account = get_account(game_name, tag_line)
        puuid = account["puuid"]

        print("\n===== 계정 정보 =====")
        print("닉네임:", account["gameName"])
        print("태그:", account["tagLine"])

        # 2. 랭크 조회
        ranks = get_rank(puuid)

        print("\n===== 솔로 랭크 =====")

        solo_rank = next(
            (
            rank for rank in ranks
            if rank["queueType"] == "RANKED_SOLO_5x5"
            ),
            None
        )

        if solo_rank:
            wins = solo_rank["wins"]
            losses = solo_rank["losses"]

            total = wins + losses
            win_rate = wins / total * 100 if total else 0

            print("티어:", solo_rank["tier"])
            print("랭크:", solo_rank["rank"])
            print("LP:", solo_rank["leaguePoints"])
            print(f"승패: {wins}승 {losses}패")
            print(f"승률: {win_rate:.2f}%")

        else:
            print("솔로 랭크 정보가 없습니다.")

        # 3. 최근 경기 조회
        match_ids = get_match_ids(puuid, count=5)

        print("\n===== 최근 5경기 ======")

        for match_id in match_ids:

            match = get_match_detail(match_id)

            participants = match["info"]["participants"]

            for player in participants:

                if player["puuid"] == puuid:

                    champion = player["championName"]

                    kills = player["kills"]
                    deaths = player["deaths"]
                    assists = player["assists"]

                    duration = match["info"]["gameDuration"]

                    early_surrender = player.get(
                        "gameEndedInEarlySurrender", False
                    )

                    # 승패 및 다시하기 판단
                    if early_surrender and duration < 300:
                        result = "다시하기"

                    elif player["win"]:
                        result = "승리"

                    else:
                        result = "패배"

                    minutes = duration // 60
                    seconds = duration % 60

                    print(
                        f"{champion} | "
                        f"{kills}/{deaths}/{assists} | "
                        f"{result} | "
                        f"{minutes}분 {seconds}초"
                    )

                    break

        if not match_ids:
            print("최근 경기 정보가 없습니다.")

    except httpx.HTTPStatusError as e:
        status = e.response.status_code

        print("\n ====== 오류 발생 ======")
        print("상태 코드:", status)
        print("요청 URL:", e.request.url)
        print("응답 내용:", e.response.text)

        if status == 403:
            print("API 키 또는 API 요청 경로를 확인하세요.")

        elif status == 404:
            print("계정 또는 데이터를 찾을 수 없습니다.")

        elif status == 429:
            print("API 요청 한도를 초과했습니다.")

    except httpx.TimeoutException:
        print("서버 응답 시간이 초과되었습니다.")

    except httpx.RequestError:
        print("네트워크 연결에 실패했습니다.")

    except ValueError as e:
        print("설정 오류:", e)

if __name__ == "__main__":
    main()