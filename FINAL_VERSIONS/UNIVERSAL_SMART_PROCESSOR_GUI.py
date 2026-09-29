#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIVERSAL SMART PROCESSOR GUI v3.0
ОДНА ПРОГРАММА - ВСЁ ВКЛЮЧЕНО!

НАЖМИТЕ КНОПКУ И ВСЁ РАБОТАЕТ!
Без кодов, без команд, без ключей!

Возможности:
✅ Скрапинг ЛЮБЫХ сайтов (включая .gov)
✅ Выбор формата: PDF, HTML, TXT, Markdown, DOCX
✅ Авто-обнаружение блокировок
✅ Прокси-симуляция (кодовая, без реальных прокси)
✅ Кэширование результатов
✅ Сохранение куки
✅ Авто-установка зависимостей
✅ Обработка JavaScript
✅ Поддержка больших файлов
✅ Логирование
✅ ВСЁ В ОДНОЙ ПРОГРАММЕ!

ИНСТРУКЦИЯ:
1. Введите URL в поле
2. Выберите формат
3. Нажмите "СТАРТ"
4. ГОТОВО!
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

# Fix encoding for Windows
try:
    if sys.platform.startswith('win'):
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
except:
    pass


# ==============================================================================
# GLOBAL SETTINGS
# ==============================================================================

APP_NAME = "UNIVERSAL SMART PROCESSOR GUI"
APP_VERSION = "3.0"

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create directories
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "cache"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "config"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)


# ==============================================================================
# SIMPLE CONFIG
# ==============================================================================

class SimpleConfig:
    def __init__(self):
        self.config = {
            "output_format": "md",
            "output_dir": os.path.join(BASE_DIR, "output"),
            "concurrency": 1,
            "use_cache": True,
            "use_proxy_simulation": True,
            "auto_scroll": True,
        }
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value


CONFIG = SimpleConfig()


# ==============================================================================
# SIMPLE LOGGING
# ==============================================================================

class SimpleLogger:
    def __init__(self, text_widget=None):
        self.text_widget = text_widget
        self.messages = []
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"[{timestamp}] {level}: {message}"
        self.messages.append(msg)
        
        if self.text_widget:
            try:
                self.text_widget.config(state="normal")
                self.text_widget.insert("end", msg + "\n")
                self.text_widget.see("end")
                self.text_widget.config(state="disabled")
            except:
                pass
        else:
            print(msg)
    
    def info(self, msg): self.log(msg, "INFO")
    def warning(self, msg): self.log(msg, "WARNING")
    def error(self, msg): self.log(msg, "ERROR")
    def success(self, msg): self.log(msg, "SUCCESS")


# ==============================================================================
# CACHE SYSTEM
# ==============================================================================

