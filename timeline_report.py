import httpx

from riot_api import (
    get_account,
    get_match_ids,
    get_match_detail,
    get_match_timeline
)

from analyzer import (
    load_players,
    find_common_matches,
    analyze_match
)

from timeline import (
    get_participant_id,
    find_lane_opponent,
    calculate_lane_difference,
    calculate_team_gold_history,
    analyze_gold_history,
    format_timestamp,
    create_participant_map,
    analyze_kill_events,
    analyze_player_deaths,
    analyze_duo_deaths,
    analyze_objective_events,
    analyze_building_events,
    analyze_gold_swings
)

def main():
    try:
        # 1. 듀오 계정 설정 불러오기
        players = load_players()

        support = players["support"]
        adc = players["adc"]

        support_account = get_account(
            support["game_name"],
            support["tag_line"]
        )

        adc_account = get_account(
            adc["game_name"],
            adc["tag_line"]
        )

        support_puuid = support_account["puuid"]
        adc_puuid = adc_account["puuid"]

        # 2. 공통 경기 탐색
        support_matches = get_match_ids(
            support_puuid, count=20
        )

        adc_matches = get_match_ids(
            adc_puuid, count=20
        )

        common_matches = find_common_matches(
            support_matches,
            adc_matches
        )

        selected_match = None

        # 3. 최근 유효한 바텀 듀오 경기 선택
        for match_id in common_matches:

            match = get_match_detail(match_id)

            result = analyze_match(
                match,
                support_puuid,
                adc_puuid
            )

            if result is None:
                continue

            if result["remake"]:
                continue

            if result["duo_type"] != "BOT_DUO":
                continue

            selected_match = match
            break

        if selected_match is None:
            print("분석 가능한 바텀 듀오 경기가 없습니다.")
            return

        # 4. 타임라인 조회
        match_id = selected_match["metadata"]["matchId"]

        timeline = get_match_timeline(match_id)

        print("===== 경기 타임라인 분석 =====")
        print("경기 ID:", match_id)

        team_id = None

        # 5. 플레이어별 성장 격차 분석
        for role, puuid in [
            ("support", support_puuid),
            ("adc", adc_puuid)
        ]:

            participant_id = get_participant_id(
                selected_match, puuid
            )

            opponent = find_lane_opponent(
                selected_match, participant_id
            )

            if opponent is None:
                print("상대 라이너를 찾을 수 없습니다.")
                continue

            opponent_id = opponent["participantId"]

            player = next(
                p for p in selected_match["info"]["participants"]
                if p["participantId"] == participant_id
            )

            team_id = player["teamId"]

            print(
                f'\n===== {players[role]["game_name"]} ====='
            )

            print(
                f'{player["championName"]} vs '
                f'{opponent["championName"]}'
            )

            duration = selected_match["info"]["gameDuration"]

            for minute in [5, 10, 15, 20]:

                if minute * 60 > duration:
                    continue

                result = calculate_lane_difference(
                    timeline,
                    participant_id,
                    opponent_id,
                    minute
                )

                if result is None:
                    continue

                print(
                    f'{minute}분 | '
                    f'골드 {result["gold_diff"]:+,}G | '
                    f'CS {result["cs_diff"]:+} | '
                    f'경험치 {result["xp_diff"]:+,} | '
                    f'레벨 {result["level_diff"]:+}'
                )

        # 6. 팀 전체 골드 흐름 분석
        if team_id is None:
            print("팀 정보를 찾을 수 없습니다.")
            return

        history = calculate_team_gold_history(
            selected_match,
            timeline,
            team_id
        )

        summary = analyze_gold_history(history)

        if summary is None:
            print("골드 기록이 없습니다.")
            return

        print("\n===== 팀 골드 변화 =====")

        for frame in history:

            print(
                f'{frame["minute"]}분 | '
                f'{frame["gold_diff"]:+,}G'
            )

        # 7. 주요 골드 변화 시점 출력
        lead = summary["max_lead"]
        deficit = summary["max_deficit"]

        print("\n===== 경기 흐름 요약 =====")

        print(
            f'최대 골드 격차: {lead["minute"]}분 | '
            f'{lead["gold_diff"]:+,}G'
        )

        print(
            f'최소 골드 격차: {deficit["minute"]}분 | '
            f'{deficit["gold_diff"]:+,}G'
        )

        print(
            f'최종 골드 격차: '
            f'{summary["final_gold_diff"]:+,}G'
        )

        print("\n===== 골드 우위 변화 시점 =====")

        for event in summary["reversals"]:

            label = (
                "골드 우위 상실"
                if event["type"] == "LOST_LEAD"
                else "골드 우위 확보"
            )

            print(
                f'{event["minute"]}분 | '
                f'{label} | '
                f'{event["gold_diff"]:+,}G'
            )

        if not summary["reversals"]:
            print("골드 우위 전환이 없습니다.")

        # 8. 챔피언 처치 이벤트 분석
        kill_events = analyze_kill_events(
            selected_match, timeline
        )

        print("\n===== 퍼스트 블러드 =====")

        first_blood = next(
            (
                event for event in kill_events
                if event["killer_team"] is not None
                and event["killer_team"] != event["victim_team"]
            ),
            None
        )

        if first_blood:
            print(
                f'{format_timestamp(first_blood["timestamp"])} | '
                f'{first_blood["killer"]} -> '
                f'{first_blood["victim"]}'
            )

        # 9. 플레이어별 데스 분석
        for role, puuid in [
            ("support", support_puuid),
            ("adc", adc_puuid)
        ]:
            participant_id = get_participant_id(
                selected_match, puuid
            )

            deaths = analyze_player_deaths(
                kill_events, participant_id
            )

            print(
                f'\n===== {players[role]["game_name"]} '
                f'데스기록 ====='
            )

            print("총 데스: ", len(deaths))

            for death in deaths:

                print(
                    f'{format_timestamp(death["timestamp"])} | '
                    f'처치자: {death["killer"]} | '
                    f'어시스트: '
                    f'{", ".join(death["assists"]) or "없음"}'
                )

        # 10. 듀오 연속 데스 분석
        support_id = get_participant_id(
            selected_match, support_puuid
        )

        adc_id = get_participant_id(
            selected_match, adc_puuid
        )

        duo_deaths = analyze_duo_deaths(
            kill_events,
            support_id,
            adc_id
        )

        print("\n===== 듀오 연속 데스 =====")

        for death in duo_deaths:

            print(
                f'{format_timestamp(death["timestamp"])} | '
                f'{death["first"]} -> {death["second"]} | '
                f'{death["interval"]:.1f}초 간격'
            )

        if not duo_deaths:
            print("연속 데스가 없습니다.")

        # 11. 오브젝트 분석
        objectives = analyze_objective_events(
            selected_match, timeline
        )

        print("\n===== 주요 오브젝트 기록 =====")

        for objective in objectives:

            objective_team = objective["team_id"]

            if objective_team is None:
                side = "팀 확인 불가"

            elif objective_team == team_id:
                side = "아군"

            else:
                side = "상대"

            print(
                f'{format_timestamp(objective["timestamp"])} | '
                f'{side} | '
                f'{objective["monster"]} | '
                f'{objective["sub_type"] or "-"} | '
                f'{objective["killer"]}'
            )
        # 12. 건물 파괴 분석
        buildings = analyze_building_events(
            selected_match, timeline
        )

        print("\n===== 포탑 및 억제기 파괴 =====")

        for building in buildings:

            destryoed_team = building["destroyed_team"]

            if destryoed_team is None:
                side = "팀 확인 불가"

            elif destryoed_team == team_id:
                side = "아군 건물 파괴"

            else:
                side = "상대 건물 파괴"

            print(
                f'{format_timestamp(building["timestamp"])} | '
                f'{side} | '
                f'{building["lane"]} | '
                f'{building["tower"] or building["building"]}'
            )

        # 13. 주요 골드 변화 구간 분석
        swings = analyze_gold_swings(
            history,
            timeline,
            threshold=1500
        )

        participant_map = create_participant_map(
            selected_match
        )

        print("\n===== 주요 골드 변화 구간 =====")

        for swing in swings:

            print(
                f'\n{format_timestamp(swing["start"])} ~ '
                f'{format_timestamp(swing["end"])} | '
                f'{swing["change"]:+,}G 변화'
            )

            print(
                f'골드 격차: {swing["before"]:+,}G → '
                f'{swing["after"]:+,}G'
            )

            for event in swing["events"]:

                time = format_timestamp(
                    event["timestamp"]
                )

                event_type = event["type"]

                killer = participant_map.get(
                    event.get("killerId", 0), {}
                ).get("champion", "Unknown")

                if event_type == "CHAMPION_KILL":

                    victim = participant_map.get(
                        event.get("victimId", 0), {}
                    ).get("champion", "Unknown")

                    print(
                        f'  {time} | 챔피언 처치 | '
                        f'{killer} → {victim}'
                    )

                elif event_type == "ELITE_MONSTER_KILL":

                    print(
                        f'  {time} | 오브젝트 | '
                        f'{event.get("monsterType")} | '
                        f'{killer}'
                    )

                elif event_type == "BUILDING_KILL":

                    print(
                        f'  {time} | 건물 파괴 | '
                        f'{event.get("laneType")} | '
                        f'{event.get("buildingType")}'
                    )

            if not swing["events"]:
                print("  주요 이벤트가 없습니다.")


    except FileNotFoundError:
        print("players.json 파일을 찾을 수 없습니다.")

    except httpx.HTTPStatusError as e:
        print("API 오류:", e.response.status_code)
        print("응답 내용:", e.response.text)

    except httpx.TimeoutException:
        print("서버 응답 시간이 초과되었습니다.")

    except httpx.RequestError:
        print("네트워크 연결에 실패했습니다.")

    except ValueError as e:
        print("설정 또는 데이터 오류:", e)


if __name__ == "__main__":
    main()