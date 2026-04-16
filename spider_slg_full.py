import asyncio
import os
import json
import time
from pathlib import Path
from playwright.async_api import async_playwright
import sys

# Ensure project root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.adapters.taptap import TapTapAdapter

async def fetch_app_ids():
    apps = []
    print(">>> 启动 Playwright 抓取 TapTap 前 30 页应用 ID...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for i in range(1, 31):
            print(f"正在扫描第 {i} 页...")
            try:
                await page.goto(f"https://www.taptap.cn/tag/slg?page={i}", wait_until="networkidle", timeout=15000)
            except Exception as e:
                print(f"第 {i} 页加载超时或失败，跳过。")
                continue
                
            data = await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a[href*="/app/"]'));
                let results = [];
                links.forEach(a => {
                    const href = a.getAttribute('href');
                    const match = href.match(/\/app\/(\d+)/);
                    let title = a.innerText.trim();
                    if(!title) {
                        const img = a.querySelector('img');
                        if(img) title = img.getAttribute('alt');
                    }
                    if(match && title && title.length > 1) {
                        results.push({app_id: match[1], name: title});
                    }
                });
                return results;
            }''')
            
            for item in data:
                if not any(g['app_id'] == item['app_id'] for g in apps):
                    apps.append(item)
            
            await page.wait_for_timeout(500)
            
        await browser.close()
    
    print(f"✅ 抓取完成，共获得 {len(apps)} 个去重后的 App ID！")
    return apps

def fetch_game_texts(apps):
    print(f">>> 开始使用 TapTapAdapter 获取每一个游戏的详细描述 (需耗时大概 {len(apps)} 秒，请耐心等待)")
    api = TapTapAdapter()
    results = []
    
    for idx, item in enumerate(apps, 1):
        try:
            info = api.get_game_info(item["app_id"])
            if info:
                desc = str(info.get("description", "")).replace("\n", " ").strip()
                tags = [t.get("value", "") for t in info.get("tags", []) if isinstance(t, dict)]
                item["description"] = desc[:800] # truncate slightly
                item["tags"] = tags
                results.append(item)
                print(f"[{idx}/{len(apps)}] 成功爬取: {item['name']}")
        except Exception as e:
            print(f"[{idx}/{len(apps)}] 爬取失败: {item['name']} ({e})")
            
        time.sleep(1.0) # 遵守防风控
        
    out_file = Path("data/taptap_full_slg_corpus.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"🎉 爬取完毕，全量语料已存入 {out_file.absolute()}")

if __name__ == "__main__":
    apps = asyncio.run(fetch_app_ids())
    fetch_game_texts(apps)
