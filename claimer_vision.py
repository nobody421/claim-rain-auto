import sys
import time
import threading
import base64
import io
import requests
from PIL import ImageGrab
import pyautogui
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

OLLAMA_URL      = "http://localhost:11434/api/chat"
MODEL           = "openbmb/minicpm-v4.6"
SCAN_INTERVAL   = 0.8
CLICK_COOLDOWN  = 2.5
PROMPT = (
    "Look at this screenshot of a casino website. "
    "Is there a big orange button that says exactly 'CLAIM RAIN'? "
    "Answer with only one word: YES or NO."
)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

class RainWatcher(threading.Thread):
    def __init__(self, status_callback):
        super().__init__(daemon=True)
        self.running = False
        self.status_callback = status_callback
        self.last_click = 0
        self.clicks = 0

    def ask_vision(self, img_b64: str) -> bool:
        payload = {
            "model": MODEL,
            "messages": [{
                "role": "user",
                "content": PROMPT,
                "images": [img_b64]
            }],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 8}
        }
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=30)
            r.raise_for_status()
            text = r.json()["message"]["content"].strip().upper()
            return "YES" in text
        except Exception as e:
            self.status_callback(f"OLLAMA ERR: {e}")
            return False

    def run(self):
        self.status_callback("WATCHING")
        while self.running:
            now = time.time()
            if now - self.last_click < CLICK_COOLDOWN:
                time.sleep(0.2)
                continue

            shot = ImageGrab.grab()
            buf = io.BytesIO()
            shot.save(buf, format="JPEG", quality=70)
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            if self.ask_vision(img_b64):
                # left sidebar CLAIM RAIN approximate position
                x, y = 140, 180
                pyautogui.click(x, y)
                self.last_click = now
                self.clicks += 1
                self.status_callback(f"CLAIMED #{self.clicks}")
            time.sleep(SCAN_INTERVAL)
        self.status_callback("IDLE")

class RainUI(QWidget):
    status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CLAIM RAIN  ·  Cinder + MiniCPM")
        self.setFixedSize(320, 180)
        self.setStyleSheet("""
            QWidget { background: #0d0d12; color: #e0e0e0; }
            QPushButton {
                background: #1a1a24; border: 1px solid #333;
                border-radius: 6px; padding: 10px; font-size: 14px;
            }
            QPushButton:hover { background: #252532; }
            QPushButton#on  { background: #1f3a1f; border-color: #2ecc71; }
            QPushButton#off { background: #3a1f1f; border-color: #e74c3c; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.title = QLabel("CLAIM RAIN (MiniCPM-V)")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(self.title)

        self.status = QLabel("IDLE")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.status)

        self.counter = QLabel("Clicks: 0")
        self.counter.setAlignment(Qt.AlignCenter)
        self.counter.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.counter)

        btn_row = QHBoxLayout()
        self.btn_on  = QPushButton("ON")
        self.btn_off = QPushButton("OFF")
        self.btn_on.setObjectName("on")
        self.btn_off.setObjectName("off")
        self.btn_on.clicked.connect(self.start)
        self.btn_off.clicked.connect(self.stop)
        btn_row.addWidget(self.btn_on)
        btn_row.addWidget(self.btn_off)
        layout.addLayout(btn_row)

        self.watcher = None
        self.status_signal.connect(self.update_status)

        self.pulse = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(80)

    def update_status(self, text):
        self.status.setText(text)
        if "CLAIMED" in text:
            self.status.setStyleSheet("color: #2ecc71; font-size: 12px;")
            try:
                num = text.split("#")[1]
                self.counter.setText(f"Clicks: {num}")
            except:
                pass
        elif "WATCHING" in text:
            self.status.setStyleSheet("color: #f1c40f; font-size: 12px;")
        elif "ERR" in text:
            self.status.setStyleSheet("color: #e74c3c; font-size: 12px;")
        else:
            self.status.setStyleSheet("color: #888; font-size: 12px;")

    def animate(self):
        if self.watcher and self.watcher.running:
            self.pulse = (self.pulse + 1) % 20
            dots = "." * (self.pulse // 5 + 1)
            if self.status.text().startswith("WATCHING"):
                self.status.setText(f"WATCHING{dots}")

    def start(self):
        if self.watcher and self.watcher.running:
            return
        self.watcher = RainWatcher(lambda t: self.status_signal.emit(t))
        self.watcher.running = True
        self.watcher.start()

    def stop(self):
        if self.watcher:
            self.watcher.running = False
            self.watcher = None
        self.update_status("IDLE")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = RainUI()
    ui.show()
    sys.exit(app.exec_())
