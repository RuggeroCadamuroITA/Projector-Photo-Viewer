import os
import sys
import json
import random
import socket
import threading
import qrcode
import cv2
from io import BytesIO
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout, QLabel, 
                             QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
                             QSpinBox, QFormLayout, QComboBox, QSizePolicy, 
                             QGraphicsOpacityEffect, QFrame, QMainWindow, QRadioButton, QButtonGroup)
from PyQt6.QtGui import QPixmap, QImage, QGuiApplication, QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint, QThread, pyqtSignal
from PIL import Image, ImageOps

# --- CONFIGURAZIONE ---
web_app = Flask(__name__)
DATA_FOLDER = ""
CONFIG = {}
SCREEN_AR = 1.77 
LAST_PATH_FILE = "last_folder_path.txt"

# --- HTML MOBILE (Stessa logica di prima, pulita) ---
HTML_MOBILE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Proiettore Remote</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css">
    <style>
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        html, body { height: 100%; margin: 0; padding: 0; background: #000; color: white; overflow: hidden; display: flex; flex-direction: column; }
        header { height: 60px; flex-shrink: 0; display: flex; justify-content: space-between; align-items: center; padding: 0 15px; background: #1a1a1a; border-bottom: 2px solid #333; }
        #editor-wrapper { flex-grow: 1; position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; }
        img { max-width: 100%; max-height: 100%; }
        .footer { height: 110px; flex-shrink: 0; display: flex; justify-content: space-between; align-items: center; padding: 10px; background: #1a1a1a; border-top: 2px solid #333; gap: 10px; }
        .btn { border: none; border-radius: 12px; font-size: 24px; height: 70px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.1s; }
        .btn:active { transform: translateY(3px); opacity: 0.8; }
        .btn-nav { background: #444; color: white; width: 55px; font-size: 18px; }
        .btn-trash { background: #d63031; color: white; flex: 1; }
        .btn-save { background: #0984e3; color: white; flex: 1.5; font-size: 18px; font-weight: bold; border: 2px solid #74b9ff; }
        .btn-check { background: #27ae60; color: white; flex: 1; }
        #info { font-family: monospace; font-size: 18px; font-weight: bold; }
        #save-indicator { position: absolute; top: 10px; left: 50%; transform: translateX(-50%); background: #27ae60; padding: 5px 15px; border-radius: 20px; font-size: 12px; display: none; z-index: 1000; }
    </style>
</head>
<body>
    <div id="save-indicator">Sincronizzato!</div>
    <header>
        <button class="btn btn-nav" onclick="navigate(-1)">◄</button>
        <span id="info">0 / 0</span>
        <button class="btn btn-nav" onclick="navigate(1)">►</button>
    </header>
    <div id="editor-wrapper"><img id="image" src=""></div>
    <div class="footer">
        <button class="btn btn-trash" onclick="trashAndNext()">🗑</button>
        <button class="btn btn-save" onclick="applyToProjector()">SALVA</button>
        <button class="btn btn-check" onclick="confirmAndNext()">✔</button>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
    <script>
        let images = [], config = {}, currentIndex = 0, cropper = null;
        const aspect_ratio = {{ aspect_ratio }};
        async function refreshData() {
            const res = await fetch('/api/data?t=' + Date.now());
            const data = await res.json();
            images = data.images; config = data.config;
            if (images.length > 0) updateView();
        }
        function updateView() {
            if (images.length === 0) return;
            const fname = images[currentIndex]; const img = document.getElementById('image');
            document.getElementById('info').innerText = (currentIndex + 1) + " / " + images.length;
            img.style.opacity = (config[fname] && config[fname].use === false) ? "0.4" : "1";
            if (cropper) cropper.destroy();
            img.src = "/photos/" + fname + "?t=" + Date.now();
            img.onload = () => {
                cropper = new Cropper(img, {
                    aspectRatio: aspect_ratio, viewMode: 1, autoCropArea: 1,
                    ready() {
                        if (config[fname] && config[fname].crop) {
                            const c = config[fname].crop; const id = cropper.getImageData();
                            cropper.setData({ x: c.x * id.naturalWidth, y: c.y * id.naturalHeight, width: c.w * id.naturalWidth, height: c.h * id.naturalHeight });
                        }
                    }
                });
            };
        }
        function saveCurrentState(useStatus) {
            const fname = images[currentIndex]; if (!cropper) return;
            const data = cropper.getData(); const id = cropper.getImageData();
            if (!config[fname]) config[fname] = {};
            config[fname].use = useStatus;
            config[fname].crop = { x: data.x / id.naturalWidth, y: data.y / id.naturalHeight, w: data.width / id.naturalWidth, h: data.height / id.naturalHeight };
        }
        function confirmAndNext() { saveCurrentState(true); navigate(1); }
        function trashAndNext() { saveCurrentState(false); navigate(1); }
        async function applyToProjector() {
            saveCurrentState(config[images[currentIndex]]?.use !== false);
            const res = await fetch('/api/save_all', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ config: config }) });
            if (res.ok) { const ind = document.getElementById('save-indicator'); ind.style.display = 'block'; setTimeout(() => ind.style.display = 'none', 2000); }
        }
        function navigate(step) {
            saveCurrentState(config[images[currentIndex]]?.use !== false);
            currentIndex = (currentIndex + step + images.length) % images.length; updateView();
        }
        refreshData();
    </script>
</body>
</html>
"""

# --- WEB SERVER ---
@web_app.route('/')
def index(): return render_template_string(HTML_MOBILE, aspect_ratio=SCREEN_AR)

@web_app.route('/api/data')
def get_data():
    files = sorted([f for f in os.listdir(DATA_FOLDER) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))])
    return jsonify({"images": files, "config": CONFIG})

@web_app.route('/api/save_all', methods=['POST'])
def save_all():
    global CONFIG
    data = request.json
    CONFIG.update(data['config'])
    with open(os.path.join(DATA_FOLDER, "proiettore_settings.json"), 'w') as f: json.dump(CONFIG, f, indent=4)
    return jsonify({"status": "ok"})

@web_app.route('/photos/<filename>')
def get_photo(filename): return send_from_directory(DATA_FOLDER, filename)

# --- THREAD WEBCAM ---
class WebcamThread(QThread):
    changePixmap = pyqtSignal(QImage)
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        while self.running:
            ret, frame = cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                p = convert_to_Qt_format.scaled(1920, 1080, Qt.AspectRatioMode.KeepAspectRatio)
                self.changePixmap.emit(p)
        cap.release()

    def stop(self):
        self.running = False
        self.wait()

# --- SLOT E PROIETTORI ---
class ImageSlot(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: black;")
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.opacity_effect = QGraphicsOpacityEffect(self); self.setGraphicsEffect(self.opacity_effect)
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity"); self.animation.setDuration(800)

    def set_image(self, path, crop=None):
        try:
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img).convert("RGB")
                w, h = img.size
                if crop: img = img.crop((int(crop['x']*w), int(crop['y']*h), int((crop['x']+crop['w'])*w), int((crop['y']+crop['h'])*h)))
                ar = self.width() / self.height() if self.height() > 0 else 1.77
                img_ar = img.width / img.height
                if img_ar > ar:
                    nw = int(img.height * ar); img = img.crop(((img.width-nw)//2, 0, (img.width-nw)//2 + nw, img.height))
                else:
                    nh = int(img.width / ar); img = img.crop((0, (img.height-nh)//2, img.width, (img.height-nh)//2 + nh))
                img.thumbnail((self.width(), self.height()), Image.Resampling.LANCZOS)
                pix = QPixmap.fromImage(QImage(img.tobytes(), img.width, img.height, img.width*3, QImage.Format.Format_RGB888))
                self.animation.stop(); self.animation.setStartValue(self.opacity_effect.opacity()); self.animation.setEndValue(0.0)
                def fade_in():
                    self.setPixmap(pix); self.animation.disconnect(); self.animation.setStartValue(0.0); self.animation.setEndValue(1.0); self.animation.start()
                self.animation.finished.connect(fade_in); self.animation.start()
        except: pass

class UniversalProjector(QWidget):
    def __init__(self, paths, screen_idx, mode="grid"):
        super().__init__()
        self.paths = paths; self.idx = 0; random.shuffle(self.paths)
        self.mode = mode
        self.setStyleSheet("background: black;"); self.setCursor(Qt.CursorShape.BlankCursor)
        
        self.layout = QGridLayout(self); self.layout.setContentsMargins(0,0,0,0); self.layout.setSpacing(0)
        
        if self.mode == "grid":
            self.slots = [ImageSlot() for _ in range(6)]
            for i, s in enumerate(self.slots): self.layout.addWidget(s, i//3, i%3)
        elif self.mode == "single":
            self.slots = [ImageSlot()]
            self.layout.addWidget(self.slots[0], 0, 0)
        elif self.mode == "webcam":
            self.video_label = QLabel()
            self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(self.video_label, 0, 0)
            self.webcam_thread = WebcamThread(camera_index=0) # Index 0 di solito è OBS o la webcam
            self.webcam_thread.changePixmap.connect(self.update_video)
            self.webcam_thread.start()

        # Posizionamento Schermo
        screens = QGuiApplication.screens()
        target_screen = screens[screen_idx] if screen_idx < len(screens) else screens[0]
        self.setGeometry(target_screen.geometry())
        self.showFullScreen()
        
        if self.mode != "webcam":
            QTimer.singleShot(500, self.load_initial)
            self.timer = QTimer(self); self.timer.timeout.connect(self.cycle); self.timer.start(10000)

    def update_video(self, image):
        self.video_label.setPixmap(QPixmap.fromImage(image))

    def load_initial(self):
        for i in range(len(self.slots)): self.update_slot(i)

    def cycle(self):
        global CONFIG
        try:
            with open(os.path.join(DATA_FOLDER, "proiettore_settings.json"), 'r') as f: CONFIG = json.load(f)
        except: pass
        
        num_slots = len(self.slots)
        delay = 1000 if num_slots > 1 else 0
        for i in range(num_slots): QTimer.singleShot(i * delay, lambda idx=i: self.update_slot(idx))

    def update_slot(self, i):
        for _ in range(len(self.paths)):
            p = self.paths[self.idx]; fname = os.path.basename(p); self.idx = (self.idx + 1) % len(self.paths)
            if CONFIG.get(fname, {}).get("use", True):
                self.slots[i].set_image(p, CONFIG.get(fname, {}).get("crop")); break

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            if self.mode == "webcam": self.webcam_thread.stop()
            self.close()

class MenuWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Studio Proiettore"); self.setFixedSize(450, 680)
        layout = QVBoxLayout()
        
        # Carica ultimo percorso
        last_path = ""
        if os.path.exists(LAST_PATH_FILE):
            try:
                with open(LAST_PATH_FILE, "r") as f: last_path = f.read().strip()
            except: pass

        self.btn_f = QPushButton("1. SELEZIONA CARTELLA"); self.btn_f.setFixedHeight(50); self.btn_f.clicked.connect(self.select_folder)
        layout.addWidget(self.btn_f)
        self.lbl_path = QLabel(last_path if last_path else "Nessuna cartella"); self.lbl_path.setWordWrap(True); self.lbl_path.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.lbl_path)
        
        self.qr_label = QLabel("QR Code"); self.qr_label.setFixedSize(300, 300); self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.qr_label.setStyleSheet("border: 1px solid #ccc; background: white;")
        layout.addWidget(self.qr_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Scelta Modalità
        self.mode_group = QButtonGroup(self)
        self.rb_grid = QRadioButton("Griglia (6 Foto)")
        self.rb_single = QRadioButton("Singola (OBS / Solo 1)")
        self.rb_webcam = QRadioButton("Webcam / OBS Virtual Cam")
        self.rb_grid.setChecked(True)
        self.mode_group.addButton(self.rb_grid)
        self.mode_group.addButton(self.rb_single)
        self.mode_group.addButton(self.rb_webcam)
        
        mode_box = QVBoxLayout(); mode_box.addWidget(QLabel("Modalità:")); mode_box.addWidget(self.rb_grid); mode_box.addWidget(self.rb_single); mode_box.addWidget(self.rb_webcam)
        layout.addLayout(mode_box)

        self.cb_scr = QComboBox()
        for i, s in enumerate(QGuiApplication.screens()): self.cb_scr.addItem(f"Schermo {i+1} ({s.size().width()}x{s.size().height()})")
        layout.addWidget(QLabel("Monitor di Destinazione:")); layout.addWidget(self.cb_scr)
        
        self.btn_start = QPushButton("2. AVVIA PROIEZIONE"); self.btn_start.setEnabled(False); self.btn_start.setFixedHeight(50); self.btn_start.setStyleSheet("background: #27ae60; color: white; font-weight: bold;"); self.btn_start.clicked.connect(self.start_p)
        layout.addWidget(self.btn_start)
        
        if last_path and os.path.exists(last_path): QTimer.singleShot(500, lambda: self.initialize_with_path(last_path))
        w = QWidget(); w.setLayout(layout); self.setCentralWidget(w)

    def select_folder(self):
        p = QFileDialog.getExistingDirectory(self, "Cartella")
        if p: self.initialize_with_path(p)

    def initialize_with_path(self, p):
        global DATA_FOLDER, CONFIG, SCREEN_AR
        DATA_FOLDER = p; self.lbl_path.setText(p)
        try:
            with open(LAST_PATH_FILE, "w") as f: f.write(p)
        except: pass
        cfg_path = os.path.join(p, "proiettore_settings.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, 'r') as f: CONFIG = json.load(f)
            except: CONFIG = {}
        s = QGuiApplication.screens()[self.cb_scr.currentIndex()].size()
        SCREEN_AR = (s.width()/3) / (s.height()/2) if self.rb_grid.isChecked() else (s.width()/s.height())
        self.gen_qr(); self.btn_start.setEnabled(True)
        if not hasattr(self, 'server_started'):
            threading.Thread(target=lambda: web_app.run(host='0.0.0.0', port=5000), daemon=True).start(); self.server_started = True

    def gen_qr(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]; s.close(); url = f"http://{ip}:5000"
            qr = qrcode.make(url); buf = BytesIO(); qr.save(buf, format="PNG")
            self.qr_label.setPixmap(QPixmap.fromImage(QImage.fromData(buf.getvalue())).scaled(300, 300))
        except: pass

    def start_p(self):
        p = sorted([os.path.join(DATA_FOLDER, f) for f in os.listdir(DATA_FOLDER) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))])
        mode = "grid" if self.rb_grid.isChecked() else "single" if self.rb_single.isChecked() else "webcam"
        self.proj = UniversalProjector(p, self.cb_scr.currentIndex(), mode)
        self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    m = MenuWindow(); m.show(); sys.exit(app.exec())
