import sys
import time
import threading
import cv2
import numpy as np
from PIL import ImageGrab
import pyautogui
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

TEMPLATE_PATH   = "claim_rain.png"
CONFIDENCE      = 0.82
SCAN_INTERVAL   = 0.05
CLICK_COOLDOWN  = 2.0

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

class RainWatcher(threading.Thread):
    def __init__(self, status_callback):
        super().__init__(daemon=True)
        self.running = False
        self.status_callback = status_callback
        self.template = None
        self.last_click = 0
        self.clicks = 0

    def load_template(self):
        self.template = cv2.imread(TEMPLATE_PATH, cv2.IMREAD_COLOR)
        if self.template is None:
            self.status_callback("ERROR: claim_rain.png missing")
            return False
        return True

    def find_claim(self):
        if self.template is None:
            return None
        shot = np.array(ImageGrab.grab())
        shot = cv2.cvtColor(shot, cv2.COLOR_RGB2BGR)
        res = cv2.matchTemplate(shot, self.template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val >= CONFIDENCE:
            h, w = self.template.shape[:2]
            cx = max_loc[0] + w // 2
            cy = max_loc[1] + h // 2
            return cx, cy, max_val
        return None

    def run(self):
        if not self.load_template():
            return
        self.status_callback("WATCHING")
        while self.running:
            now = time.time()
            if now - self.last_click < CLICK_COOLDOWN:
                time.sleep(0.03)
                continue
            hit = self.find_claim()
            if hit:
                x, y, conf = hit
                pyautogui.click(x, y)
                self.last_click = now
                self.clicks += 1
                self.status_callback(f"CLAIMED #{self.clicks}  {conf:.2f}")
            time.sleep(SCAN_INTERVAL)
        self.status_callback("IDLE")

class RainUI(QWidget):
    status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CLAIM RAIN  ·  Cinder")
        self.setFixedSize(300, 180)
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

        self.title = QLabel("CLAIM RAIN AUTO")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 13, QFont.Bold))
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
                num = text.split("#")[1].split()[0]
                self.counter.setText(f"Clicks: {num}")
            except:
                pass
        elif "WATCHING" in text:
            self.status.setStyleSheet("color: #f1c40f; font-size: 12px;")
        elif "ERROR" in text:
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
