"""SQLite 存储模块 - 产品信息与每日快照"""

import sqlite3
import logging
from datetime import date, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    asin        TEXT PRIMARY KEY,
    url         TEXT NOT NULL,
    title       TEXT NOT NULL DEFAULT '',
    enabled     INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asin        TEXT NOT NULL,
    date        TEXT NOT NULL,           -- YYYY-MM-DD
    rating      REAL,
    review_count INTEGER,
    fetched_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (asin) REFERENCES products(asin),
    UNIQUE(asin, date)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_date ON snapshots(date);
CREATE INDEX IF NOT EXISTS idx_snapshots_asin ON snapshots(asin);
"""


class Storage:
    """管理 SQLite 数据库的读写"""

    def __init__(self, db_path: str | Path = "data/tracker.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def ensure_product(self, asin: str, url: str, title: str = ""):
        """插入或更新产品记录"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT INTO products (asin, url, title) VALUES (?, ?, ?)
                   ON CONFLICT(asin) DO UPDATE SET url=excluded.url, title=excluded.title""",
                (asin, url, title),
            )
            conn.commit()

    def save_snapshot(self, asin: str, snapshot_date: str, rating: float | None, review_count: int | None):
        """保存当天快照"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO snapshots (asin, date, rating, review_count, fetched_at)
                   VALUES (?, ?, ?, ?, datetime('now', 'localtime'))""",
                (asin, snapshot_date, rating, review_count),
            )
            conn.commit()

    def save_snapshots_batch(self, results: list[dict], snapshot_date: str):
        """批量保存快照"""
        count = 0
        for r in results:
            if r.get("error"):
                continue
            self.ensure_product(r["asin"], r["url"], r.get("title", ""))
            self.save_snapshot(r["asin"], snapshot_date, r.get("rating"), r.get("review_count"))
            count += 1
        logger.info(f"已保存 {count} 条快照到数据库")

    def get_comparison(self, today: str, yesterday: str) -> list[dict]:
        """获取今天与昨天的对比数据

        Returns:
            list of {
                "asin", "url", "title",
                "rating_today", "rating_yesterday", "rating_change",
                "reviews_today", "reviews_yesterday", "reviews_change",
                "is_new", "has_error"
            }
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    p.asin, p.url, p.title,
                    t.rating AS rating_today,
                    t.review_count AS reviews_today,
                    y.rating AS rating_yesterday,
                    y.review_count AS reviews_yesterday
                FROM products p
                LEFT JOIN snapshots t ON p.asin = t.asin AND t.date = ?
                LEFT JOIN snapshots y ON p.asin = y.asin AND y.date = ?
                WHERE p.enabled = 1
                ORDER BY p.asin
                """,
                (today, yesterday),
            ).fetchall()

        result = []
        for row in rows:
            r = dict(row)
            r["is_new"] = r["rating_yesterday"] is None and r["reviews_yesterday"] is None
            r["has_error"] = r["rating_today"] is None and r["reviews_today"] is None

            if r["rating_today"] is not None and r["rating_yesterday"] is not None:
                r["rating_change"] = round(r["rating_today"] - r["rating_yesterday"], 2)
            else:
                r["rating_change"] = None

            if r["reviews_today"] is not None and r["reviews_yesterday"] is not None:
                r["reviews_change"] = r["reviews_today"] - r["reviews_yesterday"]
            else:
                r["reviews_change"] = None

            result.append(r)

        return result

    def get_last_snapshot_date(self) -> str | None:
        """获取最近一次快照的日期"""
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute("SELECT MAX(date) FROM snapshots").fetchone()
            return row[0] if row and row[0] else None

    def get_enabled_products_count(self) -> int:
        """获取启用的产品数量"""
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute("SELECT COUNT(*) FROM products WHERE enabled = 1").fetchone()
            return row[0] if row else 0
