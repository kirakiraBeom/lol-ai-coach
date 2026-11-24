import json

from pathlib import Path

def load_players(): # 계정 설정 불러오기

    path = Path(__file__).with_name("players.json")

    with open(path, "r", encoding="utf-8") as file:
        players = json.load(file)

    return players

def find_common_matches(support_matches, adc_matches): # 두 플레이어의 공통 경기 ID 찾기
    
    adc_match_set = set(adc_matches) #set은 중복 허용 X, 시간순 정렬 X

    common_matches = [
        match_id
        for match_id in support_matches
        if match_id in adc_match_set
    ]

    return common_matches

def find_player(match, puuid): # 특정 경기에서 플레이어 정보 찾기

    participants = match["info"]["participants"]

    for player in participants:

        if player["puuid"] == puuid:
            return player

        return None

def classify_duo(support, adc): # 같은 팀으로 플레이했는지, 바텀 포지션인지

    if support["teamId"] != adc["teamId"]:
        return "OPPONENT"

    positions = {
        support.get("teamPosition"),
        adc.get("teamPosition")
    }

    if positions == {"UTILITY", "BOTTOM"}:
        return "BOT_DUO"

    return "OTHER_DUO"

def is_remake(match): # 다시하기 경기인지 확인

    duration = match["info"]["gameDuration"]

    participants = match["info"]["participants"]

    early_surrender = any(
        player.get("gameEndedInEarlySurrender", False)
        for player in participants
    )

    return early_surrender and duration < 300

def analyze_match(match, support_puuid, adc_puuid): # 경기 데이터 가공하기

    support = find_player(match, support_puuid)
    adc = find_player(match, adc_puuid)

    if support is None or adc is None:
        return None

    duo_type = classify_duo(support, adc)

    remake = is_remake(match)

    return {
        "match_id": match["metadata"]["matchId"],
        "duration": match["info"]["gameDuration"],
        "duo_type": duo_type,
        "remake": remake,
        "win": support["win"],

        "support": {
            "champion": support["championName"],
            "position": support.get("teamPosition"),
            "kills": support["kills"],
            "deaths": support["deaths"],
            "assists": support["assists"]
        },

        "adc": {
            "champion": adc["championName"],
            "position": adc.get("teamPosition"),
            "kills": adc["kills"],
            "deaths": adc["deaths"],
            "assists": adc["assists"]
        }
    }

def calculate_stats(matches): # 듀오 승률과 평균 KDA 계산

    valid_matches = [
        match for match in matches
        if not match["remake"]
        and match["duo_type"] != "OPPONENT"
    ]

    total = len(valid_matches)

    wins = sum(
        1 for match in valid_matches
        if match["win"]
    )

    losses = total - wins

    win_rate = wins / total * 100 if total else 0

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate
    }

def analyze_combinations(matches):

    combinations = {}

    for match in matches:

        if match in matches:

            if match["remake"]:
                continue

            if match["duo_type"] != "BOT_DUO":
                continue

            player1 = match["support"]
            player2 = match["adc"]

            # 실제 플레이 포지션을 기준으로 조합 생성
            if player1["position"] == "UTILITY":
                support = player1
                adc = player2
            else:
                support = player2
                adc = player1

            key = (
                support["champion"],
                adc["champion"]
            )

            if key not in combinations:

                combinations[key] = {
                    "wins": 0,
                    "losses": 0,
                }

            if match["win"]:
                combinations[key]["wins"] += 1

            else:
                combinations[key]["losses"] += 1

        results = []

        for key, stats in combinations.items():

            wins = stats["wins"]
            losses = stats["losses"]
            total = wins + losses

            results.append({
                "support": key[0],
                "adc": key[1],
                "total": total,
                "wins": wins,
                "losses": losses,
                "win_rate": wins / total * 100
            })
        return sorted(
            results,
            key = lambda item: item["total"],
            reverse=True
        )