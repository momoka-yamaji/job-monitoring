import asyncio
import os
import re
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        # 1. 競合ページのURL（後から好きなURLに変更できます）
        target_url = 'https://example-job-site.com/search'
        await page.goto(target_url, wait_until='networkidle')

        # 2. 求人数の取得
        element = await page.query_selector('.job-count-number')
        text = await element.inner_text() if element else '0'
        job_count = re.sub(r'\D', '', text)  # 数字のみ抽出

        # 3. 画面全体のキャプチャ保存
        os.makedirs('screenshots', exist_ok=True)
        now_str = datetime.now().strftime('%Y%m%d_%H%M')
        img_path = f'screenshots/capture_{now_str}.png'
        await page.screenshot(path=img_path, full_page=True)

        await browser.close()

        # 4. CSVへ記録保存
        log_file = 'job_history.csv'
        data = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'count': job_count,
        }
        df = pd.DataFrame([data])
        df.to_csv(
            log_file,
            mode='a',
            header=not os.path.exists(log_file),
            index=False,
        )


if __name__ == '__main__':
    asyncio.run(run())
