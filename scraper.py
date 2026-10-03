import logging, threading, time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

log = logging.getLogger(__name__)

URL = "https://www.rate.am/hy/armenian-dram-exchange-rates/banks"
ROW_SELECTOR = "div.group.flex.items-center.h-10"
CACHE_TTL = 120

_lock = threading.Lock()
_driver = None
_cache = {"ts": 0.0, "rows": []}


def _make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=opts)

def _scrape():
    global _driver
    if _driver is None:
        _driver = _make_driver()
    _driver.get(URL)
    WebDriverWait(_driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ROW_SELECTOR))
    )
    rows = []
    for el in _driver.find_elements(By.CSS_SELECTOR, ROW_SELECTOR):
        cells = [c.strip() for c in el.text.split("\n") if c.strip()]
        if cells:
            rows.append(cells)
    return rows

def get_rows():
    global _driver
    with _lock:
        if time.time() - _cache["ts"] < CACHE_TTL and _cache["rows"]:
            return _cache["rows"]
        try:
            rows = _scrape()
        except Exception:
            log.exception("scrape failed, restarting driver")
            try:
                if _driver:
                    _driver.quit()
            finally:
                _driver = None
            if _cache["rows"]:
                return _cache["rows"]
            raise
        _cache.update(ts=time.time(), rows=rows)
        return rows

def close():
    if _driver:
        _driver.quit()