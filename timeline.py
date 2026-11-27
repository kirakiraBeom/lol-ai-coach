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

def format_timestamp(timestamp): # 공통 시간 변환 함수 추가 / 

    total_seconds = timestamp // 1000

    minutes, seconds = divmod(total_seconds, 60)

    return f"{minutes:02d}:{seconds:02d}"

def get_frame_at_minute(timeline, minute): # 가장 가까운 프레임을 선택하되, 허용 오차를 5초로 제한하기

    frames = timeline["info"]["frames"]

    if not frames:
        return None

    target_timestamp = minute * 60000

    selected_frame = min(
        frames,
        key=lambda frame: abs(
            frame["timestamp"] - target_timestamp
        )
    )

    difference = abs(
        selected_frame["timestamp"] - target_timestamp
    )

    if difference > 5000:
        return None

    return selected_frame

def get_all_events(timeline): # 전체 이벤트 가져오기

    events = []

    for frame in timeline["info"]["frames"]:

        events.extend(
            frame.get("events", [])
        )

    return sorted(
        events,
        key=lambda event: event["timestamp"]
    )

def create_participant_map(match): # 참가자 정보 매핑
    participants = match["info"]["participants"]

    return {
        player["participantId"]: {
            "champion": player["championName"],
            "team_id": player["teamId"],
            "position": player.get("teamPosition")
        }

        for player in participants
    }

def analyze_kill_events(match, timeline): # 챔피언 처치 이벤트 분석

    participant_map = create_participant_map(match)

    events = get_all_events(timeline)

    kills = []

    for event in events:

        if event["type"] != "CHAMPION_KILL":
            continue

        killer_id = event.get("killerId", 0)
        victim_id = event.get("victimId", 0)

        killer = participant_map.get(killer_id, {})
        victim = participant_map.get(victim_id, {})

        assists = [
            participant_map[pid]["champion"]
            for pid in event.get(
                "assistingParticipantIds", []
            )
            if pid in participant_map
        ]

        kills.append({
            "timestamp": event["timestamp"],

            "killer_id": killer_id,
            "victim_id": victim_id,

            "killer": killer.get(
                "champion", "Unknown"
            ),

            "victim": victim.get(
                "champion", "Unknown"
            ),

            "killer_team": killer.get("team_id"),
            "victim_team": victim.get("team_id"),

            "assists": assists,
            "position": event.get("position")
        })

    return kills

def analyze_player_deaths(kill_events, participant_id):

    deaths = []

    for event in kill_events:

        if event["victim_id"] != participant_id:
            continue

        deaths.append({
            "timestamp": event["timestamp"],
            "killer": event["killer"],
            "assists": event["assists"],
            "position": event["position"]
        })

    return deaths

def analyze_duo_deaths(
        kill_events,
        support_id,
        adc_id,
        interval=30
):

    duo_ids = {support_id, adc_id}

    deaths = [
        event
        for event in kill_events
        if event["victim_id"] in duo_ids
    ]

    deaths.sort(
        key=lambda event: event["timestamp"]
    )

    results = []

    for first, second in zip(deaths, deaths[1:]):

        if first["victim_id"] == second["victim_id"]:
            continue

        difference = (
            second["timestamp"]
            - first["timestamp"]
        )

        if difference <= interval * 1000:

            results.append({
                "first": first["victim"],
                "second": second["victim"],

                "timestamp": first["timestamp"],

                "interval": difference / 1000
            })

    return results

def analyze_objective_events(match, timeline):

    participant_map = create_participant_map(match)

    objectives = []

    for event in get_all_events(timeline):

        if event["type"] != "ELITE_MONSTER_KILL":
            continue

        killer_id = event.get("killerId", 0)

        killer = participant_map.get(killer_id, {})

        team_id = (
            event.get("killerTeaemId")
            or killer.get("team_id")
        )

        objectives.append({
            "timestamp": event["timestamp"],

            "monster": event.get("monsterType"),

            "sub_type": event.get("monsterSubType"),

            "killer": killer.get(
                "champion", "Unknown"
            ),

            "team_id": team_id
        })

    return objectives

def analyze_building_events(match, timeline):
    participant_map = create_participant_map(match)

    buildings = []

    for event in get_all_events(timeline):

        if event["type"] != "BUILDING_KILL":
            continue

        killer = participant_map.get(
            event.get("killerId", 0), {}
        )

        buildings.append({
            "timestamp": event["timestamp"],

            "building": event.get("buildingType"),

            "tower": event.get("towerType"),

            "lane": event.get("laneType"),

            "destroyed_team": event.get("teamId"),

            "killer": killer.get(
                "champion", "Unknown"
            )
        })

    return buildings

def analyze_gold_swings(
    history,
    timeline,
    threshold=1500
):
    events = get_all_events(timeline)

    important_types = {
        "CHAMPION_KILL",
        "ELITE_MONSTER_KILL",
        "BUILDING_KILL"
    }

    results = []

    for previous, current in zip(
        history, history[1:]
    ):
        change = (
            current["gold_diff"]
            - previous["gold_diff"]
        )

        if abs(change) < threshold:
            continue

        start = previous["timestamp"]
        end = current["timestamp"]

        related_events = [
            event
            for event in events

            if start < event["timestamp"] <= end

            and event["type"] in important_types
        ]

        results.append({
            "start": start,
            "end": end,

            "before": previous["gold_diff"],
            "after": current["gold_diff"],

            "change": change,

            "events": related_events
        })

    return sorted(
        results,
        key=lambda item: abs(item["change"]),
        reverse=True
    )