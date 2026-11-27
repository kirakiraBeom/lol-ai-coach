
# 실제 API를 호출하지 않고 분석 함수가 정상적으로 동작하는지 확인

import unittest

from timeline import (
    format_timestamp,
    get_frame_at_minute,
    get_all_events,
    analyze_player_deaths,
    analyze_duo_deaths,
    analyze_gold_history,
    analyze_gold_swings
)


class TestTimeline(unittest.TestCase):

    def test_format_timestamp(self):

        self.assertEqual(
            format_timestamp(2375000),
            "39:35"
        )

    def test_get_frame_at_minute(self):

        timeline = {
            "info": {
                "frames": [
                    {"timestamp": 540000},
                    {"timestamp": 600025},
                    {"timestamp": 660000}
                ]
            }
        }

        result = get_frame_at_minute(
            timeline, 10
        )

        self.assertEqual(
            result["timestamp"],
            600025
        )

        self.assertIsNone(
            get_frame_at_minute(timeline, 20)
        )

    def test_get_all_events(self):

        timeline = {
            "info": {
                "frames": [
                    {
                        "events": [
                            {"timestamp": 2000}
                        ]
                    },
                    {
                        "events": [
                            {"timestamp": 1000},
                            {"timestamp": 3000}
                        ]
                    }
                ]
            }
        }

        events = get_all_events(timeline)

        self.assertEqual(
            [event["timestamp"] for event in events],
            [1000, 2000, 3000]
        )

    def test_analyze_player_deaths(self):

        events = [
            {
                "timestamp": 600000,
                "victim_id": 5,
                "killer": "Jhin",
                "assists": ["Rell"],
                "position": None
            },
            {
                "timestamp": 620000,
                "victim_id": 4,
                "killer": "Jhin",
                "assists": [],
                "position": None
            }
        ]

        result = analyze_player_deaths(
            events, 5
        )

        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0]["killer"], "Jhin"
        )

    def test_analyze_duo_deaths(self):

        events = [
            {
                "timestamp": 600000,
                "victim_id": 5,
                "victim": "Blitzcrank"
            },
            {
                "timestamp": 618000,
                "victim_id": 4,
                "victim": "Varus"
            }
        ]

        result = analyze_duo_deaths(
            events, 5, 4
        )

        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0]["interval"], 18
        )

        self.assertEqual(
            analyze_duo_deaths(
                events, 5, 4, interval=10
            ),
            []
        )

    def test_analyze_gold_history(self):

        history = [
            {
                "timestamp": 0,
                "minute": 0,
                "gold_diff": 0
            },
            {
                "timestamp": 60000,
                "minute": 1,
                "gold_diff": 1000
            },
            {
                "timestamp": 120000,
                "minute": 2,
                "gold_diff": -500
            }
        ]

        result = analyze_gold_history(history)

        self.assertEqual(
            result["max_lead"]["gold_diff"],
            1000
        )

        self.assertEqual(
            result["max_deficit"]["gold_diff"],
            -500
        )

        self.assertEqual(
            result["reversals"][0]["type"],
            "LOST_LEAD"
        )

    def test_analyze_gold_swings(self):

        history = [
            {
                "timestamp": 600000,
                "gold_diff": 1000
            },
            {
                "timestamp": 660000,
                "gold_diff": -1000
            }
        ]

        timeline = {
            "info": {
                "frames": [
                    {
                        "events": [
                            {
                                "timestamp": 630000,
                                "type": "CHAMPION_KILL"
                            }
                        ]
                    }
                ]
            }
        }

        result = analyze_gold_swings(
            history, timeline
        )

        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0]["change"], -2000
        )

        self.assertEqual(
            len(result[0]["events"]), 1
        )


if __name__ == "__main__":
    unittest.main()
