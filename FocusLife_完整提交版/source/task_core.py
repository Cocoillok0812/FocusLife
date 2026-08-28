"""FocusLife 的领域模型与本地持久化。"""
from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path


def _id() -> str:
    return uuid.uuid4().hex[:10]


@dataclass
class Task:
    title: str
    due_date: str
    importance: int = 3
    difficulty: int = 3
    estimate_minutes: int = 25
    id: str = field(default_factory=_id)
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    completed_at: str | None = None

    def validate(self) -> None:
        if not self.title.strip():
            raise ValueError("任务名称不能为空")
        date.fromisoformat(self.due_date)
        if not 1 <= self.importance <= 5 or not 1 <= self.difficulty <= 5:
            raise ValueError("重要度和难度必须为 1 到 5")
        if self.estimate_minutes <= 0:
            raise ValueError("预计用时必须大于 0")


@dataclass
class Habit:
    name: str
    id: str = field(default_factory=_id)
    created_at: str = field(default_factory=lambda: date.today().isoformat())
    checkins: list[str] = field(default_factory=list)

    def check_in(self, day: str | None = None) -> bool:
        day = day or date.today().isoformat()
        date.fromisoformat(day)
        if day in self.checkins:
            return False
        self.checkins.append(day)
        self.checkins.sort()
        return True


@dataclass
class Review:
    review_date: str
    completed: str
    obstacle: str
    tomorrow: str


@dataclass
class Profile:
    experience: int = 0
    completed_count: int = 0
    focus_minutes: int = 0
    streak: int = 0
    history: list[dict] = field(default_factory=list)
    rewarded_task_ids: list[str] = field(default_factory=list)

    @property
    def level(self) -> int:
        return self.experience // 100 + 1

    def add_completion(self, task_id: str, focus_minutes: int = 0, today: date | None = None) -> bool:
        if task_id in self.rewarded_task_ids:
            return False
        today = today or date.today()
        minutes = max(0, focus_minutes)
        self.rewarded_task_ids.append(task_id)
        self.completed_count += 1
        self.focus_minutes += minutes
        self.experience += 20 + min(minutes, 60)
        today_text = today.isoformat()
        dates = {item.get("date") for item in self.history}
        if today_text not in dates:
            yesterday = (today - timedelta(days=1)).isoformat()
            self.streak = self.streak + 1 if yesterday in dates else 1
        self.history.append({"date": today_text, "minutes": minutes, "task_id": task_id})
        return True


@dataclass
class AppData:
    tasks: list[Task] = field(default_factory=list)
    profile: Profile = field(default_factory=Profile)
    habits: list[Habit] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    focus_sessions: list[dict] = field(default_factory=list)
    schema_version: int = 2


def priority_score(task: Task, today: date | None = None) -> float:
    today = today or date.today()
    days = (date.fromisoformat(task.due_date) - today).days
    urgency = 12 if days < 0 else 10 if days == 0 else max(0, 8 - days)
    return round(task.importance * 4 + task.difficulty * 1.2 + urgency - min(task.estimate_minutes / 120, 2), 2)


def make_two_minute_action(title: str) -> str:
    clean = re.sub(r"[，。！？,.!]+", "", title.strip()) or "当前任务"
    if any(word in clean for word in ("PPT", "报告", "作业", "文档")):
        return f"打开相关文件，用 2 分钟写下“{clean}”的第一个小标题"
    if any(word in clean for word in ("背", "复习", "阅读", "学习")):
        return f"打开学习材料，用 2 分钟完成“{clean}”的第一小段"
    return f"打开需要的材料，用 2 分钟完成“{clean}”的第一个最小步骤"


def can_add_today_task(tasks: list[Task], today: date | None = None, limit: int = 3) -> bool:
    today_text = (today or date.today()).isoformat()
    active = sum(1 for task in tasks if not task.completed and task.due_date == today_text)
    return active < limit


def calculate_debt(tasks: list[Task], today: date | None = None) -> int:
    today_text = (today or date.today()).isoformat()
    return sum(1 for task in tasks if not task.completed and task.due_date < today_text)


def habit_completion_rate(habits: list[Habit], today: date | None = None, days: int = 7) -> float:
    if not habits or days <= 0:
        return 0.0
    today = today or date.today()
    allowed = {(today - timedelta(days=offset)).isoformat() for offset in range(days)}
    done = sum(1 for habit in habits for day in set(habit.checkins) if day in allowed)
    return min(1.0, done / (len(habits) * days))


def self_discipline_score(done: int, planned: int, focus: int, focus_goal: int, habit_rate: float, reviewed: bool) -> int:
    task_part = min(1.0, done / max(1, planned)) * 40 if planned else 0
    focus_part = min(1.0, focus / max(1, focus_goal)) * 30
    habit_part = max(0.0, min(1.0, habit_rate)) * 20
    review_part = 10 if reviewed else 0
    return max(0, min(100, round(task_part + focus_part + habit_part + review_part)))


def month_summary(tasks: list[Task], year: int, month: int) -> dict[str, int]:
    prefix = f"{year:04d}-{month:02d}-"
    result: dict[str, int] = {}
    for task in tasks:
        if task.completed_at and task.completed_at.startswith(prefix):
            day = task.completed_at[:10]
            result[day] = result.get(day, 0) + 1
    return result


def seven_day_stats(history: list[dict], today: date | None = None) -> list[dict]:
    today = today or date.today()
    totals: dict[str, int] = {}
    for item in history:
        key = str(item.get("date", ""))
        totals[key] = totals.get(key, 0) + int(item.get("minutes", 0))
    return [{"date": (today - timedelta(days=i)).isoformat(), "minutes": totals.get((today - timedelta(days=i)).isoformat(), 0)} for i in range(6, -1, -1)]


class TaskStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, data: AppData, profile: Profile | None = None) -> None:
        if isinstance(data, list):  # 兼容旧 UI 调用形式 save(tasks, profile)
            data = AppData(tasks=data, profile=profile or Profile())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(asdict(data), ensure_ascii=False, indent=2)
        fd, temp_name = tempfile.mkstemp(prefix="focuslife_", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def load(self) -> AppData:
        if not self.path.exists():
            return AppData()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            tasks = [Task(**item) for item in raw.get("tasks", [])]
            for task in tasks:
                task.validate()
            profile_raw = raw.get("profile", {})
            profile_fields = {key: value for key, value in profile_raw.items() if key in Profile.__dataclass_fields__}
            return AppData(
                tasks=tasks,
                profile=Profile(**profile_fields),
                habits=[Habit(**item) for item in raw.get("habits", [])],
                reviews=[Review(**item) for item in raw.get("reviews", [])],
                focus_sessions=list(raw.get("focus_sessions", [])),
                schema_version=int(raw.get("schema_version", 2)),
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            backup = self.path.with_suffix(".broken.json")
            try:
                self.path.replace(backup)
            except OSError:
                pass
            return AppData()
