# FocusLife 升级规格

## Goal
在现有 Tkinter 任务启动器上增量升级为“自律管家 FocusLife”，保留优先级、两分钟行动、计时和 JSON 本地存储。

## Inputs / Outputs
- 输入：任务、习惯打卡、专注时长、晚间复盘。
- 输出：今日三项任务、拖延欠债、月历完成状态、周统计和 0–100 自律能量值。

## Constraints
- Python 3.10+，Tkinter，标准库优先，Windows 单机运行。
- 兼容旧版 tasks.json；所有数据采用原子写入。
- 今日未完成任务最多 3 项；专注时长支持 2/25/45/60 分钟。
- 不上传密码、用户本地数据或任何凭据。

## Edge Cases
- 空文件、损坏 JSON、旧数据缺字段、重复完成、同日重复打卡、删除当前任务。

## Out of Scope
- 云同步、联网账号体系、多人协作、手机端。

## Acceptance Criteria
- 旧数据可加载；新增数据可完整往返保存。
- 今日任务限制、欠债计算、习惯打卡、月历汇总、复盘和能量值有自动化测试。
- UI 可从导航进入今日、习惯、月历、复盘、数据页。
- 可一键运行并可打包为 Windows EXE。

## Test Stubs
- `test_store_migrates_legacy_payload`
- `test_today_limit_rejects_fourth_active_task`
- `test_habit_checkin_is_idempotent`
- `test_debt_counts_overdue_tasks`
- `test_energy_score_is_bounded`
- `test_month_summary_groups_completion_dates`
- `test_profile_completion_is_idempotent_per_task`

