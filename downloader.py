#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
منطق التحميل: Playwright (Persistent Context) + التقاط الشبكة + yt-dlp
- يفتح المتصفح مرة واحدة لتسجيل الدخول ويحفظ الجلسة في مجلد دائم
- عند التحميل: يفتح الصفحة، يشغّل الفيديو، يلتقط طلبات .mp4 / .m3u8 بصمت
- يحمّل بأفضل جودة عبر yt-dlp
"""
import os
import re
import sys
import time
import threading
from pathlib import Path


def _appdata_base() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "ZoomDownloader"
    return Path.home() / ".zoom_downloader"


def get_user_data_dir() -> str:
    """مجلد ملف تعريف المتصفح الدائم (Persistent Context)."""
    p = _appdata_base() / "browser_profile"
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


def _app_dir() -> Path:
    """مجلد البرنامج (داخل EXE المجمّع أو مجلد السكربت أثناء التطوير)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def setup_bundled_tools():
    """يوجّه Playwright إلى Chromium المضمّن، ويضيف ffmpeg المضمّن إلى PATH."""
    app = _app_dir()
    browsers = app / "ms-playwright"
    if browsers.exists():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers)
    if (app / "ffmpeg.exe").exists():
        os.environ["PATH"] = str(app) + os.pathsep + os.environ.get("PATH", "")


def get_default_save_dir() -> str:
    if os.name == "nt":
        videos = Path.home() / "Videos" / "ZoomDownloads"
    else:
        videos = Path.home() / "Videos" / "ZoomDownloads"
    videos.mkdir(parents=True, exist_ok=True)
    return str(videos)


VIDEO_URL_RE = re.compile(r"\.(mp4|m3u8)(\?|$)", re.IGNORECASE)


