import cv2
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QGridLayout, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

class CameraFeed(QWidget):
    clicked_signal = pyqtSignal(object)
    def __init__(self, camera_id=None, name="Camera"):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setCursor(Qt.PointingHandCursor if hasattr(Qt, 'PointingHandCursor') else 13)
        self.title = QLabel(f"<b>🔴 {name}</b>")
        self.title.setStyleSheet("background: white; padding: 5px; border-radius: 4px; border: 1px solid #E0E0E0;")
        self.layout.addWidget(self.title)
        self.feed_label = QLabel("Initializing Camera...")
        self.feed_label.setStyleSheet("background: #222; color: white; border-radius: 4px;")
        self.feed_label.setAlignment(Qt.AlignCenter)
        self.feed_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.feed_label.setMinimumSize(160, 120)
        self.layout.addWidget(self.feed_label)
        
        if camera_id is not None:
            self.thread = VideoThread(camera_id)
            self.thread.frame_signal.connect(self.update_image)
            self.thread.error_signal.connect(self.show_error)
            self.thread.start()
        else:
            self.feed_label.setText("📷 Camera Placeholder\n(Hardware Skipped)")
            self.feed_label.setStyleSheet("background: #EAEAEA; color: #757575; border: 1px solid #CCC; border-radius: 4px;")

    def update_image(self, q_img): 
        self.feed_label.setPixmap(QPixmap.fromImage(q_img).scaled(self.feed_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
    def show_error(self):
        self.feed_label.setText("📷 Camera Offline\nor Not Detected")
        self.feed_label.setStyleSheet("background: #FFEBEE; color: #C62828; border: 1px solid #E57373; border-radius: 4px;")

    def mousePressEvent(self, event):
        self.clicked_signal.emit(self)
        super().mousePressEvent(event)

class VideoThread(QThread):
    frame_signal = pyqtSignal(object) 
    error_signal = pyqtSignal()
    def __init__(self, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self._run = True
    def run(self):
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            self.error_signal.emit()
            return
        while self._run:
            ret, frame = cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                q_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
                self.frame_signal.emit(q_img)
            else:
                self.error_signal.emit()
                break
        cap.release()
    def stop(self):
        self._run = False
        self.wait()

def build_page(app, layout):
    layout.setContentsMargins(25, 25, 25, 25)
    layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 15px;'>📹 Live Playrooms</h1>"))
    
    app.cam_grid = QGridLayout()
    app.cam_grid.setSpacing(15)
    layout.addLayout(app.cam_grid)
    
    rooms = ["Friendly Room", "Calm Room", "Fearful Room", "Aggressive Room 1", "Aggressive Room 2", "Aggressive Room 3", "Solo Room 1", "Solo Room 2", "Solo Room 3"]
    app.cam_widgets = []
    app.expanded_cam = None
    
    camera_mapping = {
        "Friendly Room": 0,  
    }
    
    row, col = 0, 0
    for i, room in enumerate(rooms):
        # Look up the room name in the dictionary. If not found, use None.
        safe_cam_id = camera_mapping.get(room, None)
        
        cam_widget = CameraFeed(camera_id=safe_cam_id, name=room)
        cam_widget.clicked_signal.connect(lambda cam: toggle_camera_zoom(app, cam))
        
        app.cam_grid.addWidget(cam_widget, row, col)
        app.cam_widgets.append(cam_widget)
        
        col += 1
        if col > 2:
            col = 0
            row += 1
            
    layout.addStretch()

def toggle_camera_zoom(app, clicked_cam):
    if app.expanded_cam is None:
        app.expanded_cam = clicked_cam
        for cam in app.cam_widgets:
            if cam != clicked_cam: cam.hide()
    else:
        app.expanded_cam = None
        for cam in app.cam_widgets: cam.show()