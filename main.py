#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zoom Events Downloader - GUI الرئيسية
PyQt6 + Playwright (Persistent Context) + yt-dlp
يعمل على ويندوز
"""
import sys
import os
import threading
import queue
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

# استيراد منطق التحميل
from downloader import ZoomDownloader, get_default_save_dir, get_user_data_dir, setup_bundled_tools

setup_bundled_tools()


class LogSignals(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zoom Events Downloader - تحميل تسجيلات زوم")
        self.setMinimumSize(650, 500)
        self.resize(700, 560)

        self.save_dir = get_default_save_dir()
        self.downloader = None
        self.signals = LogSignals()
        self.signals.log.connect(self.append_log)
        self.signals.progress.connect(self.progress.setValue)
        self.signals.finished.connect(self.on_finished)

        self._build_ui()
        self.append_log("✅ النظام جاهز. سجّل الدخول مرة واحدة وسيُحفظ الجلسة تلقائياً.")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # عنوان
        title = QLabel("🎥 Zoom Events Downloader")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("تحميل تسجيلات وفعاليات زوم (events.zoom.us) بجودة عالية")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(subtitle)

        # مجموعة الرابط
        url_group = QGroupBox("رابط التسجيل")
        url_layout = QHBoxLayout(url_group)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("الصق رابط زوم هنا... مثال: https://events.zoom.us/...")
        self.url_input.setMinimumHeight(36)
        # RTL للعربية
        self.url_input.setAlignment(Qt.AlignmentFlag.AlignLeft)
        url_layout.addWidget(self.url_input)
        layout.addWidget(url_group)

        # مجموعة مسار الحفظ
        path_group = QGroupBox("مسار الحفظ")
        path_layout = QHBoxLayout(path_group)
        self.path_input = QLineEdit(self.save_dir)
        self.path_input.setReadOnly(True)
        browse_btn = QPushButton("📁 تحديد مسار الحفظ")
        browse_btn.setMinimumHeight(34)
        browse_btn.clicked.connect(self.browse_save_dir)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        layout.addWidget(path_group)

        # أزرار التحكم
        btn_layout = QHBoxLayout()
        self.download_btn = QPushButton("⬇️ بدء التحميل")
        self.download_btn.setMinimumHeight(42)
        self.download_btn.setStyleSheet(
            "QPushButton { background-color: #0B5CFF; color: white; font-size: 15px; "
            "font-weight: bold; border-radius: 8px; padding: 8px; }"
            "QPushButton:hover { background-color: #0849CC; }"
            "QPushButton:disabled { background-color: #999; }"
        )
        self.download_btn.clicked.connect(self.start_download)

        self.login_btn = QPushButton("🔑 فتح المتصفح لتسجيل الدخول")
        self.login_btn.setMinimumHeight(42)
        self.login_btn.setStyleSheet(
            "QPushButton { background-color: #2D8A4E; color: white; font-size: 13px; "
            "border-radius: 8px; padding: 8px; }"
            "QPushButton:hover { background-color: #23703F; }"
        )
        self.login_btn.clicked.connect(self.open_login)

        btn_layout.addWidget(self.download_btn)
        btn_layout.addWidget(self.login_btn)
        layout.addLayout(btn_layout)

        # شريط التقدم
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setMinimumHeight(22)
        self.progress.setFormat("%p%")
        layout.addWidget(self.progress)

        # صندوق السجلات
        log_group = QGroupBox("حالة النظام (Logs)")
        log_layout = QVBoxLayout(log_group)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(180)
        self.log_box.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; color: #d4d4d4; "
            "font-family: Consolas, monospace; font-size: 11px; border-radius: 6px; }"
        )
        log_layout.addWidget(self.log_box)
        layout.addWidget(log_group)

    def append_log(self, msg: str):
        self.log_box.append(msg)
        # تمرير تلقائي للأسفل
        sb = self.log_box.verticalScrollBar()
        sb.setValue(sb.maximum())

    def browse_save_dir(self):
        d = QFileDialog.getExistingDirectory(self, "اختر مسار الحفظ", self.save_dir)
        if d:
            self.save_dir = d
            self.path_input.setText(d)
            self.append_log(f"📂 مسار الحفظ: {d}")

    def open_login(self):
        """فتح المتصفح لتسجيل الدخول مرة واحدة (Persistent Context)."""
        self.append_log("🌐 فتح المتصفح... سجّل الدخول في حساب زوم ثم أغلق النافذة.")
        self.login_btn.setEnabled(False)

        def _run():
            try:
                dl = ZoomDownloader(
                    save_dir=self.save_dir,
                    log_callback=lambda m: self.signals.log.emit(m),
                    progress_callback=lambda p: self.signals.progress.emit(p),
                )
                dl.open_login_window()
                self.signals.log.emit("✅ تم حفظ جلسة تسجيل الدخول. يمكنك الآن لصق أي رابط والتحميل.")
            except Exception as e:
                self.signals.log.emit(f"❌ خطأ في فتح المتصفح: {e}")
            finally:
                # إعادة تفعيل الزر في خيط الواجهة
                self.login_btn.setEnabled(True)

        threading.Thread(target=_run, daemon=True).start()

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال رابط زوم أولاً.")
            return
        if "zoom.us" not in url:
            r = QMessageBox.question(
                self, "تأكيد",
                "الرابط لا يبدو رابط زوم. هل تريد المتابعة على أي حال؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if r != QMessageBox.StandardButton.Yes:
                return

        self.download_btn.setEnabled(False)
        self.progress.setValue(0)
        self.append_log(f"🚀 بدء التحميل من: {url}")

        def _run():
            try:
                dl = ZoomDownloader(
                    save_dir=self.save_dir,
                    log_callback=lambda m: self.signals.log.emit(m),
                    progress_callback=lambda p: self.signals.progress.emit(p),
                )
                ok, msg = dl.download(url)
                self.signals.finished.emit(ok, msg)
            except Exception as e:
                self.signals.finished.emit(False, str(e))

        threading.Thread(target=_run, daemon=True).start()

    def on_finished(self, ok: bool, msg: str):
        self.download_btn.setEnabled(True)
        if ok:
            self.progress.setValue(100)
            self.append_log(f"🎉 اكتمل التحميل: {msg}")
            QMessageBox.information(self, "نجاح", f"اكتمل التحميل:\n{msg}")
        else:
            self.append_log(f"❌ فشل التحميل: {msg}")
            QMessageBox.critical(self, "فشل التحميل", msg)


def main():
    # دعم DPI العالي على ويندوز
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
