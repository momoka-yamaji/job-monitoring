import asyncio
import base64
import json
import os
import re
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright
import requests

# ★1. 監視する6サイトの設定
SITES = [
    {
        "name": "リタリコ求人ナビ",
        "url": "https://snabi.jp/",
        "selector": "[data-recruitment-count]",
    },
    {
        "name": "スグJOB",
        "url": "https://sugujob.jp/shougaisha/",
        "selector": "strong[class*='_jobCountValue_']",
    },
    {
        "name": "atGP",
        "url": "https://www.atgp.jp/",
        "selector": ".p-content-box__heading__text__number"
    },
    {
        "name": "障害者雇用バンク",
        "url": "https://syogai-koyo-bank.com/company-job/",
       "selector": "#topSearchBarCountNum, .topSearchBarCountNum"
    },
    {
        "name": "dodaチャレンジ",
        "url": "https://doda.jp/challenge/kyujin/",
        "selector": ".allJobCount, #allJobCount, [class*='allJobCount']"
    },
    {
        "name": "babnavi",
        "url": "https://bab-navi.dandi.co.jp/zenkoku/search-result",
        "selector":".num-txt",
    },
]

# ★2. ステップ1で取得したGASのウェブアプリURL
GAS_WEBHOOK_URL = "https://script.google.com/a/macros/bm-sms.co.jp/s/AKfycbyOk5msvdGZuNYQDzIry0GR5T2sd-3-cAxROCH88E0fo2Sy2C-lDyYMveq7QTIgIJyy/exec"


async def scrape_site(page, site):
  try:
    await page.goto(site["url"], wait_until="networkidle", timeout=60000)

    # 1. 求人数の取得
    element = await page.query_selector(site["selector"])
    text = await element.inner_text() if element else "0"
    count = re.sub(r"\D", "", text)  # 数字のみ抽出

    # 2. フルページキャプチャ撮影とBase64化
    os.makedirs("screenshots", exist_ok=True)
    now_str = datetime.now().strftime("%Y%m%d_%H%M")
    img_path = f"screenshots/{site['name']}_{now_str}.png"
    await page.screenshot(path=img_path, full_page=True)

    with open(img_path, "rb") as image_file:
      encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    # 3. Google Apps Script（スプレッドシート＆ドライブ）へデータを送信
    now_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    payload = {
        "date": now_date,
        "site_name": site["name"],
        "count": count,
        "image": encoded_image,
    }
    requests.post(GAS_WEBHOOK_URL, data=json.dumps(payload))

    print(f"[{site['name']}] 成功: {count}件")
  except Exception as e:
    print(f"[{site['name']}] エラー: {e}")


async def main():
  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = await context.new_page()

    # 6サイト順次実行
    for site in SITES:
      await scrape_site(page, site)
      await page.wait_for_timeout(3000)  # 3秒待機

    await browser.close()


if __name__ == "__main__":
  asyncio.run(main())
