
import unittest

from analyzer import (
    find_common_matches,
    find_player,
    classify_duo,
    analyze_combinations
)


class TestAnalyzer(unittest.TestCase):

    # 공통 경기 탐색 테스트
    def test_common_matches(self):

        result = find_common_matches(
            ["A", "B", "C"],
            ["B", "C", "D"]
        )

        self.assertEqual(result, ["B", "C"])

    # 플레이어 탐색 테스트
    def test_find_player(self):

        match = {
            "info": {
                "participants": [
                    {"puuid": "A"},
                    {"puuid": "B"}
                ]
            }
        }

        result = find_player(match, "B")

        self.assertEqual(result, {"puuid": "B"})

    # 바텀 듀오 분류 테스트
    def test_bot_duo(self):

        support = {
            "teamId": 100,
            "teamPosition": "UTILITY"
        }

        adc = {
            "teamId": 100,
            "teamPosition": "BOTTOM"
        }

        self.assertEqual(
            classify_duo(support, adc),
            "BOT_DUO"
        )

    # 빈 경기 목록 테스트
    def test_empty_combinations(self):

        result = analyze_combinations([])

        self.assertEqual(result, [])

    # 여러 경기 조합 집계 테스트
    def test_multiple_combinations(self):

        match = {
            "remake": False,
            "duo_type": "BOT_DUO",
            "win": True,
            "support": {
                "champion": "Leona",
                "position": "UTILITY"
            },
            "adc": {
                "champion": "Kaisa",
                "position": "BOTTOM"
            }
        }

        matches = [
            match,
            {**match, "win": False},
            {**match, "remake": True}
        ]

        result = analyze_combinations(matches)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["total"], 2)
        self.assertEqual(result[0]["wins"], 1)
        self.assertEqual(result[0]["losses"], 1)
        self.assertEqual(result[0]["win_rate"], 50.0)


if __name__ == "__main__":
    unittest.main()
