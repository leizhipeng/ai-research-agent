"""SQLite artifacts and operational records; graph checkpoints share the database."""

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from research_agent.models.workflow import ResearchRequest


class BudgetExceeded(RuntimeError):
    pass


class ControlRequested(RuntimeError):
    pass


class Store:
    def __init__(self, db: str | Path):
        self.path = str(Path(db).expanduser().resolve())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, data TEXT NOT NULL, owner INTEGER);
                CREATE TABLE IF NOT EXISTS artifacts (
                    run_id TEXT, key TEXT, data TEXT NOT NULL, PRIMARY KEY(run_id,key));
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY, run_id TEXT, time REAL, stage TEXT,
                    kind TEXT, data TEXT);
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY, expires REAL, data TEXT);
            """)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=30)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def create(self, request: ResearchRequest) -> str:
        run_id = "research-" + uuid4().hex[:12]
        data = dict(
            run_id=run_id,
            request=request.model_dump(mode="json"),
            status="pending",
            stage="plan",
            reason="",
            control="continue",
            created_at=time.time(),
            active_seconds=0.0,
            session_started=None,
            usage=dict(
                model_calls=0,
                tokens=0,
                reserved_tokens=0,
                http_requests=0,
                download_bytes=0,
                cache_hits=0,
            ),
        )
        with self.connect() as conn:
            conn.execute("INSERT INTO runs VALUES (?,?,NULL)", (run_id, json.dumps(data)))
        return run_id

    def get_run(self, run_id: str) -> dict:
        with self.connect() as conn:
            row = conn.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            raise ValueError(f"unknown run: {run_id}")
        return json.loads(row[0])

    def update(self, run_id: str, **changes):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                raise ValueError(f"unknown run: {run_id}")
            data = json.loads(row[0])
            data.update(changes)
            conn.execute("UPDATE runs SET data=? WHERE id=?", (json.dumps(data), run_id))

    def acquire(self, run_id: str):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            owner, raw = conn.execute(
                "SELECT owner,data FROM runs WHERE id=?", (run_id,)
            ).fetchone()
            if owner:
                try:
                    os.kill(owner, 0)
                except ProcessLookupError:
                    pass
                else:
                    raise ValueError(f"run is already active in process {owner}")
            data = json.loads(raw)
            if data["session_started"]:
                # An unclean stop has no reliable end timestamp. Charge until recovery conservatively.
                data["active_seconds"] += max(0, time.time() - data["session_started"])
            data.update(status="running", session_started=time.time())
            conn.execute(
                "UPDATE runs SET owner=?,data=? WHERE id=?", (os.getpid(), json.dumps(data), run_id)
            )

    def release(self, run_id: str):
        data = self.get_run(run_id)
        elapsed = max(0, time.time() - data["session_started"]) if data["session_started"] else 0
        self.update(run_id, active_seconds=data["active_seconds"] + elapsed, session_started=None)
        with self.connect() as conn:
            conn.execute("UPDATE runs SET owner=NULL WHERE id=?", (run_id,))

    def guard(self, run_id: str):
        data = self.get_run(run_id)
        if data["control"] != "continue":
            raise ControlRequested(data["control"])
        elapsed = data["active_seconds"]
        if data["session_started"]:
            elapsed += max(0, time.time() - data["session_started"])
        if elapsed >= data["request"]["limits"]["max_seconds"]:
            raise BudgetExceeded("active elapsed time limit reached")

    def remaining_seconds(self, run_id: str) -> float:
        data = self.get_run(run_id)
        elapsed = data["active_seconds"]
        if data["session_started"]:
            elapsed += max(0, time.time() - data["session_started"])
        return max(0.001, data["request"]["limits"]["max_seconds"] - elapsed)

    def consume(
        self,
        run_id: str,
        counter: str,
        amount: int,
        limit: str | None = None,
        *,
        actual: bool = False,
    ):
        if not actual:
            self.guard(run_id)
        exceeded = False
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            data = json.loads(
                conn.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()[0]
            )
            value = data["usage"][counter] + amount
            if limit and value > data["request"]["limits"][limit]:
                if not actual:
                    raise BudgetExceeded(f"{limit} reached")
                exceeded = True
            data["usage"][counter] = value
            conn.execute("UPDATE runs SET data=? WHERE id=?", (json.dumps(data), run_id))
        if exceeded:
            raise BudgetExceeded(f"{limit} reached")
        self.guard(run_id)

    def put(self, run_id: str, key: str, data):
        self.put_many(run_id, {key: data})

    def reserve_model(self, run_id: str, tokens: int):
        self.guard(run_id)
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            data = json.loads(
                conn.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()[0]
            )
            limits = data["request"]["limits"]
            if data["usage"]["model_calls"] + 1 > limits["max_model_calls"]:
                raise BudgetExceeded("max_model_calls reached")
            if data["usage"]["reserved_tokens"] + tokens > limits["max_tokens"]:
                raise BudgetExceeded("max_tokens reached")
            data["usage"]["model_calls"] += 1
            data["usage"]["reserved_tokens"] += tokens
            conn.execute("UPDATE runs SET data=? WHERE id=?", (json.dumps(data), run_id))

    def put_many(self, run_id: str, items: dict):
        with self.connect() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO artifacts VALUES (?,?,?)",
                [
                    (run_id, key, json.dumps(data, ensure_ascii=False))
                    for key, data in items.items()
                ],
            )

    def get(self, run_id: str, key: str):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT data FROM artifacts WHERE run_id=? AND key=?", (run_id, key)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def event(self, run_id: str, stage: str, kind: str, data):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO events (run_id,time,stage,kind,data) VALUES (?,?,?,?,?)",
                (run_id, time.time(), stage, kind, json.dumps(data)),
            )

    def control(self, run_id: str, action: str):
        if action not in {"continue", "pause", "cancel"}:
            raise ValueError("control must be continue, pause, or cancel")
        if action != "continue" and self.get_run(run_id)["status"] in {
            "completed",
            "partial",
            "halted",
        }:
            raise ValueError("a finished run cannot be paused or cancelled")
        self.update(run_id, control=action)
        self.event(run_id, "control", action, {})
        with self.connect() as conn:
            owner = conn.execute("SELECT owner FROM runs WHERE id=?", (run_id,)).fetchone()[0]
        if not owner and action in {"pause", "cancel"}:
            self.update(run_id, status="paused" if action == "pause" else "halted", reason=action)
        return self.get_run(run_id)

    def list_runs(self) -> list[dict]:
        with self.connect() as conn:
            return [
                json.loads(row[0])
                for row in conn.execute("SELECT data FROM runs ORDER BY rowid DESC")
            ]

    def inspect(self, run_id: str) -> dict:
        with self.connect() as conn:
            artifacts = {
                k: json.loads(v)
                for k, v in conn.execute(
                    "SELECT key,data FROM artifacts WHERE run_id=? ORDER BY key", (run_id,)
                )
            }
            events = [
                dict(id=i, time=t, stage=s, kind=k, data=json.loads(d))
                for i, t, s, k, d in conn.execute(
                    "SELECT id,time,stage,kind,data FROM events WHERE run_id=? ORDER BY id",
                    (run_id,),
                )
            ]
        return dict(run=self.get_run(run_id), artifacts=artifacts, events=events)

    def cache_get(self, key: str):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT data FROM cache WHERE key=? AND expires>?", (key, time.time())
            ).fetchone()
        return json.loads(row[0]) if row else None

    def cache_set(self, key: str, data):
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache VALUES (?,?,?)",
                (key, time.time() + 86400, json.dumps(data)),
            )

    def export(self, run_id: str, directory: str | Path) -> dict:
        data = self.inspect(run_id)
        target = Path(directory).expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)
        (target / "artifacts.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        )
        report = data["artifacts"].get("report")
        if report:
            (target / "report.md").write_text(report["markdown"])
        return {
            "artifacts": str(target / "artifacts.json"),
            "report": str(target / "report.md") if report else None,
        }
