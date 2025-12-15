import json
import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def capture_screenshot(task, chrome_bin: str, chromedriver_bin: str, captures_dir: str) -> str:
    os.makedirs(captures_dir, exist_ok=True)

    opts = Options()
    opts.binary_location = chrome_bin
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument(f"--window-size={task.viewport_width},{task.viewport_height}")

    service = Service(chromedriver_bin)
    driver = webdriver.Chrome(service=service, options=opts)

    try:
        driver.get(task.url)

        # Zoom via CSS si aplica
        if task.css_zoom and abs(task.css_zoom - 1.0) > 1e-6:
            driver.execute_script(f"document.body.style.zoom = '{task.css_zoom}';")

        # Pre JS
        if task.pre_js:
            driver.execute_script(task.pre_js)

        # Wait
        if task.wait_mode == "SELECTOR" and task.wait_selector:
            WebDriverWait(driver, max(1, int(task.wait_seconds))).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, task.wait_selector))
            )
        else:
            time.sleep(max(0, int(task.wait_seconds)))

        # Remove selectors
        selectors = []
        try:
            selectors = json.loads(task.remove_selectors or "[]")
        except Exception:
            selectors = []

        for sel in selectors:
            if not sel:
                continue
            driver.execute_script(f"document.querySelector('{sel}')?.remove();")

        time.sleep(0.5)

        # Path
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename = f"task{task.id}_{stamp}.png"
        path = os.path.join(captures_dir, filename)

        # Screenshot (viewport). Full page v1: dejamos viewport grande (como tu script 1920x5000) :contentReference[oaicite:2]{index=2}
        driver.save_screenshot(path)
        return path
    finally:
        driver.quit()
