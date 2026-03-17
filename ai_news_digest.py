import feedparser
import requests
from bs4 import BeautifulSoup
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import configparser
import sys
from datetime import datetime
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.ini"
DIGESTS_DIR = Path(__file__).parent / "digests"

RSS_SOURCES = [
    # 境外源（需要 VPN）
    ("HackerNews",      "https://news.ycombinator.com/rss"),
    ("MIT Tech Review", "https://www.technologyreview.com/feed/"),
    ("VentureBeat AI",  "https://venturebeat.com/category/ai/feed/"),
    ("The Verge AI",    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    # 学术源（国内可直连）
    ("ArXiv AI",        "http://arxiv.org/rss/cs.AI"),
    ("ArXiv ML",        "http://arxiv.org/rss/cs.LG"),
    # 国内媒体（无需 VPN）
    ("机器之心",         "https://www.jiqizhixin.com/rss"),
    ("量子位",           "https://www.qbitai.com/feed"),
    ("新智元",           "https://www.aiweekly.co/feed"),
]

def load_config():
    config = configparser.ConfigParser()
    if not CONFIG_FILE.exists():
        print(f"[ERROR] config.ini not found at {CONFIG_FILE}")
        sys.exit(1)
    config.read(CONFIG_FILE, encoding='utf-8')
    return config

def get_keywords(config):
    kw_str = config.get('digest', 'keywords', fallback='LLM,Agent,GPT,Claude,Gemini,AI,机器学习,大模型')
    return [k.strip().lower() for k in kw_str.split(',')]

def matches(text, keywords):
    return any(k in text.lower() for k in keywords)

def fetch_rss(keywords):
    sections = []
    for name, url in RSS_SOURCES:
        try:
            resp = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
            feed = feedparser.parse(resp.content)
            items = []
            for e in feed.entries[:25]:
                title   = e.get('title', '').strip()
                link    = e.get('link', '')
                summary = e.get('summary', '')
                if matches(title + ' ' + summary, keywords):
                    clean = BeautifulSoup(summary, 'html.parser').get_text()[:180]
                    items.append({'title': title, 'link': link, 'summary': clean})
            if items:
                sections.append({'source': name, 'items': items[:8]})
        except Exception as ex:
            print(f"[WARN] {name}: {ex}")
    return sections

def fetch_github(keywords):
    try:
        # 使用 GitHub Search API，比直接访问 github.com/trending 更稳定
        r = requests.get(
            'https://api.github.com/search/repositories',
            params={
                'q': 'topic:llm OR topic:generative-ai OR topic:large-language-model OR topic:ai',
                'sort': 'updated',
                'order': 'desc',
                'per_page': 30,
            },
            headers={'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'Mozilla/5.0'},
            timeout=10,
        )
        repos = []
        for item in r.json().get('items', []):
            name = item['full_name']
            link = item['html_url']
            desc = item.get('description') or ''
            if matches(name + ' ' + desc, keywords):
                repos.append({'name': name, 'link': link, 'desc': desc})
        return repos[:12]
    except Exception as ex:
        print(f"[WARN] GitHub: {ex}")
        return []

def build_html(date_str, rss_sections, gh_repos):
    rows_gh = ''.join(
        f'<tr><td><a href="{r["link"]}">{r["name"]}</a></td>'
        f'<td style="color:#555;font-size:13px">{r["desc"]}</td></tr>'
        for r in gh_repos
    ) or '<tr><td colspan="2" style="color:#999">暂无匹配仓库</td></tr>'

    rss_html = ''
    for sec in rss_sections:
        items_html = ''.join(
            f'<li style="margin-bottom:10px"><a href="{i["link"]}">{i["title"]}</a>'
            f'<p style="color:#666;font-size:12px;margin:2px 0 0">{i["summary"]}</p></li>'
            for i in sec['items']
        )
        rss_html += (f'<h3 style="color:#1a73e8;border-bottom:1px solid #eee;padding-bottom:4px">'
                     f'{sec["source"]}</h3><ul style="padding-left:20px">{items_html}</ul>')

    if not rss_html:
        rss_html = '<p style="color:#999">暂无匹配新闻，可尝试放宽关键词</p>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body{{font-family:Arial,sans-serif;max-width:820px;margin:auto;padding:24px;color:#333}}
  h1{{background:#1a73e8;color:#fff;padding:16px 20px;border-radius:8px;margin-bottom:24px}}
  h2{{color:#333;border-left:4px solid #1a73e8;padding-left:10px;margin-top:32px}}
  table{{width:100%;border-collapse:collapse}}
  td{{padding:8px 6px;border-bottom:1px solid #f0f0f0;vertical-align:top}}
  a{{color:#1a73e8;text-decoration:none}}a:hover{{text-decoration:underline}}
  .footer{{color:#aaa;font-size:12px;margin-top:40px;border-top:1px solid #eee;padding-top:12px}}
</style></head>
<body>
<h1>AI 日报 · {date_str}</h1>
<h2>GitHub Trending · AI/ML 热门仓库</h2>
<table>{rows_gh}</table>
<h2>RSS 精选新闻</h2>
{rss_html}
<div class="footer">由 ai_news_digest 自动生成 · {date_str}</div>
</body></html>"""

def save_digest(date_str, html):
    DIGESTS_DIR.mkdir(exist_ok=True)
    path = DIGESTS_DIR / f"{date_str}.html"
    path.write_text(html, encoding='utf-8')
    print(f"[INFO] Digest saved: {path}")

def send_email(config, subject, html):
    host     = config.get('smtp', 'host')
    port     = config.getint('smtp', 'port', fallback=465)
    sender   = config.get('smtp', 'sender')
    password = config.get('smtp', 'password')
    receiver = config.get('smtp', 'receiver')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = sender
    msg['To']      = receiver
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=ctx) as s:
        s.login(sender, password)
        s.sendmail(sender, receiver, msg.as_string())
    print(f"[INFO] Email sent to {receiver}")

def main():
    test = '--test' in sys.argv
    cfg  = load_config()
    kw   = get_keywords(cfg)
    date = datetime.now().strftime('%Y-%m-%d')

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching RSS feeds...")
    rss = fetch_rss(kw)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching GitHub Trending...")
    gh  = fetch_github(kw)

    html = build_html(date, rss, gh)
    save_digest(date, html)

    if test:
        print("[INFO] --test mode: digest saved, email skipped.")
        print(f"[INFO] Open: {DIGESTS_DIR / (date + '.html')}")
    else:
        send_email(cfg, f"[AI日报] {date}", html)

if __name__ == '__main__':
    main()
