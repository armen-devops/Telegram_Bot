import logging, threading, time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

log = logging.getLogger(__name__)

URL = "https://www.rate.am/hy/armenian-dram-exchange-rates/banks"
ROW_SELECTOR = "div.group.flex.items-center.h-10"
REFRESH_EVERY = 60
RETRY_AFTER = 10
FIRST_LOAD_TIMEOUT = 25

_driver = None
_cache = {"ts": 0.0, "rows": []}
_ready = threading.Event()
_stop = threading.Event()
_thread = None
_thread_lock = threading.Lock()


def _make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.page_load_strategy = "eager"
    opts.add_experimental_option(
        "prefs", {"profile.managed_default_content_settings.images": 2}
    )
    return webdriver.Chrome(
        service=Service(popen_kw={"start_new_session": True}),
        options=opts,
    )


def _quit_driver():
    global _driver
    try:
        if _driver:
            _driver.quit()
    except Exception:
        log.exception("driver.quit() failed")
    finally:
        _driver = None


def _scrape():
    global _driver
    if _driver is None:
        _driver = _make_driver()
    _driver.get(URL)
    WebDriverWait(_driver, 15).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, ROW_SELECTOR))
    )
    rows = []
    for el in _driver.find_elements(By.CSS_SELECTOR, ROW_SELECTOR):
        cells = [c.strip() for c in el.text.split("\n") if c.strip()]
        if cells:
            rows.append(cells)
    return rows


def _refresh_loop():
    global _cache
    while not _stop.is_set():
        wait = REFRESH_EVERY
        try:
            rows = _scrape()
            if rows:
                _cache = {"ts": time.time(), "rows": rows}
                _ready.set()
        except Exception:
            log.exception("scrape failed, restarting driver")
            _quit_driver()
            wait = RETRY_AFTER
        _stop.wait(wait)
    _quit_driver()


def start():
    global _thread
    with _thread_lock:
        if _thread is None or not _thread.is_alive():
            _stop.clear()
            _thread = threading.Thread(target=_refresh_loop, daemon=True, name="rate-scraper")
            _thread.start()


def get_rows():
    start()
    if not _ready.wait(timeout=FIRST_LOAD_TIMEOUT):
        raise RuntimeError("rates not loaded yet")
    return _cache["rows"]


def updated_at():
    return _cache["ts"]


def close():
    _stop.set()
    if _thread:
        _thread.join(timeout=10)
    _quit_driver()