import sqlite3
import json

from pathlib import Path
from contextlib import closing

ROOT_DIR = Path(__file__).resolve().parent

DATA_DIR = ROOT_DIR / "data"

DB_PATH = DATA_DIR / "lol_coach.db"

def get_connection():

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DB_PATH)

    return connection

def initialize_database():

    with closing(get_connection()) as connection:

        with connection:

            connection.execute(
                """CREATE TABLE IF NOT EXISTS matches(
                    match_id TEXT PRIMARY KEY NOT NULL,
                    data TEXT NOT NULL,
                    cached_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS timelines (
                    match_id TEXT PRIMARY KEY NOT NULL,
                    data TEXT NOT NULL,
                    cached_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                )
            """)

def save_match(match_id, data):

    json_data = json.dumps(
        data,
        ensure_ascii=False
    )

    with closing(get_connection()) as connection:

        with connection:

            connection.execute("""
                INSERT INTO matches (
                    match_id,
                    data
                )
                VALUES (?, ?)

                ON CONFLICT(match_id)
                DO UPDATE SET
                    data = excluded.data,
                    cached_at = CURRENT_TIMESTAMP
            """, (match_id, json_data))

def get_cached_match(match_id):

    with closing(get_connection()) as connection:

        cursor = connection.execute("""
            SELECT data
            FROM matches
            WHERE match_id = ?
        """, (match_id,))

        row = cursor.fetchone()

    if row is None:
        return None

    return json.loads(row[0])

def save_timeline(match_id, data):

    json_data = json.dumps(
        data,
        ensure_ascii=False
    )

    with closing(get_connection()) as connection:

        with connection:

            connection.execute("""
                INSERT INTO timelines (
                    match_id,
                    data
                )
                VALUES (?, ?)

                ON CONFLICT(match_id)
                DO UPDATE SET
                    data = excluded.data,
                    cached_at = CURRENT_TIMESTAMP
            """, (match_id, json_data))

def get_cached_timeline(match_id):

    with closing(get_connection()) as connection:

        cursor = connection.execute("""
            SELECT data
            FROM timelines
            WHERE match_id = ?

        """, (match_id,))

        row = cursor.fetchone()

    if row is None:
        return None

    return json.loads(row[0])



if __name__ == "__main__":

    initialize_database()

    print("데이터베이스 초기화 완료")
    print("DB 경로:", DB_PATH)

    with closing(get_connection()) as connection:

        match_count = connection.execute(
            "SELECT COUNT(*) FROM matches"
        ).fetchone()[0]

        timeline_count = connection.execute(
            "SELECT COUNT(*) FROM timelines"
        ).fetchone()[0]

        print("저장된 경기: ", match_count)
        print("저장된 타임라인: ", timeline_count)