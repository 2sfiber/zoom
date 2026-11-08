# 🎥 ZoomDownloader — دليل البناء والتثبيت (ويندوز)

تم تنفيذ المشروع كاملاً برمجياً: واجهة PyQt6 + Playwright (بروفايل دائم) + التقاط شبكة صامت + yt-dlp بخيوط منفصلة + تغليف PyInstaller + مثبت Inno Setup مع اختصار سطح المكتب.

## 📁 محتويات المشروع

| الملف | الوظيفة |
|---|---|
| `main.py` | الواجهة الرسومية (رابط + مسار حفظ + Logs + Progress Bar) |
| `downloader.py` | Playwright Persistent Context + التقاط `.mp4` / `.m3u8` + تحميل yt-dlp |
| `requirements.txt` | `PyQt6 + playwright + yt-dlp` |
| `ZoomDownloader.spec` | إعداد PyInstaller لإنتاج `.exe` مستقل بدون نافذة سوداء |
| `build_windows.bat` | بناء كل شيء بنقرة واحدة على ويندوز |
| `installer/setup.iss` | معالج التثبيت الاحترافي (Inno Setup) + اختصار سطح المكتب |
| `installer/install.bat` | يجلب التبعيات الناقصة (Chromium / ffmpeg) تلقائياً بعد التثبيت |

## 🖥️ طريقة البناء على ويندوز (5 دقائق)

> ⚠️ ملف الـ `.exe` النهائي **يجب بناؤه على جهاز ويندوز** (لا يمكن إنتاج exe ويندوز من سيرفر لينكس).
> كل شيء آلي — فقط نفّذ:

1. ثبّت **Python 3.10+** من `python.org` (مع تفعيل ✅ Add to PATH).
2. ثبّت **Inno Setup 6** من `https://jrsoftware.org/isdl.php`.
3. انسخ مجلد `zoom-downloader` إلى جهاز الويندوز.
4. دبل-كليك على **`build_windows.bat`** — سيقوم تلقائياً بـ:
   - `pip install -r requirements.txt`
   - `playwright install chromium` (متصفح مدمج + بروفايل دائم لتسجيل الدخول مرة واحدة)
   - `PyInstaller ZoomDownloader.spec` → ينتج `dist\ZoomDownloader\ZoomDownloader.exe`
   - جلب `ffmpeg.exe` تلقائياً (لدمج m3u8)
   - بناء المثبت عبر Inno Setup → `installer\Output\ZoomDownloader-Setup.exe`
5. وزّع ملف **`ZoomDownloader-Setup.exe`** — يثبت البرنامج + ينشئ **اختصار سطح مكتب** + يجلب أي تبعيات ناقصة تلقائياً.

## 🚀 طريقة الاستخدام

1. افتح البرنامج → اضغط **"🔑 فتح المتصفح لتسجيل الدخول"** → سجّل الدخول في Zoom مرة واحدة → أغلق المتصفح (الجلسة تُحفظ في `%APPDATA%\ZoomDownloader\browser_profile`).
2. الصق رابط التسجيل → اختر مسار الحفظ → **"⬇️ بدء التحميل"**.
3. راقب `Logs` وشريط التقدم. يُحفظ الفيديو بأفضل جودة `.mp4`.

## ⚙️ كيف يعمل؟

- **Persistent Context**: `launch_persistent_context(user_data_dir=...)` يحفظ الكوكيز/الجلسة فلا حاجة لتسجيل الدخول كل مرة.
- **التقاط صامت**: مستمعون على `request` و `response` يلتقطون أي URL فيه `.mp4` أو `.m3u8` أثناء تشغيل الفيديو، + فحص عناصر `<video>`، + ضغط زر Play تلقائياً.
- **عدم التجميد**: التحميل يعمل في `threading.Thread` منفصل، والتقدم يصل للواجهة عبر `pyqtSignal`.
- **yt-dlp**: `bestvideo+bestaudio/best` مع دمج `mp4` و `concurrent_fragment_downloads=4` لتسريع m3u8، وخطة بديلة بتحميل الصفحة مباشرة إن تعذّر الالتقاط.

## ❓ لماذا لا يوجد رابط تحميل مباشر هنا؟

بيئة البناء الحالية سيرفر **لينكس سحابي** — لا يمكنها إنتاج أو استضافة `.exe` ويندوز موقّع. المخرجات الجاهزة هنا هي **المشروع الكامل + سكربتات البناء الآلي**. نفّذ `build_windows.bat` على أي جهاز ويندوز وستحصل على `ZoomDownloader-Setup.exe` النهائي خلال دقائق.