class ZoomDownloader:
    def __init__(self, save_dir: str, log_callback=None, progress_callback=None):
        self.save_dir = save_dir
        self.log = log_callback or (lambda m: print(m, flush=True))
        self.progress_cb = progress_callback or (lambda p: None)
        self._found_urls: list[str] = []
        self._stop_capture = threading.Event()

    # ---------- المتصفح ----------

    def _launch_context(self, playwright, headless: bool = False):
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=get_user_data_dir(),
            headless=headless,
            accept_downloads=True,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        return browser

    def open_login_window(self):
        """يفتح المتصفح ليدخل المستخدم لحساب زوم يدوياً ثم يغلقه."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            ctx = self._launch_context(pw, headless=False)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            self.log("🌐 تم فتح المتصفح. سجّل الدخول في Zoom ثم أغلق نافذة المتصفح.")
            page.goto("https://events.zoom.us/", wait_until="domcontentloaded")
            # انتظر حتى يغلق المستخدم المتصفح يدوياً
            try:
                while ctx.pages:
                    time.sleep(1)
            except Exception:
                pass
            finally:
                try:
                    ctx.close()
                except Exception:
                    pass

    # ---------- التقاط رابط الفيديو ----------

    def _on_response(self, response):
        try:
            url = response.url
            if VIDEO_URL_RE.search(url):
                # تجاهل الملفات الصغيرة/الإعلانات الشائعة
                if url not in self._found_urls:
                    self._found_urls.append(url)
                    self.log(f"🔗 تم اكتشاف رابط فيديو: {url[:120]}...")
        except Exception:
            pass

    def _on_request(self, request):
        try:
            url = request.url
            if VIDEO_URL_RE.search(url) and url not in self._found_urls:
                self._found_urls.append(url)
                self.log(f"🔗 تم اكتشاف رابط فيديو: {url[:120]}...")
        except Exception:
            pass

    def _extract_with_playwright(self, url: str, timeout_s: int = 90) -> str | None:
        from playwright.sync_api import sync_playwright

        self._found_urls = []
        with sync_playwright() as pw:
            ctx = self._launch_context(pw, headless=False)
            # حمّل الإضافة/التبعيات: التقاط كل الاستجابات والطلبات
            ctx.on("response", self._on_response)
            ctx.on("request", self._on_request)

            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            self.log(f"🌐 فتح صفحة التسجيل...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)

            # محاولة الضغط على زر التشغيل تلقائياً
            for selector in [
                "video",
                'button[aria-label*="Play" i]',
                'button[aria-label*="play" i]',
                '[class*="play"]',
                'button:has-text("Play")',
            ]:
                try:
                    el = page.query_selector(selector)
                    if el:
                        try:
                            el.click(timeout=3000)
                            self.log("▶️ تم الضغط على زر التشغيل.")
                            break
                        except Exception:
                            pass
                except Exception:
                    pass

            # انتظر ظهور رابط الفيديو
            self.log("⏳ بانتظار اكتشاف رابط الفيديو (.mp4 / .m3u8)... شغّل الفيديو إذا لزم.")
            waited = 0
            while waited < timeout_s:
                if self._found_urls:
                    break
                # ابحث أيضاً داخل عناصر <video> و <source>
                try:
                    srcs = page.eval_on_selector_all(
                        "video, source",
                        "els => els.map(e => e.src || e.getAttribute('src')).filter(Boolean)"
                    )
                    for s in srcs or []:
                        if VIDEO_URL_RE.search(s) and s not in self._found_urls:
                            self._found_urls.append(s)
                            self.log(f"🔗 رابط من عنصر video: {s[:120]}...")
                            break
                    if self._found_urls:
                        break
                except Exception:
                    pass
                time.sleep(2)
                waited += 2
                if waited % 10 == 0:
                    self.progress_cb(min(30, waited // 3))
                    self.log(f"⏳ ما زلت أراقب الشبكة... ({waited}s)")

            try:
                ctx.close()
            except Exception:
                pass

        if self._found_urls:
            # فضّل mp4 المباشر، ثم m3u8
            mp4s = [u for u in self._found_urls if ".mp4" in u.lower()]
            best = mp4s[0] if mp4s else self._found_urls[0]
            return best
        return None

    # ---------- التحميل عبر yt-dlp ----------

    def _progress_hook(self, d):
        try:
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    pct = int(downloaded * 100 / total)
                    # احجز 30% لمرحلة الاكتشاف، 70% للتحميل
                    self.progress_cb(30 + int(pct * 0.7))
            elif d.get("status") == "finished":
                self.progress_cb(100)
        except Exception:
            pass

    def _download_with_ytdlp(self, video_url: str, referer: str) -> tuple[bool, str]:
        import yt_dlp

        Path(self.save_dir).mkdir(parents=True, exist_ok=True)
        outtmpl = str(Path(self.save_dir) / "%(title).80s [%(id)s].%(ext)s")

        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "progress_hooks": [self._progress_hook],
            "http_headers": {
                "Referer": referer,
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                ),
            },
            "retries": 5,
            "concurrent_fragment_downloads": 4,
        }

        self.log("⬇️ بدء التنزيل بأفضل جودة عبر yt-dlp...")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)
                return True, filename
        except Exception as e:
            # خطة بديلة: جرّب الرابط الأصلي مباشرة مع yt-dlp (قد يعالج صفحة زوم نفسها)
            self.log(f"⚠️ فشل الرابط المباشر ({e}). أجرّب رابط الصفحة مباشرة...")
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(referer, download=True)
                    filename = ydl.prepare_filename(info)
                    return True, filename
            except Exception as e2:
                return False, f"{e} | {e2}"

    # ---------- الواجهة الرئيسية ----------

    def download(self, url: str) -> tuple[bool, str]:
        self.progress_cb(5)
        self.log("🔍 الخطوة 1/2: اكتشاف رابط الفيديو من الشبكة...")
        video_url = self._extract_with_playwright(url)

        if video_url:
            self.log(f"✅ تم العثور على الفيديو. التحميل الآن...")
            self.progress_cb(30)
            return self._download_with_ytdlp(video_url, referer=url)

        # لم يُعثر على رابط مباشر → جرّب yt-dlp على الصفحة مباشرة
        self.log("⚠️ لم يُكتشف رابط مباشر. أجرّب yt-dlp على الصفحة مباشرة...")
        self.progress_cb(30)
        return self._download_with_ytdlp(url, referer=url)
