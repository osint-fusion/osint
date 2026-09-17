import sqlite3
import json
import os
from datetime import datetime

class Database:
    def __init__(self, db_path="data/osint_fusion.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id TEXT PRIMARY KEY,
                    target_type TEXT NOT NULL,
                    target TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    execution_time REAL,
                    findings_count INTEGER DEFAULT 0,
                    raw_output TEXT,
                    parsed_results TEXT,
                    error_message TEXT,
                    FOREIGN KEY (scan_id) REFERENCES scans (id)
                )
            """)
            conn.commit()

    def create_scan(self, scan_id: str, target_type: str, target: str):
        with self._get_connection() as conn:
            conn.cursor().execute(
                "INSERT INTO scans (id, target_type, target, status) VALUES (?, ?, ?, ?)",
                (scan_id, target_type, target, "running")
            )
            conn.commit()

    def update_scan_status(self, scan_id: str, status: str):
        with self._get_connection() as conn:
            conn.cursor().execute(
                "UPDATE scans SET status = ?, completed_at = ? WHERE id = ?",
                (status, datetime.utcnow().isoformat(), scan_id)
            )
            conn.commit()

    def save_tool_result(self, scan_id: str, tool_name: str, status: str, exec_time: float, findings_count: int, raw_output: str, parsed_results: list, error_msg: str = None):
        with self._get_connection() as conn:
            conn.cursor().execute(
                """INSERT INTO tool_results 
                   (scan_id, tool_name, status, execution_time, findings_count, raw_output, parsed_results, error_message)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (scan_id, tool_name, status, exec_time, findings_count, raw_output, json.dumps(parsed_results, ensure_ascii=False), error_msg)
            )
            conn.commit()

    def get_scan(self, scan_id: str):
        with self._get_connection() as conn:
            scan = conn.cursor().execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
            if not scan:
                return None
            results = conn.cursor().execute("SELECT * FROM tool_results WHERE scan_id = ?", (scan_id,)).fetchall()
            
            scan_dict = dict(scan)
            scan_dict['results'] = []
            for r in results:
                res_dict = dict(r)
                res_dict['parsed_results'] = json.loads(res_dict['parsed_results']) if res_dict['parsed_results'] else []
                scan_dict['results'].append(res_dict)
            return scan_dict

    def get_history(self, limit=20):
        with self._get_connection() as conn:
            scans = conn.cursor().execute(
                "SELECT * FROM scans ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(s) for s in scans]

    def delete_scan(self, scan_id: str):
        with self._get_connection() as conn:
            conn.cursor().execute("DELETE FROM tool_results WHERE scan_id = ?", (scan_id,))
            conn.cursor().execute("DELETE FROM scans WHERE id = ?", (scan_id,))
            conn.commit()