# FocusLife 自律管家

这是在原“拖延症任务启动器”代码上增量升级的单机桌面项目，保留任务优先级、两分钟行动、专注计时和 JSON 本地存储，并新增：

- 今日三项任务仪表盘
- 2/25/45/60 分钟专注计时
- 习惯打卡与完成率
- 拖延欠债、月历完成记录
- 晚间三问复盘
- 周数据中心与 0–100 自律能量值

## 一键运行

Windows 双击 `一键启动FocusLife.bat` 或纯英文入口 `start_focuslife.bat`。入口会优先运行已经打包好的 `FocusLife.exe`。

也可进入 `源代码` 后运行：

```powershell
python app.py
```

## 测试

```powershell
cd 源代码
python -m unittest -v test_task_core.py
```

## 数据位置

数据保存于 `%LOCALAPPDATA%\FocusLife\focuslife.json`。程序不联网、不上传个人数据。

## 构建 EXE

先安装依赖：`py -3 -m pip install -r source\requirements.txt`，再双击 `构建EXE.bat` 或 `build_focuslife.bat`。
