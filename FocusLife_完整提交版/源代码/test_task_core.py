import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from task_core import (
    AppData, Habit, Profile, Review, Task, TaskStore,
    calculate_debt, can_add_today_task, habit_completion_rate,
    month_summary, priority_score, self_discipline_score,
)


class FocusLifeCoreTests(unittest.TestCase):
    def test_overdue_important_task_has_high_priority(self):
        today = date(2026, 8, 20)
        urgent = Task("交期末作业", (today - timedelta(days=1)).isoformat(), 5, 5, 90)
        later = Task("整理桌面", (today + timedelta(days=7)).isoformat(), 2, 1, 20)
        self.assertGreater(priority_score(urgent, today), priority_score(later, today))

    def test_today_limit_rejects_fourth_active_task(self):
        today = date(2026, 8, 20)
        tasks = [Task(f"任务{i}", today.isoformat()) for i in range(3)]
        self.assertFalse(can_add_today_task(tasks, today))
        tasks[0].completed = True
        self.assertTrue(can_add_today_task(tasks, today))

    def test_habit_checkin_is_idempotent(self):
        habit = Habit("早起")
        self.assertTrue(habit.check_in("2026-08-20"))
        self.assertFalse(habit.check_in("2026-08-20"))
        self.assertEqual(habit.checkins, ["2026-08-20"])

    def test_debt_counts_overdue_tasks(self):
        today = date(2026, 8, 20)
        tasks = [
            Task("拖延1", "2026-08-18"),
            Task("拖延2", "2026-08-19"),
            Task("今天", "2026-08-20"),
        ]
        self.assertEqual(calculate_debt(tasks, today), 2)

    def test_energy_score_is_bounded(self):
        score = self_discipline_score(4, 3, 90, 60, 1.0, True)
        self.assertEqual(score, 100)
        self.assertEqual(self_discipline_score(0, 3, 0, 60, 0.0, False), 0)

    def test_month_summary_groups_completion_dates(self):
        tasks = [Task("完成", "2026-08-01", completed=True, completed_at="2026-08-03T09:00:00")]
        self.assertEqual(month_summary(tasks, 2026, 8)["2026-08-03"], 1)

    def test_habit_completion_rate(self):
        habit = Habit("阅读", checkins=["2026-08-18", "2026-08-20"])
        self.assertAlmostEqual(habit_completion_rate([habit], date(2026, 8, 20), 3), 2 / 3)

    def test_profile_completion_is_idempotent_per_task(self):
        profile = Profile()
        self.assertTrue(profile.add_completion("abc", 25, date(2026, 8, 20)))
        self.assertFalse(profile.add_completion("abc", 25, date(2026, 8, 20)))
        self.assertEqual(profile.completed_count, 1)

    def test_store_round_trip_and_legacy_migration(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            store = TaskStore(path)
            data = AppData(
                tasks=[Task("阅读", "2026-08-22")],
                habits=[Habit("喝水", checkins=["2026-08-20"])],
                reviews=[Review("2026-08-20", "完成", "无", "继续")],
            )
            store.save(data)
            restored = store.load()
            self.assertEqual(restored.habits[0].name, "喝水")
            path.write_text('{"tasks": [], "profile": {"experience": 40}}', encoding="utf-8")
            legacy = store.load()
            self.assertEqual(legacy.profile.experience, 40)


if __name__ == "__main__":
    unittest.main()
