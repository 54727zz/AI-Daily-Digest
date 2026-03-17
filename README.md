# AI 日报自动推送

每天定时从 RSS 订阅源和 GitHub Trending 收集 AI 相关新闻，生成 HTML 摘要并发送到指定邮箱。

## 目录结构

```
auto-message/
├── ai_news_digest.py   # 主脚本
├── config.ini          # 配置文件（必须手动填写）
├── requirements.txt    # Python 依赖
├── setup_schedule.bat  # 注册 Windows 定时任务（右键管理员运行）
└── digests/            # 自动生成，存放每日 HTML 存档
```

## 数据来源

| 来源 | 说明 |
|------|------|
| HackerNews | 科技社区热门讨论 |
| ArXiv AI | AI 领域最新论文 |
| ArXiv ML | 机器学习最新论文 |
| MIT Tech Review | MIT 科技评论 |
| VentureBeat AI | AI 行业新闻 |
| The Verge AI | 科技媒体 AI 板块 |
| GitHub Trending | 每日热门 AI/ML 开源项目 |

---

## 快速开始

### 第一步：安装依赖

确保已安装 Python 3.8+，然后执行：

```bash
pip install -r requirements.txt
```

### 第二步：配置 config.ini

用任意文本编辑器打开 `config.ini`，填写以下内容：

```ini
[smtp]
host = smtp.qq.com        # QQ 邮箱填 smtp.qq.com，163 邮箱填 smtp.163.com
port = 465                # QQ/163 的 SSL 端口均为 465
sender = your@qq.com      # 你的发件邮箱
password = xxxxxxxxxxxx   # 授权码（不是登录密码，见下方说明）
receiver = your@email.com # 收件邮箱，可以和发件相同

[digest]
keywords = LLM,Agent,GPT,Claude,Gemini,AI,机器学习,大模型
```

#### 如何获取授权码（重要）

**QQ 邮箱：**
1. 登录 QQ 邮箱 → 右上角「设置」→「账户」
2. 找到「POP3/IMAP/SMTP 服务」，点击「开启」
3. 按提示用手机发送短信验证
4. 复制页面上生成的 16 位授权码，粘贴到 `password`

**163 邮箱：**
1. 登录 163 邮箱 → 右上角头像 →「设置」→「POP3/SMTP/IMAP」
2. 开启「SMTP 服务」，设置授权密码
3. 将该授权密码填入 `password`

> 授权码只显示一次，请立即复制保存。

### 第三步：测试运行

```bash
python ai_news_digest.py --test
```

`--test` 模式只生成本地文件，**不发送邮件**，用于验证脚本是否正常工作。
生成的文件在 `digests/` 文件夹，用浏览器打开查看效果。

### 第四步：注册定时任务

确认测试没问题后，**右键** `setup_schedule.bat` → **以管理员身份运行**。

```
[成功] 定时任务已创建，每天 08:00 自动运行
```

之后无需打开终端，每天 8:00 Windows 会自动运行脚本并发送邮件。

---

## 常用命令

```bash
# 手动运行（会真实发送邮件）
python ai_news_digest.py

# 仅测试，不发邮件
python ai_news_digest.py --test

# 查看定时任务状态
schtasks /query /tn "AI_News_Digest"

# 删除定时任务
schtasks /delete /tn "AI_News_Digest" /f
```

---

## 常见问题

**Q: 运行报错 `SMTPAuthenticationError`**
- 检查 `password` 填的是授权码，不是邮箱登录密码
- QQ 邮箱确认 SMTP 服务已开启

**Q: 邮件里新闻条数很少**
- 当天 RSS 源更新慢，或关键词过滤太严
- 可以在 `config.ini` 的 `keywords` 里减少关键词，或去掉不常见的词

**Q: GitHub Trending 抓不到数据**
- 网络问题，脚本会打印 `[WARN]` 但不会中断，邮件仍会发出（只缺少该部分）

**Q: 修改发送时间**
- 删除旧任务后重新注册：修改 `setup_schedule.bat` 里的 `/st 08:00` 为目标时间，再以管理员身份运行

**Q: 想添加更多 RSS 源**
- 打开 `ai_news_digest.py`，在 `RSS_SOURCES` 列表里添加 `("来源名称", "RSS链接")` 即可
