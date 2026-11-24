import httpx

from riot_api import(
    get_account, # riot_api.py에서 작성한 get_~~ 함수를 현재 파일에서 불러오기
    get_match_ids,
    get_match_detail
)

from analyzer import (
    load_players,
    find_common_matches,
    analyze_match,
    calculate_stats,
    calculate_average_kda,
    analyze_combinations
)

def main():

    try:

        # 1. 사용자 설정 불러오기
        players = load_players()

        support = players["support"]
        adc = players["adc"]

        # 2. 두 사람의 PUUID 조회
        support_account = get_account(
            support["game_name"],
            support["tag_line"]
        )

        support_puuid = support_account["puuid"]
        adc_puuid = adc_account["puuid"]

        print("===== 듀오 전적 분석 =====")
        print("플레이어 1: ", support["game_name"])
        print("플레이어 2: ", adc["game_name"])

        # 3. 각 계정의 최근 경기 목록 조회
        support_matches = get_match_ids(
            support_puuid, count=20
        )

        adc_matches = get_match_ids(
            adc_puuid, count=20
        )

        # 4. 공통 경기 탐색
        common_matches = find_common_matches(
            support_matches,
            adc_matches
        )

        print("\n공통 경기:", len(common_matches))

        if not common_matches:
            print("공통 경기가 없습니다.")
            return

        analyzed_matches = []

        # 5. 공통 경기 상세 분석
        for match_id in common_matches:

            match = get_match_detail(match_id)

            result = analyze_match(
                match,
                support_puuid,
                adc_puuid
            )

            if result is not None:
                analyzed_matches.append(result)

        # 6. 경기 유형별 분류
        bot_matches = [
            match for match in analyzed_matches
            if match["duo_type"] == "BOT_DUO"
        ]

        other_matches = [
            match for match in analyzed_matches
            if match["duo_type"] == "OTHER_DUO"
        ]

        opponent_matches = [
            match for match in analyzed_matches
            if match["duo_type"] == "OPPONENT"
        ]

        print("\n===== 경기 분류 =====")
        print("바텀 듀오:", len(bot_matches))
        print("기타 같은 팀:", len(other_matches))
        print("상대 팀:", len(opponent_matches))

        # 7. 전체 같은 팀 경기 통계
        stats = calculate_stats(analyzed_matches)

        print("\n===== 전체 같은 팀 전적 =====")
        print("유효 경기:", stats["total"])
        print(f'{stats["wins"]}승 {stats["losses"]}패')
        print(f'승률: {stats["win_rate"]:.2f}%')

        # 8. 바텀 듀오 통계
        bot_stats = calculate_stats(bot_matches)

        print("\n===== 바텀 듀오 전적 =====")
        print("유효 경기:", bot_stats["total"])
        print(
            f'{bot_stats["wins"]}승 '
            f'{bot_stats["losses"]}패'
        )
        print(f'승률: {bot_stats["win_rate"]:.2f}%')

        # 9. 계정별 평균 KDA
        print("\n===== 바텀 듀오 평균 KDA =====")

        if bot_stats["total"] == 0:
            print("분석 가능한 바텀 듀오 경기가 없습니다.")

        else:
            for role in ["support", "adc"]:

                kda = calculate_average_kda(
                    bot_matches, role
                )

                print(
                    f'{players[role]["game_name"]}: '
                    f'{kda["kills"]:.1f}/'
                    f'{kda["deaths"]:.1f}/'
                    f'{kda["assists"]:.1f} | '
                    f'KDA {kda["kda"]:.2f}'
                )

        # 10. 챔피언 조합별 통계
        combinations = analyze_combinations(
            analyzed_matches
        )

        print("\n===== 챔피언 조합별 전적 =====")

        for combo in combinations:

            print(
                f'{combo["support"]} + '
                f'{combo["adc"]} | '
                f'{combo["total"]}경기 | '
                f'{combo["wins"]}승 '
                f'{combo["losses"]}패 | '
                f'승률 {combo["win_rate"]:.2f}%'
            )

        if not combinations:
            print("분석 가능한 조합이 없습니다.")

        # 11. 공통 경기 상세 목록
        print("\n===== 공통 경기 목록 =====")

        for match in analyzed_matches:

            if match["remake"]:
                result = "다시하기"

            else:
                result = "승리" if match["win"] else "패배"

            print(
                f'{match["support"]["champion"]} + '
                f'{match["adc"]["champion"]} | '
                f'{match["duo_type"]} | '
                f'{result} | '
                f'{match["duration"] // 60}분 '
                f'{match["duration"] % 60}초'
            )

    except FileNotFoundError:
        print("players.json 파일을 찾을 수 없습니다.")

    except httpx.HTTPStatusError as e:
        print("API 오류:", e.response.status_code)
        print("요청 URL:", e.request.url)
        print("응답 내용:", e.response.text)

    except httpx.TimeoutException:
        print("서버 응답 시간이 초과되었습니다.")

    except httpx.RequestError:
        print("네트워크 연결에 실패했습니다.")

    except ValueError as e:
        print("설정 또는 데이터 오류:", e)


if __name__ == "__main__":
    main()