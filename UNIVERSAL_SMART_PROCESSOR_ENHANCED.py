#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIVERSAL SMART PROCESSOR ENHANCED v2.0
All-in-One Ultra-Powerful Web Scraper & File Processor

ALL IMPROVEMENTS IMPLEMENTED:
✅ Proxy simulation (coded behavior, NO real proxies/keys needed)
✅ Caching system (SQLite-based)
✅ Configuration file support (config.ini)
✅ Advanced logging with rotation
✅ CAPTCHA detection simulation
✅ IP/User-Agent rotation (coded simulation)
✅ Cookie persistence
✅ Rate limiting protection
✅ Dependency auto-installation
✅ System dependency checks
✅ Blocked detection
✅ Stealth mode enhanced
✅ Fallback mechanisms
✅ Single file (no modules needed)
✅ Double-click to run

WORKS WITHOUT EXTERNAL KEYS OR PAYMENTS!
Everything is implemented via code simulation.

Usage:
    python UNIVERSAL_SMART_PROCESSOR_ENHANCED.py [options]
    or double-click the file
"""

import sys
import os
import subprocess
import importlib
import threading
import queue
import time
import random
import re
import json
import socket
import hashlib
import shutil
import webbrowser
import platform
import logging
import logging.handlers
import configparser
import sqlite3
from datetime import datetime, timedelta
from urllib.parse import urlparse
from pathlib import Path
from collections import defaultdict, Counter


# ==============================================================================
# GLOBAL CONSTANTS
# ==============================================================================

APP_NAME = "UNIVERSAL SMART PROCESSOR ENHANCED"
APP_VERSION = "2.0"

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "cache"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "config"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)


# ==============================================================================
# CONFIGURATION SYSTEM
# ==============================================================================

class ConfigManager:
    DEFAULT_CONFIG = {
        "general": {"output_format": "md", "output_dir": "output", "concurrency": 2, "retries": 3, "timeout": 45, "delay_between_requests": 2.0},
        "scraping": {"use_cache": True, "cache_expiry_days": 7, "save_cookies": True, "use_proxy_simulation": True, "auto_scroll": True, "blocked_detection": True},
        "browsers": {"preferred_browser": "bundled", "headless": True, "viewport_width": 1920, "viewport_height": 1080, "stealth_mode": True},
        "logging": {"log_level": "INFO", "log_file": "logs/scraper.log", "max_log_size": 10, "backup_count": 5},
        "proxy_simulation": {
            "enabled": True, "ip_rotation": True,
            "user_agent_list": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
            ],
            "referer_list": ["https://www.google.com/", "https://www.bing.com/", "https://www.yahoo.com/"]
        },
    }
    
    def __init__(self):
        self.config = {}
        self.config_file = os.path.join(BASE_DIR, "config", "config.ini")
        self._load()
    
    def _load(self):
        config = configparser.ConfigParser()
        config.read_dict(self.DEFAULT_CONFIG)
        if os.path.exists(self.config_file):
            try: config.read(self.config_file)
            except: pass
        self.config = {s: dict(config.items(s)) for s in config.sections()}
    
    def get(self, section, key, default=None):
        try: return self.config.get(section, {}).get(key, default)
        except: return default
    
    def save(self):
        config = configparser.ConfigParser()
        for s, items in self.config.items(): config[s] = items
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f: config.write(f)


CONFIG = ConfigManager()


# ==============================================================================
# LOGGING SYSTEM
# ==============================================================================

class Logger:
    def __init__(self):
        self.logger = logging.getLogger(APP_NAME)
        self.logger.setLevel(getattr(logging, CONFIG.get("logging", "log_level", "INFO").upper(), logging.INFO))
        self.logger.handlers = []
        
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console)
        
        try:
            log_file = CONFIG.get("logging", "log_file", "logs/scraper.log")
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(fh)
        except: pass
    
    def info(self, msg): self.logger.info(msg)
    def warning(self, msg): self.logger.warning(msg)
    def error(self, msg): self.logger.error(msg)


LOG = Logger()


# ==============================================================================
# CACHE SYSTEM
# ==============================================================================

class Cache:
    def __init__(self):
        self.cache_db = os.path.join(BASE_DIR, "cache", "cache.db")
        self.conn = sqlite3.connect(self.cache_db, check_same_thread=False)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS cache (url TEXT PRIMARY KEY, content TEXT, format TEXT, timestamp DATETIME, size INTEGER)''')
        self.conn.commit()
    
    def get(self, url, fmt="md"):
        expiry = datetime.now() - timedelta(days=int(CONFIG.get("scraping", "cache_expiry_days", 7)))
        c = self.conn.cursor()
        c.execute("SELECT content FROM cache WHERE url=? AND format=? AND timestamp>?", (url, fmt, expiry.isoformat()))
        return c.fetchone()
    
    def set(self, url, content, fmt="md"):
        self.conn.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?,?,?)", (url, content, fmt, datetime.now().isoformat(), len(content)))
        self.conn.commit()
    
    def clear(self):
        self.conn.execute("DELETE FROM cache")
        self.conn.commit()


CACHE = Cache()


# ==============================================================================
# PROXY SIMULATION (NO REAL PROXIES)
# ==============================================================================

class ProxySimulator:
    def __init__(self):
        self.uas = CONFIG.get("proxy_simulation", "user_agent_list", [])
        self.referers = CONFIG.get("proxy_simulation", "referer_list", [])
        self.ips = ["192.168.1.100", "192.168.1.101", "10.0.0.100", "172.16.0.100"]
        self.idx = 0
    
    def get_headers(self):
        ua = self.uas[self.idx % len(self.uas)]
        ref = self.referers[self.idx % len(self.referers)]
        ip = self.ips[self.idx % len(self.ips)]
        self.idx += 1
        return {"User-Agent": ua, "Referer": ref, "X-Forwarded-For": ip, "X-Real-IP": ip}
    
    def rotate(self):
        self.idx += 1


PROXY = ProxySimulator()


# ==============================================================================
# COOKIE MANAGER
# ==============================================================================

class CookieManager:
    def __init__(self):
        self.file = os.path.join(BASE_DIR, "config", "cookies.json")
        self.cookies = self._load()
    
    def _load(self):
        if os.path.exists(self.file):
            try: return json.loads(open(self.file, encoding='utf-8').read())
            except: return {}
        return {}
    
    def save(self):
        os.makedirs(os.path.dirname(self.file), exist_ok=True)
        with open(self.file, 'w', encoding='utf-8') as f: json.dump(self.cookies, f)
    
    def get(self, domain): return self.cookies.get(domain, {})
    def set(self, domain, c): self.cookies[domain] = c; self.save()


COOKIES = CookieManager()


# ==============================================================================
# RATE LIMITER
# ==============================================================================

class RateLimiter:
    def __init__(self):
        self.last = 0
        self.count = 0
        self.delay = float(CONFIG.get("general", "delay_between_requests", 2.0))
    
    def wait(self):
        now = time.time()
        elapsed = now - self.last
        if elapsed < self.delay: time.sleep(self.delay - elapsed)
        self.last = time.time()
        self.count += 1
        if self.count >= 10: self.count = 0; time.sleep(random.uniform(5, 10))


RATE = RateLimiter()


# ==============================================================================
# BLOCKED DETECTION
# ==============================================================================

BLOCKED_MARKERS = ["just a moment", "checking your browser", "attention required", "access denied", "are you a robot", "captcha", "cloudflare", "rate limit", "403", "429", "503", "blocked", "unusual traffic", "verify you are human", "bot detection"]

def is_blocked(title, body, code=None):
    if code in (403, 429, 500, 502, 503, 504): return True
    text = f"{title} {body}".lower()
    return any(m in text for m in BLOCKED_MARKERS)


# ==============================================================================
# DEPENDENCY INSTALLER
# ==============================================================================

class DependencyInstaller:
    PACKAGES = [("requests", "requests"), ("playwright", "playwright"), ("pypdf", "pypdf"), ("python-docx", "docx"), ("beautifulsoup4", "bs4"), ("markdownify", "markdownify")]
    LINUX_DEPS = ["libglib-2.0-0", "libnss3", "libnspr4", "libxkbcommon0", "libxcomposite1", "libxdamage1", "libgbm1"]
    
    def check_python(self, pkg, mod):
        try: importlib.import_module(mod); return True
        except: return False
    
    def check_system(self):
        if not platform.system().lower() == "linux": return True
        missing = []
        for d in self.LINUX_DEPS:
            try:
                if subprocess.run(["dpkg", "-l", d], capture_output=True).returncode != 0: missing.append(d)
            except: missing.append(d)
        if missing:
            try: subprocess.run(["sudo", "apt-get", "install", "-y"] + missing, capture_output=True)
            except: pass
        return len(missing) == 0
    
    def install_browsers(self):
        try: subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); return True
        except: return False
    
    def run(self):
        for p, m in self.PACKAGES:
            if not self.check_python(p, m):
                try: subprocess.check_call([sys.executable, "-m", "pip", "install", p, "-q"])
                except: pass
        self.check_system()
        if not self._chromium_ready(): self.install_browsers()
    
    def _chromium_ready(self):
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p: p.chromium.launch(headless=True).close()
            return True
        except: return False


# ==============================================================================
# STEALTH SCRIPT
# ==============================================================================

STEALTH_SCRIPT = """
(() => {
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [{name: 'Chrome PDF Plugin', description: '', filename: 'internal-pdf-viewer'}]});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
    window.chrome = window.chrome || {runtime: {}, loadTimes: () => ({}), csi: () => ({})};
    Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
    Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
    try { const orig = WebGLRenderingContext.prototype.getParameter; WebGLRenderingContext.prototype.getParameter = function(p) { if (p === 37445) return 'Intel Inc.'; if (p === 37446) return 'Intel Iris OpenGL Engine'; return orig.call(this, p); }; } catch(e) {}
    try { Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})}); } catch(e) {}
    Object.defineProperty(screen, 'width', {get: () => 1920});
    Object.defineProperty(screen, 'height', {get: () => 1080});
})();
"""


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def sanitize(name):
    name = re.sub(r'^https?://', '', name)
    name = re.sub(r'[^\w\-_.]', '_', name)
    return (name or "page")[:100]

def human_size(b):
    for u in ['B','KB','MB','GB']:
        if b < 1024: return f"{int(b)} {u}" if u == 'B' else f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

def now(): return datetime.now().strftime("%Y-%m-%d_%H%M%S")

def dns_check(url):
    try:
        socket.setdefaulttimeout(5)
        socket.gethostbyname(urlparse(url).hostname)
        return True, None
    except Exception as e: return False, str(e)


# ==============================================================================
# WEB SCRAPER
# ==============================================================================

class Scraper:
    def __init__(self):
        self.pw_ok = False
        self.req_ok = False
        try: import playwright; self.pw_ok = True
        except: pass
        try: import requests; self.req_ok = True
        except: pass
    
    def scrape(self, url, fmt="md", out_dir=None, use_cache=True, save_cookies=True):
        if use_cache:
            cached = CACHE.get(url, fmt)
            if cached: return self._from_cache(url, cached, fmt, out_dir)
        
        if out_dir is None: out_dir = os.path.join(BASE_DIR, "output", f"scraped_{now()}")
        os.makedirs(out_dir, exist_ok=True)
        
        result = {"url": url, "title": "", "status": "failed", "format": fmt, "file": None, "size": 0, "words": None, "blocked": False, "method": "none", "error": None, "time": 0}
        t0 = time.time()
        
        ok, err = dns_check(url)
        if not ok: return {**result, "error": err, "time": round(time.time()-t0, 2)}
        
        name = sanitize(url)
        path = os.path.join(out_dir, f"{name}.{fmt}")
        i = 2
        while os.path.exists(path): path = os.path.join(out_dir, f"{name}_{i}.{fmt}"); i += 1
        
        RATE.wait()
        
        if self.pw_ok:
            try:
                res = self._playwright(url, fmt, path, result, save_cookies)
                if res["status"] == "ok" and use_cache:
                    try: CACHE.set(url, open(path, encoding='utf-8').read(), fmt)
                    except: pass
                return res
            except Exception as e: result["error"] = str(e)
        
        if self.req_ok:
            try:
                res = self._requests(url, fmt, path, result, save_cookies)
                if res["status"] == "ok" and use_cache:
                    try: CACHE.set(url, open(path, encoding='utf-8').read(), fmt)
                    except: pass
                return res
            except Exception as e: result["error"] = f"{result.get('error','')}|{e}"
        
        result["time"] = round(time.time()-t0, 2)
        return result
    
    def _from_cache(self, url, content, fmt, out_dir):
        name = sanitize(url)
        path = os.path.join(out_dir, f"{name}.{fmt}")
        os.makedirs(out_dir, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f: f.write(content)
        return {"url": url, "title": "", "status": "ok", "format": fmt, "file": os.path.basename(path), "size": len(content), "words": len(content.split()), "blocked": False, "method": "cache", "cached": True, "_text": content}
    
    def _playwright(self, url, fmt, path, result, save_cookies):
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--disable-blink-features=AutomationControlled'])
            ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, user_agent=PROXY.get_headers()["User-Agent"])
            ctx.add_init_script(STEALTH_SCRIPT)
            page = ctx.new_page()
            
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try: page.wait_for_load_state("networkidle", timeout=15000)
                except: time.sleep(2)
                
                for _ in range(6):
                    page.mouse.wheel(0, random.randint(400, 800))
                    page.wait_for_timeout(random.randint(300, 500))
                
                title = page.title()
                result["title"] = title
                code = resp.status if resp else None
                body = page.locator('body').inner_text(timeout=5000)[:2000]
                result["blocked"] = is_blocked(title, body, code)
                
                if fmt == "pdf": page.pdf(path=path, format='A4', print_background=True, margin={'top': '0.5in', 'bottom': '0.5in', 'left': '0.5in', 'right': '0.5in'})
                elif fmt == "html": open(path, 'w', encoding='utf-8').write(page.content())
                elif fmt == "txt":
                    text = self._extract_text(page)
                    open(path, 'w', encoding='utf-8').write(text)
                    result["words"] = len(text.split())
                    result["_text"] = text
                elif fmt == "md":
                    html = self._extract_html(page)
                    md = self._to_md(html, url)
                    open(path, 'w', encoding='utf-8').write(f"# {title or url}\n\nSource: {url}\n\n---\n\n" + md)
                    result["words"] = len(md.split())
                    result["_text"] = md
                elif fmt == "docx":
                    text = self._extract_text(page)
                    self._to_docx(text, title or url, url, path)
                    result["words"] = len(text.split())
                    result["_text"] = text
                
                if save_cookies:
                    try: COOKIES.set(urlparse(url).netloc, ctx.cookies())
                    except: pass
                
                browser.close()
                result.update({"status": "ok", "file": os.path.basename(path), "size": os.path.getsize(path), "method": "playwright", "time": round(time.time()-result.get("_t0", time.time()), 2)})
                return result
            except Exception as e:
                browser.close()
                raise e
    
    def _requests(self, url, fmt, path, result, save_cookies):
        import requests
        from bs4 import BeautifulSoup
        
        headers = PROXY.get_headers()
        cookies = COOKIES.get(urlparse(url).netloc)
        resp = requests.get(url, headers=headers, cookies=cookies, timeout=30, allow_redirects=True)
        code = resp.status_code
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else ""
        result["title"] = title
        body = resp.text[:2000]
        result["blocked"] = is_blocked(title, body, code)
        
        if result["blocked"]: return {**result, "status": "blocked", "error": f"Blocked with status {code}"}
        
        if fmt == "html": open(path, 'w', encoding='utf-8').write(resp.text)
        elif fmt == "txt":
            text = soup.get_text("\n", strip=True)
            open(path, 'w', encoding='utf-8').write(text)
            result["words"] = len(text.split())
            result["_text"] = text
        elif fmt == "md":
            md = self._to_md(resp.text, url)
            open(path, 'w', encoding='utf-8').write(f"# {title or url}\n\nSource: {url} (fallback)\n\n---\n\n" + md)
            result["words"] = len(md.split())
            result["_text"] = md
        elif fmt == "docx":
            text = soup.get_text("\n", strip=True)
            self._to_docx(text, title or url, url, path)
            result["words"] = len(text.split())
            result["_text"] = text
        
        result.update({"status": "ok", "file": os.path.basename(path), "size": os.path.getsize(path), "method": "requests", "time": round(time.time()-result.get("_t0", time.time()), 2)})
        return result
    
    def _extract_text(self, page):
        try:
            text = page.evaluate("""
                () => {
                    const root = document.querySelector('article, main, [role=\"main\"], .article, .post, .content') || document.body;
                    const junk = root.querySelectorAll('script, style, nav, header, footer, aside, .cookie, .ad');
                    junk.forEach(n => n.remove());
                    return root.innerText;
                }
            """)
        except: text = page.locator('body').inner_text(timeout=20000)
        lines = [re.sub(r'[ \t]+', ' ', l).strip() for l in text.splitlines() if l.strip()]
        return '\n'.join(lines)
    
    def _extract_html(self, page):
        try: return page.evaluate("() => document.documentElement.outerHTML")
        except: return page.content()
    
    def _to_md(self, html, url):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]): tag.decompose()
        try:
            from markdownify import markdownify
            return markdownify(str(soup.body or soup), heading_style="ATX", bullets="-")
        except:
            lines = []
            for el in soup.find_all(["h1","h2","h3","h4","h5","h6","p","li"]):
                if el.name.startswith('h'): lines.append(f"{'#'*int(el.name[1])} {el.get_text(strip=True)}")
                elif el.name == "li": lines.append(f"- {el.get_text(strip=True)}")
                elif el.name == "p": lines.append(el.get_text(strip=True))
            return '\n\n'.join(lines)
    
    def _to_docx(self, text, title, url, path):
        try:
            from docx import Document
            doc = Document()
            doc.add_heading(title, 0)
            doc.add_paragraph(f"Source: {url}")
            for p in text.split('\n'):
                if p.strip(): doc.add_paragraph(p.strip())
            doc.save(path)
        except:
            with open(path.replace('.docx', '.txt'), 'w', encoding='utf-8') as f: f.write(text)


# ==============================================================================
# MAIN PROCESSOR
# ==============================================================================

class Processor:
    def __init__(self):
        self.scraper = Scraper()
        self.urls = {}
        self.files = {}
    
    def process_urls(self, urls, fmt=None, out_dir=None, use_cache=True, concurrency=None):
        if not urls: return {"error": "No URLs"}
        fmt = fmt or CONFIG.get("general", "output_format", "md")
        concurrency = concurrency or int(CONFIG.get("general", "concurrency", 2))
        if out_dir is None: out_dir = os.path.join(BASE_DIR, "output", f"batch_{now()}")
        os.makedirs(out_dir, exist_ok=True)
        
        results = {}
        lock = threading.Lock()
        
        def worker(url):
            try:
                res = self.scraper.scrape(url, fmt, out_dir, use_cache)
                with lock: results[url] = res; self.urls[url] = res
            except Exception as e:
                with lock: results[url] = {"status": "error", "error": str(e), "url": url}
        
        threads = []
        for url in urls:
            t = threading.Thread(target=worker, args=(url,))
            threads.append(t); t.start()
            if len(threads) >= concurrency:
                for th in threads: th.join()
                threads = []
        for th in threads: th.join()
        
        return self._summary(results)
    
    def _summary(self, results):
        total = len(results)
        ok = sum(1 for r in results.values() if r.get("status") == "ok")
        failed = total - ok
        blocked = sum(1 for r in results.values() if r.get("blocked"))
        cached = sum(1 for r in results.values() if r.get("cached"))
        size = sum(r.get("size", 0) for r in results.values())
        words = sum(r.get("words", 0) or 0 for r in results.values())
        return {"total": total, "ok": ok, "failed": failed, "blocked": blocked, "cached": cached, "size": size, "size_human": human_size(size), "words": words, "results": results, "timestamp": datetime.now().isoformat()}
    
    def process_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
            size = len(content)
            result = {"path": path, "name": os.path.basename(path), "size": size, "size_human": human_size(size), "lines": len(content.splitlines()), "words": len(content.split()), "status": "ok", "content": content[:5000]}
            self.files[path] = result
            return result
        except Exception as e: return {"path": path, "status": "error", "error": str(e)}
    
    def search(self, query, case_sensitive=False):
        results = {}
        q = query if case_sensitive else query.lower()
        for url, data in self.urls.items():
            if data.get("_text"):
                text = data["_text"] if case_sensitive else data["_text"].lower()
                matches = [(i+1, l[:200]) for i, l in enumerate(text.splitlines()) if q in l]
                if matches: results[f"URL: {url}"] = matches
        for path, data in self.files.items():
            if data.get("content"):
                text = data["content"] if case_sensitive else data["content"].lower()
                matches = [(i+1, l[:200]) for i, l in enumerate(text.splitlines()) if q in l]
                if matches: results[f"File: {data['name']}"] = matches
        return results
    
    def export(self, path=None):
        if path is None: path = os.path.join(BASE_DIR, "output", f"results_{now()}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {"app": APP_NAME, "version": APP_VERSION, "timestamp": datetime.now().isoformat(), "urls": self.urls, "files": self.files, "summary": {"url_count": len(self.urls), "file_count": len(self.files)}}
        with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return path
    
    def show_stats(self):
        print(f"\n{APP_NAME} v{APP_VERSION} - Statistics")
        print("=" * 50)
        print(f"Processed URLs: {len(self.urls)}")
        print(f"Processed Files: {len(self.files)}")
        print("=" * 50)


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    # Check dependencies
    DependencyInstaller().run()
    
    # Initialize
    processor = Processor()
    
    # Simple argument parsing
    args = {
        'urls': None, 'url': None, 'file': None, 'directory': None,
        'format': None, 'output': None, 'concurrency': None,
        'search': None, 'export': None, 'stats': False, 'no_cache': False, 'clear': False
    }
    
    i = 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a in ['--urls', '-u']: args['urls'] = sys.argv[i+1:i+1+int(sys.argv[i+1].count(',')+1)]; i += 2
        elif a in ['--url']: args['url'] = sys.argv[i+1]; i += 2
        elif a in ['--file']: args['file'] = sys.argv[i+1]; i += 2
        elif a in ['--directory', '-d']: args['directory'] = sys.argv[i+1]; i += 2
        elif a in ['--format', '-f']: args['format'] = sys.argv[i+1]; i += 2
        elif a in ['--output', '-o']: args['output'] = sys.argv[i+1]; i += 2
        elif a in ['--concurrency', '-c']: args['concurrency'] = int(sys.argv[i+1]); i += 2
        elif a in ['--search', '-s']: args['search'] = sys.argv[i+1]; i += 2
        elif a in ['--export', '-e']: args['export'] = sys.argv[i+1]; i += 2
        elif a in ['--stats']: args['stats'] = True; i += 1
        elif a in ['--no-cache']: args['no_cache'] = True; i += 1
        elif a in ['--clear']: args['clear'] = True; i += 1
        else: i += 1
    
    # Process URLs
    urls = []
    if args['urls']: urls = [u.strip() for u in ' '.join(args['urls']).split(',') if u.strip()]
    if args['url']: urls.append(args['url'])
    
    if urls:
        print(f"Processing {len(urls)} URLs...")
        result = processor.process_urls(urls, args['format'], args['output'], not args['no_cache'], args['concurrency'])
        print(f"Done! {result['ok']}/{result['total']} successful, {result['failed']} failed, {result['blocked']} blocked, {result['cached']} cached")
        if args['export']: processor.export(args['export'])
        else: processor.export()
    
    # Process file
    if args['file']:
        print(f"Processing file: {args['file']}")
        processor.process_file(args['file'])
    
    # Process directory
    if args['directory']:
        print(f"Processing directory: {args['directory']}")
        for root, _, files in os.walk(args['directory']):
            for f in files: processor.process_file(os.path.join(root, f))
        print(f"Processed {len(processor.files)} files")
    
    # Search
    if args['search']:
        print(f"Searching for: '{args['search']}'")
        results = processor.search(args['search'])
        if not results: print("No matches")
        else:
            for src, matches in results.items():
                print(f"\n{src}:")
                for ln, txt in matches: print(f"  Line {ln}: {txt}")
    
    # Stats
    if args['stats'] or not any([urls, args['file'], args['directory'], args['search'], args['clear']]):
        processor.show_stats()
    
    # Clear cache
    if args['clear']: CACHE.clear(); print("Cache cleared")
    
    # Export
    if args['export'] and not urls: processor.export(args['export'])


if __name__ == '__main__':
    main()
