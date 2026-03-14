# B站观看总结生成器

自动获取你的B站观看历史，生成结构化的**每日 + 每周**总结报告，并通过 Claude AI 进行智能分析。

## ✨ 功能特点

### 每日总结（`daily_summary.py`）
- 📊 **多维度统计** - 按视频时长、分区、UP主分类统计
- ⭐ **质量评分** - 自动评估观看质量（知识增量、思考深度等）
- 🎯 **目标追踪** - 设定每日目标，追踪完成情况
- 📈 **趋势对比** - 与昨日数据对比，发现变化趋势
- 🕐 **时间热力图** - 可视化你的观看时段分布
- 🤖 **AI 总结** - 调用 Claude 生成智能分析和建议
- 📝 **Obsidian 适配** - 生成带有 frontmatter 的 Markdown 文件，支持 Dataview 查询

### 每周总结（`weekly_summary.py`）
- 📅 **自动识别周边界** - 按 ISO 周自动计算周一至周日
- 📊 **周汇总统计** - 自动聚合全周时长、视频数、深度观看等指标
- 🔍 **问题自动检测** - 对比健康基准，自动标记超时、碎片化、评分下滑等问题
- 💡 **分层建议生成** - 根据检测到的问题自动生成紧急/中期/长期行动建议
- 📁 **文件自动归档** - 周结束后将日报移入对应周文件夹，保持目录整洁

---

## 📋 环境要求

- **Python 3.8+**
- **Claude Code CLI**（用于生成 AI 总结）
- **Obsidian**（可选，用于查看和管理总结）

---

## 🚀 安装步骤

### 1. 克隆或下载代码

```bash
git clone https://github.com/Tooru283/bilibili-daily-summary.git
cd bilibili-daily-summary
```

### 2. 创建虚拟环境（推荐）

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install requests browser-cookie3
```

### 4. 安装 Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
```

首次使用需要登录：

```bash
claude login
```

---

## ⚙️ 配置说明

### 1. 登录 B站

直接在浏览器（Chrome / Safari / Firefox）中登录 B站即可。脚本会通过 `browser-cookie3` **自动读取**浏览器中的 Cookie，无需手动复制。

> **注意：** 首次运行时，macOS 可能会弹出权限提示，需要允许访问 Safari/Chrome 的 Cookie 数据库。

### 2. 修改保存路径

编辑 `daily_summary.py` 第 9 行，修改为你的 Obsidian vault 路径：

```python
# 保存路径
SUMMARY_FOLDER = "/path/to/your/obsidian/vault/bilibili"
```

**示例路径：**
- macOS: `/Users/你的用户名/Documents/Obsidian/笔记/bilibili`
- Windows: `C:/Users/你的用户名/Documents/Obsidian/笔记/bilibili`

---

## 📖 使用方法

### 每日总结

```bash
python daily_summary.py
```

### 每周总结

```bash
python weekly_summary.py          # 生成上周总结（默认，每周一运行）
python weekly_summary.py 0        # 生成本周（当前不完整）总结
python weekly_summary.py 2026-W10 # 生成指定周总结
```

> **推荐工作流：** 每天晚上 23:55 自动运行 `daily_summary.py`，每周一早上手动或自动运行 `weekly_summary.py`。

### 运行输出

```
📥 获取B站历史记录...
   获取到 240 条记录

🔄 检查昨日总结...
   ✅ 昨日总结已是最新，跳过

📊 生成今日总结...
📅 正在生成 2026-03-05 的总结（45条记录）...
   🤖 生成 AI 总结...
   ✅ 已保存到: /path/to/bilibili/2026-03-05-B站总结.md

🎉 完成！今日得分：65/100
```

---

## ⏰ 定时任务设置

### macOS - 使用 LaunchAgent（推荐）✨

LaunchAgent 支持**即使电脑休眠也会自动唤醒运行**，无需电脑始终开着。

#### 1. 创建包装脚本

项目中已包含 `run_summary.sh`，这是一个自动激活虚拟环境并运行脚本的包装脚本：

```bash
# 查看脚本内容
cat run_summary.sh

# 确保脚本可执行
chmod +x run_summary.sh
```

