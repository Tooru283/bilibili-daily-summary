# B站每日观看总结生成器

自动获取你的B站观看历史，生成结构化的每日总结报告，并通过 Claude AI 进行智能分析。

## ✨ 功能特点

- 📊 **多维度统计** - 按视频时长、分区、UP主分类统计
- ⭐ **质量评分** - 自动评估观看质量（知识增量、思考深度等）
- 🎯 **目标追踪** - 设定每日目标，追踪完成情况
- 📈 **趋势对比** - 与昨日数据对比，发现变化趋势
- 🕐 **时间热力图** - 可视化你的观看时段分布
- 🤖 **AI 总结** - 调用 Claude 生成智能分析和建议
- 📝 **Obsidian 适配** - 生成带有 frontmatter 的 Markdown 文件，支持 Dataview 查询

---

## 📋 环境要求

- **Python 3.8+**
- **Claude Code CLI**（用于生成 AI 总结）
- **Obsidian**（可选，用于查看和管理总结）

---

## 🚀 安装步骤

### 1. 克隆或下载代码

```bash
cd /path/to/your/folder
# 将 daily_summary.py 放到此目录
```

### 2. 创建虚拟环境（推荐）

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install requests
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

### 1. 获取 B站 Cookie

1. 打开浏览器，登录 [B站](https://www.bilibili.com)
2. 按 `F12` 或 `Cmd + Option + I` 打开开发者工具
3. 切换到 **Network** 标签
4. 刷新页面，点击任意一个请求
5. 在 **Headers** 中找到 `Cookie`，复制完整内容

### 2. 创建 cookie.txt

在代码同目录下创建 `cookie.txt` 文件，将复制的 Cookie 粘贴进去：

```bash
touch cookie.txt
# 用编辑器打开，粘贴 Cookie 内容
```

### 3. 修改保存路径

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

### 手动运行

```bash
cd /path/to/your/folder
python daily_summary.py
```

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

### macOS - 使用 crontab

```bash
# 编辑定时任务
crontab -e
```

添加以下行（每天 23:55 运行）：

```cron
55 23 * * * cd /path/to/your/folder && /path/to/your/folder/.venv/bin/python daily_summary.py >> /path/to/your/folder/logs/cron.log 2>&1
```

**注意：** 将 `/path/to/your/folder` 替换为实际路径。

创建日志目录：

```bash
mkdir -p /path/to/your/folder/logs
```

验证任务：

```bash
crontab -l
```

### macOS - 使用 launchd（推荐）

创建配置文件：

```bash
nano ~/Library/LaunchAgents/com.bilibili-summary.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bilibili-summary</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/your/folder/.venv/bin/python</string>
        <string>/path/to/your/folder/daily_summary.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/path/to/your/folder</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>23</integer>
        <key>Minute</key>
        <integer>55</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/path/to/your/folder/logs/bilibili.log</string>
    
    <key>StandardErrorPath</key>
    <string>/path/to/your/folder/logs/bilibili-error.log</string>
</dict>
</plist>
```

加载任务：

```bash
launchctl load ~/Library/LaunchAgents/com.bilibili-summary.plist
```

### Windows - 使用任务计划程序

1. 打开「任务计划程序」
2. 创建基本任务
3. 设置触发器：每天 23:55
4. 设置操作：启动程序
   - 程序：`C:\path\to\your\folder\.venv\Scripts\python.exe`
   - 参数：`daily_summary.py`
   - 起始位置：`C:\path\to\your\folder`

---

## 📄 生成的文件结构

```
bilibili/
├── 2026-03-04-B站总结.md
├── 2026-03-05-B站总结.md
├── .stats_2026-03-04.json    # 统计数据缓存
└── .stats_2026-03-05.json
```

### 总结文件内容

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

---

## 🔧 自定义配置

### 修改目标值

编辑 `daily_summary.py` 中的 `generate_goal_tracking` 函数：

```python
video_goal = 30       # 每日最大视频数
time_goal = 3 * 3600  # 每日最大时长（秒）
deep_goal = 2         # 每日最少深度观看数
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

### Q: 提示「账号未登录」

**原因：** Cookie 已过期

**解决：** 重新从浏览器获取 Cookie，更新 `cookie.txt`

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