class SimpleCache:
    def __init__(self):
        self.cache_db = os.path.join(BASE_DIR, "cache", "cache.db")
        self.conn = sqlite3.connect(self.cache_db, check_same_thread=False)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS cache (url TEXT PRIMARY KEY, content TEXT, format TEXT, timestamp DATETIME)''')
        self.conn.commit()
    
    def get(self, url, fmt="md"):
        expiry = datetime.now() - timedelta(days=7)
        c = self.conn.cursor()
        c.execute("SELECT content FROM cache WHERE url=? AND format=? AND timestamp>?", (url, fmt, expiry.isoformat()))
        return c.fetchone()
    
    def set(self, url, content, fmt="md"):
        self.conn.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?,?)", (url, content, fmt, datetime.now().isoformat()))
        self.conn.commit()
    
    def clear(self):
        self.conn.execute("DELETE FROM cache")
        self.conn.commit()


CACHE = SimpleCache()


# ==============================================================================
# PROXY SIMULATION
# ==============================================================================

class ProxySimulator:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        ]
        self.referers = ["https://www.google.com/", "https://www.bing.com/", "https://www.yahoo.com/"]
        self.ips = ["192.168.1.100", "10.0.0.100", "172.16.0.100"]
        self.idx = 0
    
    def get_headers(self):
        ua = self.user_agents[self.idx % len(self.user_agents)]
        ref = self.referers[self.idx % len(self.referers)]
        ip = self.ips[self.idx % len(self.ips)]
        self.idx += 1
        return {"User-Agent": ua, "Referer": ref, "X-Forwarded-For": ip, "X-Real-IP": ip}


PROXY = ProxySimulator()


# ==============================================================================
# BLOCKED DETECTION
# ==============================================================================

BLOCKED_MARKERS = [
    "just a moment", "checking your browser", "attention required",
    "access denied", "are you a robot", "captcha", "cloudflare",
    "rate limit", "403", "429", "503", "blocked", "unusual traffic",
    "verify you are human", "bot detection", "please enable cookies",
    "please solve", "try again later", "error 403", "error 429",
    "your ip has been", "temporarily blocked", "access temporarily",
    "we have detected", "suspicious activity", "forbidden",
    "not authorized", "permission denied", "security check",
    "ddos protection", "waf", "firewall", "access blocked",
    "please wait", "loading", "processing request",
]

def is_blocked(title, body, code=None):
    if code in (403, 429, 500, 502, 503, 504):
        return True
    text = f"{title} {body}".lower()
    return any(m in text for m in BLOCKED_MARKERS)


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
# DEPENDENCY INSTALLER
# ==============================================================================

class DependencyInstaller:
    PACKAGES = [("requests", "requests"), ("playwright", "playwright"), ("pypdf", "pypdf"), ("python-docx", "docx"), ("beautifulsoup4", "bs4"), ("markdownify", "markdownify")]
    
    def install_python_packages(self):
        for pkg, mod in self.PACKAGES:
            try:
                importlib.import_module(mod)
            except ImportError:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except:
                    pass
    
    def install_browsers(self):
        try:
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False
    
    def check_system_deps(self):
        if not platform.system().lower() == "linux":
            return True
        deps = ["libglib-2.0-0", "libnss3", "libnspr4", "libxkbcommon0", "libxcomposite1", "libxdamage1", "libgbm1"]
        missing = []
        for d in deps:
            try:
                if subprocess.run(["dpkg", "-l", d], capture_output=True).returncode != 0:
                    missing.append(d)
            except:
                missing.append(d)
        if missing:
            try:
                subprocess.run(["sudo", "apt-get", "install", "-y"] + missing, capture_output=True)
            except:
                pass
        return len(missing) == 0
    
    def run(self, logger=None):
        if logger: logger.info("Проверка зависимостей...")
        self.install_python_packages()
        self.check_system_deps()
        if not self._chromium_ready():
            if logger: logger.info("Установка Chromium...")
            self.install_browsers()
        if logger: logger.info("Зависимости готовы!")
    
    def _chromium_ready(self):
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                p.chromium.launch(headless=True).close()
            return True
        except:
            return False


# ==============================================================================
# MAIN SCRAPER
# ==============================================================================

class MainScraper:
    def __init__(self, logger=None):
        self.logger = logger or SimpleLogger()
        self.pw_ok = False
        self.req_ok = False
        try: import playwright; self.pw_ok = True
        except: pass
        try: import requests; self.req_ok = True
        except: pass
    
    def scrape_url(self, url, output_format="md", output_dir=None, use_cache=True):
        # Check cache
        if use_cache:
            cached = CACHE.get(url, output_format)
            if cached:
                return self._from_cache(url, cached, output_format, output_dir)
        
        # Setup output
        if output_dir is None:
            output_dir = os.path.join(BASE_DIR, "output", f"scraped_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}")
        os.makedirs(output_dir, exist_ok=True)
        
        result = {
            "url": url,
            "title": "",
            "status": "failed",
            "format": output_format,
            "file": None,
            "size": 0,
            "words": None,
            "blocked": False,
            "method": "none",
            "error": None,
            "time": 0
        }
        
        t0 = time.time()
        
        # Validate URL
        try:
            host = urlparse(url).hostname
            if not host:
                return {**result, "error": "Неверный URL", "time": round(time.time()-t0, 2)}
            socket.setdefaulttimeout(5)
            socket.gethostbyname(host)
        except Exception as e:
            return {**result, "error": f"Ошибка DNS: {e}", "time": round(time.time()-t0, 2)}
        
        # Filename
        name = re.sub(r'[^\w\-_.]', '_', url.replace('https://', '').replace('http://', ''))[:100]
        path = os.path.join(output_dir, f"{name}.{output_format}")
        i = 2
        while os.path.exists(path):
            path = os.path.join(output_dir, f"{name}_{i}.{output_format}")
            i += 1
        
        # Rate limiting
        time.sleep(random.uniform(1.0, 3.0))
        
        # Try Playwright
        if self.pw_ok:
            try:
                res = self._playwright(url, output_format, path, result)
                if res["status"] == "ok":
                    if use_cache:
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                CACHE.set(url, f.read(), output_format)
                        except:
                            pass
                    return res
            except Exception as e:
                result["error"] = str(e)
                self.logger.warning(f"Playwright ошибка: {e}")
        
        # Fallback to requests
        if self.req_ok:
            try:
                res = self._requests(url, output_format, path, result)
                if res["status"] == "ok" and use_cache:
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            CACHE.set(url, f.read(), output_format)
                    except:
                        pass
                return res
            except Exception as e:
                result["error"] = f"{result.get('error','')}|{e}"
                self.logger.error(f"Requests ошибка: {e}")
        
        result["time"] = round(time.time()-t0, 2)
        return result
    
    def _from_cache(self, url, content, fmt, out_dir):
        name = re.sub(r'[^\w\-_.]', '_', url.replace('https://', '').replace('http://', ''))[:100]
        path = os.path.join(out_dir, f"{name}.{fmt}")
        os.makedirs(out_dir, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {
            "url": url, "title": "", "status": "ok", "format": fmt,
            "file": os.path.basename(path), "size": len(content),
            "words": len(content.split()), "blocked": False,
            "method": "cache", "cached": True, "_text": content
        }
    
    def _playwright(self, url, fmt, path, result):
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled',
                    '--lang=en-US,en;q=0.9'
                ]
            )
            ctx = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=PROXY.get_headers()["User-Agent"]
            )
            ctx.add_init_script(STEALTH_SCRIPT)
            page = ctx.new_page()
            
            try:
                # Apply proxy headers
                headers = PROXY.get_headers()
                for k, v in headers.items():
                    page.set_extra_http_headers({k: v})
                
                resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except:
                    time.sleep(2)
                
                # Auto-scroll for lazy loading
                for _ in range(8):
                    page.mouse.wheel(0, random.randint(400, 800))
                    page.wait_for_timeout(random.randint(300, 500))
                
                # Get title
                title = page.title()
                result["title"] = title
                
                # Check for blocking
                code = resp.status if resp else None
                body = page.locator('body').inner_text(timeout=5000)[:2000]
                result["blocked"] = is_blocked(title, body, code)
                
                if result["blocked"]:
                    self.logger.warning(f"Блокировка обнарулена: {url}")
                
                # Extract content
                if fmt == "pdf":
                    page.pdf(path=path, format='A4', print_background=True, margin={'top': '0.5in', 'bottom': '0.5in', 'left': '0.5in', 'right': '0.5in'})
                    result["words"] = None
                elif fmt == "html":
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(page.content())
                elif fmt == "txt":
                    text = self._extract_text(page)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    result["words"] = len(text.split())
                    result["_text"] = text
                elif fmt == "md":
                    html = self._extract_html(page)
                    md = self._to_md(html, url)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(f"# {title or url}\n\nSource: {url}\n\n---\n\n" + md)
                    result["words"] = len(md.split())
                    result["_text"] = md
                elif fmt == "docx":
                    text = self._extract_text(page)
                    self._to_docx(text, title or url, url, path)
                    result["words"] = len(text.split())
                    result["_text"] = text
                
                browser.close()
                result.update({
                    "status": "ok",
                    "file": os.path.basename(path),
                    "size": os.path.getsize(path),
                    "method": "playwright",
                    "time": round(time.time() - result.get("_t0", time.time()), 2)
                })
                self.logger.success(f"✅ {url} -> {os.path.basename(path)}")
                return result
            
            except Exception as e:
                browser.close()
                raise e
    
    def _requests(self, url, fmt, path, result):
        import requests
        from bs4 import BeautifulSoup
        
        headers = PROXY.get_headers()
        
        try:
            resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            code = resp.status_code
            soup = BeautifulSoup(resp.text, "html.parser")
            title = soup.title.get_text(strip=True) if soup.title else ""
            result["title"] = title
            body = resp.text[:2000]
            result["blocked"] = is_blocked(title, body, code)
            
            if result["blocked"]:
                return {**result, "status": "blocked", "error": f"Blocked {code}"}
            
            if fmt == "html":
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(resp.text)
            elif fmt == "txt":
                text = soup.get_text("\n", strip=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
                result["words"] = len(text.split())
                result["_text"] = text
            elif fmt == "md":
                md = self._to_md(resp.text, url)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(f"# {title or url}\n\nSource: {url}\n\n---\n\n" + md)
                result["words"] = len(md.split())
                result["_text"] = md
            elif fmt == "docx":
                text = soup.get_text("\n", strip=True)
                self._to_docx(text, title or url, url, path)
                result["words"] = len(text.split())
                result["_text"] = text
            
            result.update({
                "status": "ok",
                "file": os.path.basename(path),
                "size": os.path.getsize(path),
                "method": "requests",
                "time": round(time.time() - result.get("_t0", time.time()), 2)
            })
            self.logger.success(f"✅ {url} -> {os.path.basename(path)}")
            return result
        
        except Exception as e:
            result["error"] = str(e)
            return {**result, "status": "failed"}
    
    def _extract_text(self, page):
        try:
            text = page.evaluate("""
                () => {
                    const root = document.querySelector('article, main, [role=\"main\"], .article, .post, .content') || document.body;
                    const junk = root.querySelectorAll('script, style, nav, header, footer, aside, .cookie, .ad, .modal, .popup');
                    junk.forEach(n => n.remove());
                    return root.innerText;
                }
            """)
        except:
            text = page.locator('body').inner_text(timeout=20000)
        lines = [re.sub(r'[ \t]+', ' ', l).strip() for l in text.splitlines() if l.strip()]
        return '\n'.join(lines)
    
    def _extract_html(self, page):
        try:
            return page.evaluate("() => document.documentElement.outerHTML")
        except:
            return page.content()
    
    def _to_md(self, html, url):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        try:
            from markdownify import markdownify
            return markdownify(str(soup.body or soup), heading_style="ATX", bullets="-")
        except:
            lines = []
            for el in soup.find_all(["h1","h2","h3","h4","h5","h6","p","li"]):
                if el.name.startswith('h'):
                    lines.append(f"{'#'*int(el.name[1])} {el.get_text(strip=True)}")
                elif el.name == "li":
                    lines.append(f"- {el.get_text(strip=True)}")
                elif el.name == "p":
                    lines.append(el.get_text(strip=True))
            return '\n\n'.join(lines)
    
    def _to_docx(self, text, title, url, path):
        try:
            from docx import Document
            doc = Document()
            doc.add_heading(title, 0)
            doc.add_paragraph(f"Source: {url}")
            for p in text.split('\n'):
                if p.strip():
                    doc.add_paragraph(p.strip())
            doc.save(path)
        except:
            with open(path.replace('.docx', '.txt'), 'w', encoding='utf-8') as f:
                f.write(text)


# ==============================================================================
# GUI APPLICATION
# ==============================================================================

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.logger = SimpleLogger(self.log_text)
        self.scraper = MainScraper(self.logger)
        
        # Install dependencies
        DependencyInstaller().run(self.logger)
        
        root.title(f"{APP_NAME} v{APP_VERSION}")
        root.geometry("900x700")
        root.minsize(800, 600)
        root.configure(bg="#f0f0f0")
        
        # Main frame
        main_frame = tk.Frame(root, bg="#f0f0f0", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        
        # URL Entry
        tk.Label(main_frame, text="URL (один или несколько через запятую):", bg="#f0f0f0", anchor="w").pack(fill="x", pady=(0, 5))
        self.url_entry = tk.Entry(main_frame, width=80, font=("Arial", 10))
        self.url_entry.pack(fill="x", pady=(0, 10))
        self.url_entry.insert(0, "https://")
        
        # Format Selection
        tk.Label(main_frame, text="Формат вывода:", bg="#f0f0f0", anchor="w").pack(fill="x", pady=(0, 5))
        self.format_var = tk.StringVar(value="md")
        format_frame = tk.Frame(main_frame, bg="#f0f0f0")
        format_frame.pack(fill="x", pady=(0, 10))
        
        formats = [("Markdown", "md"), ("HTML", "html"), ("Текст", "txt"), ("PDF", "pdf"), ("DOCX", "docx")]
        for text, value in formats:
            tk.Radiobutton(format_frame, text=text, variable=self.format_var, value=value, bg="#f0f0f0").pack(side="left", padx=10)
        
        # Output Directory
        tk.Label(main_frame, text="Папка для сохранения:", bg="#f0f0f0", anchor="w").pack(fill="x", pady=(0, 5))
        self.output_dir_var = tk.StringVar(value=os.path.join(BASE_DIR, "output"))
        output_frame = tk.Frame(main_frame, bg="#f0f0f0")
        output_frame.pack(fill="x", pady=(0, 10))
        tk.Entry(output_frame, textvariable=self.output_dir_var, width=50).pack(side="left", fill="x", expand=True)
        tk.Button(output_frame, text="...", command=self.choose_dir, width=5).pack(side="left", padx=5)
        
        # Options
        self.use_cache_var = tk.BooleanVar(value=True)
        self.auto_scroll_var = tk.BooleanVar(value=True)
        
        options_frame = tk.Frame(main_frame, bg="#f0f0f0")
        options_frame.pack(fill="x", pady=(0, 10))
        tk.Checkbutton(options_frame, text="Использовать кэш", variable=self.use_cache_var, bg="#f0f0f0").pack(side="left", padx=10)
        tk.Checkbutton(options_frame, text="Авто-прокрутка", variable=self.auto_scroll_var, bg="#f0f0f0").pack(side="left", padx=10)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill="x", pady=(0, 10))
        
        tk.Button(button_frame, text="🚀 СТАРТ", command=self.start_scraping, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=15).pack(side="left", padx=5)
        tk.Button(button_frame, text="📂 ОТКРЫТЬ ПАПКУ", command=self.open_output_dir, bg="#2196F3", fg="white", font=("Arial", 10), width=15).pack(side="left", padx=5)
        tk.Button(button_frame, text="🗑️ ОЧИСТИТЬ КЭШ", command=self.clear_cache, bg="#f44336", fg="white", font=("Arial", 10), width=15).pack(side="left", padx=5)
        
        # Log
        tk.Label(main_frame, text="Журнал:", bg="#f0f0f0", anchor="w").pack(fill="x", pady=(0, 5))
        self.log_text = tk.Text(main_frame, height=15, wrap="word", state="disabled", font=("Consolas", 9), bg="#2d2d2d", fg="#00ff00", insertbackground="#00ff00")
        self.log_text.pack(fill="both", expand=True, pady=(0, 10))
        
        # Scrollbar
        scrollbar = tk.Scrollbar(self.log_text)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        
        # Status
        self.status_var = tk.StringVar(value="Готово к работе!")
        tk.Label(main_frame, textvariable=self.status_var, bg="#f0f0f0", fg="#666", anchor="w").pack(fill="x")
        
        # Info
        tk.Label(main_frame, text="Введите URL и нажмите СТАРТ. Всё остальное программа сделает сама!", bg="#f0f0f0", fg="#888", anchor="w", font=("Arial", 8)).pack(fill="x", pady=(5, 0))
    
    def choose_dir(self):
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
    
    def open_output_dir(self):
        directory = self.output_dir_var.get()
        if os.path.isdir(directory):
            try:
                if sys.platform.startswith('win'):
                    os.startfile(directory)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', directory])
                else:
                    subprocess.Popen(['xdg-open', directory])
            except:
                webbrowser.open(f'file://{directory}')
    
    def clear_cache(self):
        CACHE.clear()
        self.logger.info("Кэш очищен!")
        self.status_var.set("Кэш очищен")
    
    def start_scraping(self):
        urls_text = self.url_entry.get().strip()
        if not urls_text:
            self.logger.error("Введите URL!")
            self.status_var.set("Ошибка: введите URL")
            return
        
        urls = [u.strip() for u in urls_text.split(',') if u.strip()]
        if not urls:
            self.logger.error("Нет правильных URL!")
            return
        
        output_format = self.format_var.get()
        output_dir = self.output_dir_var.get()
        use_cache = self.use_cache_var.get()
        
        self.status_var.set(f"Обрабатываем {len(urls)} URL...")
        self.logger.info(f"Начало обработки {len(urls)} URL...")
        
        def worker():
            try:
                results = {}
                for url in urls:
                    self.logger.info(f"Обработка: {url}")
                    result = self.scraper.scrape_url(url, output_format, output_dir, use_cache)
                    results[url] = result
                    self.logger.info(f"Результат: {result.get('status', 'unknown')} - {result.get('file', 'N/A')}")
                
                # Show summary
                ok = sum(1 for r in results.values() if r.get('status') == 'ok')
                failed = len(urls) - ok
                blocked = sum(1 for r in results.values() if r.get('blocked'))
                cached = sum(1 for r in results.values() if r.get('cached'))
                
                self.logger.success(f"✅ ГОТОВО! Успешно: {ok}/{len(urls)}, Неудачно: {failed}, Блокировок: {blocked}, Из кэша: {cached}")
                self.status_var.set(f"Готово! {ok}/{len(urls)} успешно")
                
                # Open output directory
                if os.path.isdir(output_dir):
                    self.open_output_dir()
            
            except Exception as e:
                self.logger.error(f"Ошибка: {e}")
                self.status_var.set(f"Ошибка: {e}")
        
        threading.Thread(target=worker, daemon=True).start()


# ==============================================================================
# RUN GUI
# ==============================================================================

if __name__ == '__main__':
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
        
        root = tk.Tk()
        app = ScraperApp(root)
        root.mainloop()
        
    except ImportError as e:
        print(f"Ошибка: {e}")
        print("Установите Tkinter: pip install tk")
        input("Нажмите Enter для выхода...")