#### 2. 创建 LaunchAgent 配置

创建配置文件：

```bash
cat > ~/Library/LaunchAgents/com.user.bilisummary.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.bilisummary</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/moca/Work/Python/Blisummary/run_summary.sh</string>
    </array>

    <!-- 定时配置：每天23:00运行 -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>23</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <!-- 同时在启动时也运行一次 -->
    <key>RunAtLoad</key>
    <true/>

    <!-- 标准输出/错误日志 -->
    <key>StandardOutPath</key>
    <string>/tmp/bilisummary_out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/bilisummary_err.log</string>

    <key>WorkingDirectory</key>
    <string>/Users/moca/Work/Python/Blisummary</string>
</dict>
</plist>
EOF
```

**注意：** 将路径修改为你的实际项目目录。

#### 3. 加载并启动任务

```bash
# 加载 LaunchAgent
launchctl load ~/Library/LaunchAgents/com.user.bilisummary.plist

# 验证已加载
launchctl list | grep bilisummary
```

#### 4. 管理命令

```bash
# 手动触发一次
launchctl start com.user.bilisummary

# 暂停运行
launchctl unload ~/Library/LaunchAgents/com.user.bilisummary.plist

# 重新启用
launchctl load ~/Library/LaunchAgents/com.user.bilisummary.plist

# 查看日志
tail -50 /tmp/bilisummary.log
tail -20 /tmp/bilisummary_err.log  # 查看错误日志
```

#### 5. 修改运行时间

编辑配置文件中的 `StartCalendarInterval` 部分：

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>23</integer>     <!-- 改为你想要的小时（0-23）-->
    <key>Minute</key>
    <integer>0</integer>      <!-- 改为你想要的分钟（0-59）-->
</dict>
```

修改后需要重新加载：

```bash
launchctl unload ~/Library/LaunchAgents/com.user.bilisummary.plist
launchctl load ~/Library/LaunchAgents/com.user.bilisummary.plist
```

### macOS - 使用 crontab（备选）

如果不想用 LaunchAgent，也可以用 crontab：

```bash
crontab -e
```

添加以下行（每天 23:00 运行）：

```cron
0 23 * * * cd /Users/moca/Work/Python/Blisummary && source .venv/bin/activate && python daily_summary.py >> /tmp/bilisummary.log 2>&1
```

### Windows - 使用任务计划程序

1. 打开「任务计划程序」
2. 创建基本任务
3. 设置触发器：每天 23:00
4. 设置操作：启动程序
   - 程序：`C:\path\to\your\folder\.venv\Scripts\python.exe`
   - 参数：`daily_summary.py`
   - 起始位置：`C:\path\to\your\folder`

---

## 📄 生成的文件结构

```
bilibili/
├── 2026-03-10-B站总结.md         # 本周日报（周结束后自动归档）
├── 2026-03-11-B站总结.md
├── .stats_2026-03-10.json        # 统计数据缓存（供周总结读取）
├── .stats_2026-03-11.json
└── 周总结/
    └── W10(2026.3.4-3.8)/
        ├── 2026-03-04-B站总结.md # 已归档的日报
        ├── 2026-03-05-B站总结.md
        └── 2026-W10-周总结.md    # 周总结文件
