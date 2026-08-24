import asyncio
import os
import re
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright

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
        "selector": ".p-content-box__heading__text__number",
    },
    {
        "name": "障害者雇用バンク",
        "url": "https://syogai-koyo-bank.com/company-job/",
        "selector": "#topSearchBarCountNum, .topSearchBarCountNum",
    },
    {
        "name": "dodaチャレンジ",
        "url": "https://doda.jp/challenge/kyujin/",
        "selector": ".allJobCount, #allJobCount, [class*='allJobCount']",
    },
    {
        "name": "babnavi",
        "url": "https://bab-navi.dandi.co.jp/zenkoku/search-result",
        "selector": ".num-txt",
    },
]


async def scrape_site(page, site):
  try:
    await page.goto(site["url"], wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(3000)

    # 1. 求人数の取得
    element = await page.query_selector(site["selector"])
    text = await element.inner_text() if element else "0"
    count = re.sub(r"\D", "", text)

    # 2. キャプチャ画像の保存
    os.makedirs("screenshots", exist_ok=True)
    now_str = datetime.now().strftime("%Y%m%d_%H%M")
    img_path = f"screenshots/{site['name']}_{now_str}.png"
    await page.screenshot(path=img_path, full_page=True)

    now_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{site['name']}] 成功: {count}件")

    return {
        "date": now_date,
        "site_name": site["name"],
        "count": count,
        "image_path": img_path,
    }

  except Exception as e:
    print(f"[{site['name']}] エラー: {e}")
    return None


async def main():
  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = await context.new_page()

    results = []
    for site in SITES:
      res = await scrape_site(page, site)
      if res:
        results.append(res)
      await page.wait_for_timeout(2000)

    await browser.close()

    # CSVファイル（job_history.csv）へ保存・追記
    if results:
      log_file = "job_history.csv"
      df = pd.DataFrame(results)
      df.to_csv(
          log_file,
          mode="a",
          header=not os.path.exists(log_file),
          index=False,
          encoding="utf-8-sig",
      )


if __name__ == "__main__":
  asyncio.run(main())
