# -*- coding: utf-8 -*-
"""화성ON 화면·사용 과정 캡처 → docs/screenshots/*.png

사용:
  1) 서버 실행:  python -m uvicorn backend.app:app --host 0.0.0.0 --port 5200
  2) 의존성:     pip install playwright && python -m playwright install chromium
  3) 캡처:       python scripts/screenshot.py
"""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://127.0.0.1:5200/"


def lang_btn(page, name):
    page.locator(".lang", has_text=name).first.click()


with sync_playwright() as p:
    b = p.chromium.launch()

    # ---------- 데스크톱 ----------
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    page = ctx.new_page()
    page.goto(URL); page.wait_for_selector(".hero h1"); time.sleep(1.2)
    page.screenshot(path=str(OUT / "01_home_ko.png"))

    lang_btn(page, "English"); time.sleep(0.8)
    page.screenshot(path=str(OUT / "02_home_en.png"))

    lang_btn(page, "한국어"); time.sleep(0.4)
    page.fill("#input", "쓰레기는 어떻게 버려요?"); page.click("#send")
    page.wait_for_selector(".cit-card", timeout=15000); time.sleep(1.0)
    page.screenshot(path=str(OUT / "03_chat_ko.png"))

    page.reload(); page.wait_for_selector(".hero h1")
    lang_btn(page, "Tiếng Việt"); time.sleep(0.5)
    page.fill("#input", "Tôi chưa được trả lương"); page.click("#send")
    page.wait_for_selector(".cit-card", timeout=15000); time.sleep(1.0)
    page.screenshot(path=str(OUT / "04_chat_vi.png"))

    page.reload(); page.wait_for_selector(".hero h1")
    lang_btn(page, "中文"); time.sleep(0.7)
    page.screenshot(path=str(OUT / "05_home_zh.png"))

    page.reload(); page.wait_for_selector(".hero h1")
    page.fill("#input", "월급을 못 받았어요"); page.click("#send")
    page.wait_for_selector(".act.form", timeout=15000); time.sleep(0.6)
    page.screenshot(path=str(OUT / "06_chat_labor.png"))
    page.click(".act.form"); page.wait_for_selector("#modal.open"); time.sleep(0.6)
    page.screenshot(path=str(OUT / "07_draft_modal.png"))

    vals = {"name": "Nguyen Van A", "nationality": "베트남", "phone": "010-1234-5678",
            "company": "○○산업(주)", "company_addr": "화성시 향남읍 행정중앙로 12",
            "start_date": "2025-03-01", "end_date": "재직", "amount": "3200000",
            "period": "2026-03 ~ 2026-05"}
    for k, v in vals.items():
        loc = page.locator(f'#modal-body input[data-key="{k}"]')
        if loc.count():
            loc.fill(v)
    page.click("#modal-make"); page.wait_for_selector("#modal-result", state="visible"); time.sleep(0.8)
    page.add_style_tag(content=".modal-card{max-height:none !important;overflow:visible !important}")
    page.evaluate("()=>{const t=document.getElementById('modal-result');t.style.height=(t.scrollHeight+8)+'px';}")
    time.sleep(0.4)
    page.locator(".modal-card").screenshot(path=str(OUT / "08_draft_result.png"))

    # 환각 방지: 범위 밖 질문 → 단정하지 않고 안전 안내
    page.reload(); page.wait_for_selector(".hero h1")
    page.fill("#input", "비트코인 시세랑 맛집 추천해줘"); page.click("#send")
    page.wait_for_selector(".msg.bot .bubble", timeout=15000); time.sleep(1.0)
    page.screenshot(path=str(OUT / "11_refusal_ko.png"))

    # 태국어 / 캄보디아어 홈(6개 언어 완비)
    page.reload(); page.wait_for_selector(".hero h1")
    page.locator(".lang", has_text="ภาษาไทย").first.click(); time.sleep(0.7)
    page.screenshot(path=str(OUT / "12_home_th.png"))
    page.locator(".lang", has_text="ភាសាខ្មែរ").first.click(); time.sleep(0.7)
    page.screenshot(path=str(OUT / "13_home_km.png"))
    ctx.close()

    # ---------- 모바일 ----------
    EXPAND = (".messages{overflow:visible !important;height:auto !important}"
              ".chat-col{height:auto !important}"
              ".side{flex-direction:column !important;overflow:visible !important}"
              ".layout{height:auto !important}"
              "body{height:auto !important;display:block !important}")
    m = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True)
    mp = m.new_page()
    mp.goto(URL); mp.wait_for_selector(".hero h1"); mp.add_style_tag(content=EXPAND); time.sleep(1.0)
    mp.screenshot(path=str(OUT / "09_mobile_home.png"), full_page=True)
    mp.fill("#input", "외국인등록 어떻게 해요?"); mp.click("#send")
    mp.wait_for_selector(".cit-card", timeout=15000); mp.add_style_tag(content=EXPAND); time.sleep(1.0)
    mp.screenshot(path=str(OUT / "10_mobile_chat.png"), full_page=True)
    m.close()

    b.close()
print("DONE ->", OUT)