```

### 总结文件内容

**每日总结（`daily_summary.py`）**
- **Frontmatter** - 包含日期、标签、统计数据（支持 Dataview）
- **目标追踪** - 视频数量、时长、深度观看目标完成情况
- **与昨日对比** - 各项指标变化趋势
- **基础统计** - 观看视频数、时长、完成度等
- **视频分类统计** - 长/中/短视频分布和质量评分
- **时间热力图** - 按小时统计的观看分布
- **精华内容** - 最佳长视频、短视频推荐
- **UP主推荐** - 今日观看时长最多的UP主
- **TOP10 详情** - 观看时长前10的视频
- **AI 总结** - Claude 生成的智能分析
- **反思日记** - 预留的反思模板
- **Dataview 查询** - 本周、月度统计查询模板

**每周总结（`weekly_summary.py`）**
- **周汇总数据** - 总时长、视频数、深度观看、周均分
- **日均对比表** - 每天数据一览及健康状态
- **数据对标** - 与健康基准的差距分析
- **AI 总结** - Claude 生成的周分析
- **问题分析** - 自动检测并按严重程度（🔴🟡）分级
- **改进建议** - 紧急/中期/长期三层行动建议
- **下周目标** - 自动生成下周行动计划

---

## 🔧 自定义配置

### 修改每日目标值

编辑 `daily_summary.py` 中的 `generate_goal_tracking` 函数：

```python
video_goal = 30       # 每日最大视频数
time_goal = 3 * 3600  # 每日最大时长（秒）
deep_goal = 2         # 每日最少深度观看数
```

### 修改每周健康基准

编辑 `weekly_summary.py` 顶部的 `HEALTH` 字典：

```python
HEALTH = {
    "daily_time_sec":   2 * 3600,  # 每日时长上限（秒）
    "daily_videos":     30,         # 每日视频数上限
    "deep_watch_ratio": 0.30,       # 深度观看占比目标
    "fragment_ratio":   0.50,       # 碎片视频占比上限
    "weekly_score":     70,         # 周评分目标
    "avg_completion":   40.0,       # 平均完成度目标 %
}
```

### 修改获取页数

在 `main` 函数中修改 `pages` 参数（每页 30 条）：

```python
history = get_bilibili_history(cookie, pages=8)  # 获取 8 页 = 240 条
```

### 修改视频分类标准

编辑 `classify_videos` 函数：

```python
if duration >= 600:    # 长视频 >= 10分钟
    long_videos.append(item)
elif duration >= 180:  # 中视频 >= 3分钟
    medium_videos.append(item)
else:                  # 短视频 < 3分钟
    short_videos.append(item)
```

---

## ❓ 常见问题

### Q: 提示「未能从浏览器获取 B站 Cookie」

**原因：** 浏览器未登录 B站，或脚本没有权限访问浏览器 Cookie

**解决：**
1. 确认已在 Chrome / Safari / Firefox 中登录 B站
2. macOS 系统设置 → 隐私与安全性 → 完全磁盘访问权限，添加终端或 Python

### Q: 提示「请求失败」

**原因：** 网络问题或 B站 API 变更

**解决：**
1. 检查网络连接
2. 确认 Cookie 有效
3. 稍后重试

### Q: AI 总结为空

**原因：** Claude Code CLI 未安装或未登录

**解决：**
```bash
npm install -g @anthropic-ai/claude-code
claude login
```

### Q: crontab 任务不执行

**macOS 解决方案：**
1. 检查 cron 服务：`sudo launchctl list | grep cron`
2. 授予完全磁盘访问权限：
   - 系统设置 → 隐私与安全性 → 完全磁盘访问权限
   - 添加 `/usr/sbin/cron`

### Q: 中文显示乱码

**解决：** 确保终端和文件使用 UTF-8 编码

```bash
export LANG=zh_CN.UTF-8
```

---

## 📊 Obsidian Dataview 查询示例

在 Obsidian 中安装 Dataview 插件后，可以使用以下查询：

### 本周观看汇总

```dataview
TABLE WITHOUT ID
  file.link as "日期",
  video_count as "视频数",
  round(total_time / 3600, 1) as "小时",
  score as "得分"
FROM #bilibili
WHERE week_number = this.week_number
SORT date DESC
```

### 碎片化警告记录

```dataview
TABLE WITHOUT ID
  file.link as "日期",
  video_count as "视频数",
  behavior_metrics.avg_completion + "%" as "完成度"
FROM #bilibili AND #碎片化警告
SORT date DESC
LIMIT 5
```

---

## 📝 更新日志

### v1.2.0
- 新增 `weekly_summary.py` 每周总结生成器
- 支持自动识别周边界、问题检测、分层建议、文件归档

### v1.1.0
- 改用 `browser-cookie3` 自动从浏览器读取 Cookie，无需手动维护 `cookie.txt`
- 支持 Chrome、Safari、Firefox 自动检测

### v1.0.0
- 初始版本
- 基础统计和分类功能
- AI 总结集成
- Obsidian 适配

---

## 📜 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
