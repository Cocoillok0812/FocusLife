"""FocusLife 自律管家：基于原任务启动器增量升级的 Tkinter 单机应用。"""
from __future__ import annotations

import calendar
import os
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from task_core import (
    AppData, Habit, Review, Task, TaskStore, calculate_debt,
    can_add_today_task, habit_completion_rate, make_two_minute_action,
    month_summary, priority_score, self_discipline_score, seven_day_stats,
)


BG, PANEL, CARD = "#0B0F0D", "#111813", "#172019"
NEON, BLUE, TEXT, MUTED, DANGER = "#B7FF4A", "#7C8CFF", "#F4F7F2", "#8E9B91", "#FF6B6B"


def data_path() -> Path:
    return Path(os.getenv("LOCALAPPDATA", Path.home())) / "FocusLife" / "focuslife.json"


class FocusLifeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("FocusLife · 自律管家")
        self.geometry("1180x760")
        self.minsize(1050, 680)
        self.configure(bg=BG)
        self.store = TaskStore(data_path())
        self.data = self.store.load()
        self.current_task: Task | None = None
        self.timer_job: str | None = None
        self.timer_seconds = 0
        self.timer_total_minutes = 0
        self.timer_paused = False
        self._setup_style()
        self._build_shell()
        self.show_today()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Microsoft YaHei UI", 10))
        style.configure("Nav.TButton", background=PANEL, foreground=TEXT, padding=(16, 12), anchor="w")
        style.map("Nav.TButton", background=[("active", CARD)])
        style.configure("Accent.TButton", background=NEON, foreground="#101510", padding=(13, 9), font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#D1FF8B")])
        style.configure("Soft.TButton", background=CARD, foreground=TEXT, padding=(12, 8))
        style.map("Soft.TButton", background=[("active", "#243028")])
        style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT, rowheight=34, borderwidth=0)
        style.configure("Treeview.Heading", background=PANEL, foreground=MUTED, relief="flat")
        style.map("Treeview", background=[("selected", "#334522")], foreground=[("selected", TEXT)])

    def _build_shell(self) -> None:
        sidebar = tk.Frame(self, bg=PANEL, width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="FOCUSLIFE", bg=PANEL, fg=NEON, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=22, pady=(28, 2))
        tk.Label(sidebar, text="自律管家", bg=PANEL, fg=MUTED).pack(anchor="w", padx=22, pady=(0, 24))
        for title, command in [
            ("今日仪表盘", self.show_today), ("习惯打卡", self.show_habits),
            ("月历", self.show_calendar), ("晚间复盘", self.show_review), ("数据中心", self.show_data),
        ]:
            ttk.Button(sidebar, text=title, style="Nav.TButton", command=command).pack(fill="x", padx=12, pady=3)
        tk.Label(sidebar, text="数据只保存在本机", bg=PANEL, fg=MUTED, font=("Microsoft YaHei UI", 8)).pack(side="bottom", pady=18)
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="right", fill="both", expand=True)

    def _clear(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()

    def _heading(self, title: str, subtitle: str) -> tk.Frame:
        header = tk.Frame(self.content, bg=BG)
        header.pack(fill="x", padx=30, pady=(26, 16))
        tk.Label(header, text=title, bg=BG, fg=TEXT, font=("Microsoft YaHei UI", 24, "bold")).pack(anchor="w")
        tk.Label(header, text=subtitle, bg=BG, fg=MUTED).pack(anchor="w", pady=(5, 0))
        return header

    def _card(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground="#263129")

    def _save(self) -> None:
        self.store.save(self.data)

    def _today_metrics(self) -> tuple[int, int, int, int]:
        today = date.today().isoformat()
        planned = sum(1 for task in self.data.tasks if task.due_date == today)
        done = sum(1 for task in self.data.tasks if task.completed_at and task.completed_at.startswith(today))
        focus = sum(int(s.get("minutes", 0)) for s in self.data.focus_sessions if s.get("date") == today)
        reviewed = any(review.review_date == today for review in self.data.reviews)
        score = self_discipline_score(done, planned, focus, 60, habit_completion_rate(self.data.habits, days=1), reviewed)
        return planned, done, focus, score

    def show_today(self) -> None:
        self._clear()
        quotes = ["先完成，再完美。", "今天的三件事，值得被认真完成。", "专注不是坚持很久，而是一次只做一件事。"]
        self._heading("今日仪表盘", quotes[date.today().toordinal() % len(quotes)])
        metrics = tk.Frame(self.content, bg=BG)
        metrics.pack(fill="x", padx=25)
        planned, done, focus, score = self._today_metrics()
        values = [("今日任务", f"{done}/{planned}"), ("专注分钟", str(focus)), ("拖延欠债", str(calculate_debt(self.data.tasks))), ("自律能量", f"{score}/100")]
        for name, value in values:
            card = self._card(metrics); card.pack(side="left", fill="x", expand=True, padx=5)
            tk.Label(card, text=name, bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=(13, 4))
            tk.Label(card, text=value, bg=CARD, fg=NEON, font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=16, pady=(0, 14))
        body = tk.Frame(self.content, bg=BG); body.pack(fill="both", expand=True, padx=30, pady=18)
        left = self._card(body); left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = self._card(body); right.pack(side="right", fill="y", ipadx=8); right.configure(width=300); right.pack_propagate(False)
        top = tk.Frame(left, bg=CARD); top.pack(fill="x", padx=18, pady=16)
        tk.Label(top, text="今天只做三件事", bg=CARD, fg=TEXT, font=("Microsoft YaHei UI", 15, "bold")).pack(side="left")
        ttk.Button(top, text="＋ 新任务", style="Accent.TButton", command=self.add_task).pack(side="right")
        self.task_tree = ttk.Treeview(left, columns=("task", "priority", "time", "state"), show="headings")
        for key, text, width in [("task", "任务", 310), ("priority", "优先值", 80), ("time", "分钟", 70), ("state", "状态", 80)]:
            self.task_tree.heading(key, text=text); self.task_tree.column(key, width=width, anchor="w" if key == "task" else "center")
        self.task_tree.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        today_tasks = sorted([t for t in self.data.tasks if t.due_date == date.today().isoformat()], key=priority_score, reverse=True)
        for task in today_tasks:
            self.task_tree.insert("", "end", iid=task.id, values=(task.title, f"{priority_score(task):.1f}", task.estimate_minutes, "已完成" if task.completed else "待完成"))
        self.task_tree.bind("<<TreeviewSelect>>", self._select_task)
        bar = tk.Frame(left, bg=CARD); bar.pack(fill="x", padx=18, pady=(0, 16))
        ttk.Button(bar, text="✓ 标记完成", style="Soft.TButton", command=self.complete_task).pack(side="left")
        ttk.Button(bar, text="删除", style="Soft.TButton", command=self.delete_task).pack(side="left", padx=6)
        tk.Label(right, text="专注启动", bg=CARD, fg=TEXT, font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=18, pady=(22, 8))
        self.action_label = tk.Label(right, text="选择任务后，会生成一个两分钟起步动作。", wraplength=250, justify="left", bg="#1D291F", fg=NEON, padx=14, pady=14)
        self.action_label.pack(fill="x", padx=18)
        tk.Label(right, text="选择时长", bg=CARD, fg=MUTED).pack(anchor="w", padx=18, pady=(22, 8))
        for minutes in (2, 25, 45, 60):
            ttk.Button(right, text=f"{minutes} 分钟", style="Soft.TButton", command=lambda m=minutes: self.start_focus(m)).pack(fill="x", padx=18, pady=4)

    def _select_task(self, _event=None) -> None:
        selected = self.task_tree.selection()
        self.current_task = next((task for task in self.data.tasks if selected and task.id == selected[0]), None)
        if self.current_task:
            self.action_label.config(text=make_two_minute_action(self.current_task.title))

    def add_task(self) -> None:
        if not can_add_today_task(self.data.tasks):
            messagebox.showwarning("今日已满", "今天最多保留 3 项未完成任务。先完成一项再添加。")
            return
        title = simpledialog.askstring("新建今日任务", "任务名称：", parent=self)
        if not title:
            return
        minutes = simpledialog.askinteger("预计用时", "预计分钟数：", initialvalue=25, minvalue=1, maxvalue=480, parent=self)
        if minutes is None:
            return
        task = Task(title.strip(), date.today().isoformat(), estimate_minutes=minutes)
        task.validate(); self.data.tasks.append(task); self._save(); self.show_today()

    def _selected_task(self) -> Task | None:
        selected = self.task_tree.selection() if hasattr(self, "task_tree") else ()
        return next((task for task in self.data.tasks if selected and task.id == selected[0]), self.current_task)

    def complete_task(self) -> None:
        task = self._selected_task()
        if not task or task.completed:
            return
        task.completed = True; task.completed_at = datetime.now().isoformat(timespec="seconds")
        self.data.profile.add_completion(task.id, min(task.estimate_minutes, 25))
        self._save(); self.current_task = None; self.show_today()

    def delete_task(self) -> None:
        task = self._selected_task()
        if task and messagebox.askyesno("删除任务", f"确定删除“{task.title}”吗？"):
            self.data.tasks.remove(task); self.current_task = None; self._save(); self.show_today()

    def start_focus(self, minutes: int) -> None:
        task = self._selected_task()
        if not task:
            messagebox.showinfo("先选任务", "请先在左侧选择一项任务。")
            return
        self.timer_total_minutes = minutes; self.timer_seconds = minutes * 60; self.timer_paused = False
        win = tk.Toplevel(self); self.focus_window = win; win.title("专注中"); win.configure(bg=BG); win.geometry("640x420"); win.transient(self)
        tk.Label(win, text=task.title, bg=BG, fg=TEXT, font=("Microsoft YaHei UI", 18, "bold")).pack(pady=(55, 10))
        self.timer_label = tk.Label(win, text="", bg=BG, fg=NEON, font=("Consolas", 64, "bold")); self.timer_label.pack(pady=25)
        row = tk.Frame(win, bg=BG); row.pack()
        ttk.Button(row, text="暂停/继续", style="Soft.TButton", command=self._toggle_focus).pack(side="left", padx=5)
        ttk.Button(row, text="结束专注", style="Soft.TButton", command=lambda: self._finish_focus(False)).pack(side="left", padx=5)
        win.protocol("WM_DELETE_WINDOW", lambda: self._finish_focus(False)); self._focus_tick()

    def _focus_tick(self) -> None:
        if self.timer_paused or not getattr(self, "focus_window", None):
            return
        minutes, seconds = divmod(self.timer_seconds, 60); self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
        if self.timer_seconds <= 0:
            self._finish_focus(True); return
        self.timer_seconds -= 1; self.timer_job = self.after(1000, self._focus_tick)

    def _toggle_focus(self) -> None:
        self.timer_paused = not self.timer_paused
        if not self.timer_paused:
            self._focus_tick()

    def _finish_focus(self, completed: bool) -> None:
        if self.timer_job:
            self.after_cancel(self.timer_job); self.timer_job = None
        win = getattr(self, "focus_window", None); self.focus_window = None
        if win and win.winfo_exists(): win.destroy()
        elapsed = self.timer_total_minutes if completed else max(0, (self.timer_total_minutes * 60 - self.timer_seconds) // 60)
        if elapsed:
            self.data.focus_sessions.append({"date": date.today().isoformat(), "minutes": elapsed, "task_id": self.current_task.id if self.current_task else ""})
            self.data.profile.focus_minutes += elapsed; self._save()
        if completed:
            self.bell(); messagebox.showinfo("专注完成", f"已记录 {elapsed} 分钟专注。")
        self.show_today()

    def show_habits(self) -> None:
        self._clear(); header = self._heading("习惯打卡", "小习惯用完成率积累长期确定感。")
        ttk.Button(header, text="＋ 新习惯", style="Accent.TButton", command=self.add_habit).pack(side="right")
        area = tk.Frame(self.content, bg=BG); area.pack(fill="both", expand=True, padx=30)
        today = date.today().isoformat()
        for habit in self.data.habits:
            card = self._card(area); card.pack(fill="x", pady=6)
            tk.Label(card, text=habit.name, bg=CARD, fg=TEXT, font=("Microsoft YaHei UI", 14, "bold")).pack(side="left", padx=18, pady=18)
            checked = today in habit.checkins
            ttk.Button(card, text="今日已完成" if checked else "今日打卡", style="Soft.TButton", state="disabled" if checked else "normal", command=lambda h=habit: self.check_habit(h)).pack(side="right", padx=18)
        if not self.data.habits:
            tk.Label(area, text="还没有习惯，先添加一个容易做到的小习惯。", bg=BG, fg=MUTED).pack(pady=60)

    def add_habit(self) -> None:
        name = simpledialog.askstring("新习惯", "习惯名称：", parent=self)
        if name and name.strip(): self.data.habits.append(Habit(name.strip())); self._save(); self.show_habits()

    def check_habit(self, habit: Habit) -> None:
        habit.check_in(); self._save(); self.show_habits()

    def show_calendar(self) -> None:
        self._clear(); today = date.today(); self._heading("月历", f"{today.year} 年 {today.month} 月完成记录")
        area = self._card(self.content); area.pack(fill="both", expand=True, padx=30, pady=(0, 25))
        summary = month_summary(self.data.tasks, today.year, today.month)
        for col, name in enumerate("一二三四五六日"):
            tk.Label(area, text=name, bg=CARD, fg=MUTED, width=12).grid(row=0, column=col, padx=4, pady=10, sticky="nsew")
            area.grid_columnconfigure(col, weight=1)
        for row, week in enumerate(calendar.monthcalendar(today.year, today.month), start=1):
            for col, day in enumerate(week):
                if not day: continue
                key = f"{today.year:04d}-{today.month:02d}-{day:02d}"; count = summary.get(key, 0)
                text = f"{day}\n{count} 项完成" if count else str(day)
                tk.Label(area, text=text, bg="#24411F" if count else PANEL, fg=NEON if count else TEXT, height=4).grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

    def show_review(self) -> None:
        self._clear(); self._heading("晚间复盘", "三句话结束今天，也为明天减轻启动阻力。")
        form = self._card(self.content); form.pack(fill="both", expand=True, padx=30, pady=(0, 25))
        existing = next((r for r in self.data.reviews if r.review_date == date.today().isoformat()), None)
        entries: list[tk.Text] = []
        for prompt, value in [("今天完成了什么？", existing.completed if existing else ""), ("最大的阻碍是什么？", existing.obstacle if existing else ""), ("明天最重要的一件事？", existing.tomorrow if existing else "")]:
            tk.Label(form, text=prompt, bg=CARD, fg=TEXT, font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=26, pady=(20, 6))
            box = tk.Text(form, height=3, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat", padx=10, pady=8); box.insert("1.0", value); box.pack(fill="x", padx=26); entries.append(box)
        ttk.Button(form, text="保存今日复盘", style="Accent.TButton", command=lambda: self.save_review(entries)).pack(anchor="e", padx=26, pady=22)

    def save_review(self, entries: list[tk.Text]) -> None:
        values = [box.get("1.0", "end").strip() for box in entries]
        today = date.today().isoformat(); self.data.reviews = [r for r in self.data.reviews if r.review_date != today]
        self.data.reviews.append(Review(today, *values)); self._save(); messagebox.showinfo("已保存", "今日复盘已经保存。")

    def show_data(self) -> None:
        self._clear(); header = self._heading("数据中心", "用趋势观察自己，不用单次表现评价自己。")
        ttk.Button(header, text="导出备份", style="Soft.TButton", command=self.export_data).pack(side="right")
        planned, done, focus, score = self._today_metrics()
        card = self._card(self.content); card.pack(fill="x", padx=30)
        tk.Label(card, text=f"本周习惯完成率  {habit_completion_rate(self.data.habits) * 100:.0f}%   ·   当前连续行动 {self.data.profile.streak} 天   ·   自律能量 {score}", bg=CARD, fg=NEON, font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", padx=20, pady=20)
        canvas = tk.Canvas(self.content, bg=CARD, highlightthickness=0, height=280); canvas.pack(fill="x", padx=30, pady=16)
        stats = seven_day_stats(self.data.profile.history)
        maximum = max(60, max((item["minutes"] for item in stats), default=0))
        for index, item in enumerate(stats):
            x = 60 + index * 125; height = 180 * item["minutes"] / maximum
            canvas.create_rectangle(x, 225 - height, x + 58, 225, fill=BLUE, outline="")
            canvas.create_text(x + 29, 245, text=item["date"][5:], fill=MUTED)
            canvas.create_text(x + 29, 215 - height, text=str(item["minutes"]), fill=TEXT)

    def export_data(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON 备份", "*.json")])
        if path: TaskStore(path).save(self.data); messagebox.showinfo("导出完成", "数据备份已经生成。")

    def _close(self) -> None:
        self._save(); self.destroy()


if __name__ == "__main__":
    FocusLifeApp().mainloop()
