def get_participant_id(match, puuid): # 1. 플레이어 ID 조회 : find_player()와 비슷하지만 participantId만 반환

    participants = match["info"]["participants"]

    for player in participants:

        if player["puuid"] == puuid:
            return player["participantId"] # 특정 경기의 참가자, 경기 내부 데이터를 조회

    return None

def get_frame_at_minute(timeline, minute): # 2. 특정 시간의 Frame 찾기

    frames = timeline["info"]["frames"]

    target_timestamp = minute * 60 * 1000

    selected_frame = None

    for frame in frames:

        if frame["timestamp"] <= target_timestamp:
            selected_frame = frame

        else:
            break

    return selected_frame

def get_player_frame(frame, participant_id): # 3. 플레이어 성장 정보 추출

    if frame is None:
        return None

    participants = frame["participantFrames"]

    player = participants.get(str(participant_id))

    if player is None:
        return None

    return {
        "gold": player["totalGold"],
        "current_gold": player["currentGold"],
        "cs": (
            player["minionsKilled"]
            + player["jungleMinionsKilled"]
        ),
        "xp": player["xp"],
        "level": player["level"]
    }

def find_lane_opponent(match, participant_id): # 상대 라이너 찾기

    participants = match["info"]["participants"]

    target = None

    # 1. 분석할 플레이어 찾기
    for player in participants:

        if player["participantId"] == participant_id:
            target = player
            break

    if target is None:
        return None

    position = target.get("teamPosition")

    if not position:
        return None

    # 2. 상대 팀의 동일 포지션 찾기
    for player in participants:

        if (
            player["teamId"] != target["teamId"]
            and player.get("teamPosition") == position
        ):
            return player

    return None

def calculate_lane_difference( # 시간대별 성장 격차 계산
    timeline,
    participant_id,
    opponent_id,
    minute
):
    frame = get_frame_at_minute(timeline, minute)

    player = get_player_frame(frame, participant_id)
    opponent = get_player_frame(frame, opponent_id)

    if player is None or opponent is None:
        return None

    return {
        "minute": minute,
        "timestamp": frame["timestamp"],

        "player": player,
        "opponent": opponent,

        "gold_diff": (
            player["gold"] - opponent["gold"]
        ),

        "cs_diff": (
            player["cs"] - opponent["cs"]
        ),

        "xp_diff": (
            player["xp"] - opponent["xp"]
        ),

        "level_diff": (
            player["level"] - opponent["level"]
        )
    }

def calculate_team_gold_history(match, timeline, team_id): # 팀 골드 변화량 계산

    participants = match["info"]["participants"]

    ally_ids = [
        player["participantId"]
        for player in participants
        if player["teamId"] == team_id
    ]

    enemy_ids = [
        player["participantId"]
        for player in participants
        if player["teamId"] != team_id
    ]

    history = []

    for frame in timeline["info"]["frames"]:

        players = frame["participantFrames"]

        ally_gold = sum(
            players[str(pid)]["totalGold"]
            for pid in ally_ids
        )

        enemy_gold = sum(
            players[str(pid)]["totalGold"]
            for pid in enemy_ids
        )

        history.append({
            "timestamp": frame["timestamp"],
            "minute": frame["timestamp"] // 60000,
            "ally_gold": ally_gold,
            "enemy_gold": enemy_gold,
            "gold_diff": ally_gold - enemy_gold
        })

    return history

def analyze_gold_history(history): # 최대 골드 우위 및 역전 시점 탐색

    if not history:
        return None

    max_lead = max(
        history,
        key=lambda frame: frame["gold_diff"]
    )

    max_deficit = min(
        history,
        key=lambda frame: frame["gold_diff"]
    )

    reversals = []

    pervious_side = 0

    for frame in history:

        diff = frame["gold_diff"]

        if diff == 0:
            continue

        current_side = 1 if diff > 0 else -1

        if pervious_side != 0 and current_side != pervious_side:

            reversals.append({
                "minute": frame["minute"],
                "timestamp": frame["timestamp"],
                "gold_diff": diff,
                "type": (
                    "LOST_LEAD"
                    if current_side == -1
                    else "GAINED_LEAD"
                )
            })

        pervious_side = current_side

    return {
        "max_lead": max_lead,
        "max_deficit": max_deficit,
        "final_gold_diff": history[-1]["gold_diff"],
        "reversals": reversals
    }