import sys, os, sqlite3, random
import cv2
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
                             QPushButton, QMessageBox, QLabel, QFrame, QStackedWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QCompleter, QScrollArea,
                             QDateEdit, QDialog, QTimeEdit, QGridLayout, QSizePolicy, QRadioButton)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate, QTime
from PyQt5.QtGui import QImage, QPixmap, QIcon

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'ResPAWNsible(Real).db')

# --- Shared Styles ---
TABLE_HEADER_STYLE = """
    QHeaderView::section {
        background-color: #4A352B;
        color: white;
        font-weight: bold;
        padding: 5px;
        border: none;
    }
"""

# --- Camera Threading & Widget Classes ---
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
            self.show_placeholder()

    def update_image(self, q_img): 
        pixmap = QPixmap.fromImage(q_img).scaled(self.feed_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.feed_label.setPixmap(pixmap)
        
    def show_error(self):
        self.feed_label.setText("📷 Camera Offline\nor Not Detected")
        self.feed_label.setStyleSheet("background: #FFEBEE; color: #C62828; border: 1px solid #E57373; border-radius: 4px;")

    def show_placeholder(self):
        self.feed_label.setText("📷 Camera Placeholder\n(Hardware Skipped)")
        self.feed_label.setStyleSheet("background: #EAEAEA; color: #757575; border: 1px solid #CCC; border-radius: 4px;")

    def mousePressEvent(self, event):
        self.clicked_signal.emit(self)
        super().mousePressEvent(event)

class VideoThread(QThread):
    frame_signal = pyqtSignal(QImage)
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

# --- Main Application ---
class ResPAWnsibleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ResPAWnsible - Safety-First Boarding")
        self.resize(1200, 700)
        self.setStyleSheet("background-color: #FDFBF7; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px;")
        self.init_db()
        self.init_ui()

    def init_db(self):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys = ON;")
        try: 
            self.c.execute("SELECT TagID, Behavior FROM BEHAVIOR_TAG;")
        except sqlite3.OperationalError:
            self.tags = []
            return
            
        self.tags = self.c.fetchall()
        if not self.tags:
            defaults = [("Calm / Friendly",), ("Nervous / Fearful",), ("Hyperactive / Playful",), 
                        ("Aggressive / Territorial",), ("Requires Solo Room",)]
            self.c.executemany("INSERT INTO BEHAVIOR_TAG (Behavior) VALUES (?);", defaults)
            self.conn.commit()
            self.c.execute("SELECT TagID, Behavior FROM BEHAVIOR_TAG;")
            self.tags = self.c.fetchall()

    def generate_unique_pet_id(self):
        while True:
            new_id = random.randint(100000, 999999)
            self.c.execute("SELECT 1 FROM PET WHERE PetID = ?", (new_id,))
            if not self.c.fetchone():
                return new_id

    def get_dashboard_count(self):
        try:
            self.c.execute("SELECT COUNT(PetID) FROM PET;")
            return str(self.c.fetchone()[0])
        except sqlite3.OperationalError: return "0"

    def get_active_visits(self):
        try:
            self.c.execute("SELECT COUNT(*) FROM VISIT WHERE EndTime IS NULL OR EndTime = '';")
            return self.c.fetchone()[0]
        except sqlite3.OperationalError: return 0

    def get_room_utilization(self):
        try:
            self.c.execute("SELECT SUM(MaxCapacity) FROM PLAYROOM;")
            cap = self.c.fetchone()[0]
            if not cap: return "0%"
            return f"{int((self.get_active_visits() / cap) * 100)}%"
        except sqlite3.OperationalError: return "0%"

    def generate_safety_alerts(self):
        alerts = []
        try:
            self.c.execute("SELECT RoomID, RoomName, MaxCapacity FROM PLAYROOM;")
            for r_id, r_name, r_cap in self.c.fetchall():
                self.c.execute("""SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType FROM VISIT V JOIN PET P ON V.PetID = P.PetID
                                  LEFT JOIN PET_TAG PT ON P.PetID = PT.PetID LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID = BT.TagID
                                  LEFT JOIN BREED B ON P.PetID = B.PetID WHERE V.RoomID = ? AND (V.EndTime IS NULL OR V.EndTime = '');""", (r_id,))
                occupants = self.c.fetchall()
                count = len(occupants)
                
                if r_cap and count >= r_cap: 
                    alerts.append(("CRITICAL", "Capacity Overflow", f"{r_name} is FULL ({count}/{r_cap}). No further admittance allowed."))
                elif r_cap > 1 and count >= r_cap - 1: 
                    alerts.append(("WARNING", "Near Capacity", f"{r_name} is almost full ({count}/{r_cap}). Consider redirecting check-ins."))
                
                if count < 2: continue
                solo = [p for p in occupants if "Requires Solo Room" in str(p[2])]
                if solo: alerts.append(("CRITICAL", "Isolation Breach", f"{solo[0][0]} requires a solo room, but {count-1} other pets are inside {r_name}."))
                
                species = set([self.parse_species(p[3]) for p in occupants])
                if len(species) > 1: alerts.append(("CRITICAL", "Species Mismatch", f"{r_name} contains mixed species: {', '.join(species)}."))
                
                dogs = [p for p in occupants if self.parse_species(p[3]) == "Dog"]
                aggr = [p for p in dogs if "Aggressive" in str(p[2])]
                calm = [p for p in dogs if "Calm" in str(p[2])]
                
                if aggr and calm: alerts.append(("CRITICAL", "Behavior Conflict", f"{aggr[0][0]} (Aggressive) is locked with a Calm dog in {r_name}."))
                if aggr:
                    sizes = set(["Small" if (p[1] or 0) < 30 else "Large" for p in dogs])
                    if len(sizes) > 1: alerts.append(("CRITICAL", "Size & Aggression Risk", f"Mixed Size (Small/Large) grouping in {r_name} alongside an aggressive marker."))
        except Exception: pass
        return alerts

    def create_tag_pill(self, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)    
        text_lower = text.lower()
        if "aggressive" in text_lower or "solo" in text_lower:
            bg, fg, border = "#FFEBEE", "#C62828", "#FFCDD2"
        elif "calm" in text_lower:
            bg, fg, border = "#F3E5F5", "#6A1B9A", "#E1BEE7"
        elif "hyperactive" in text_lower or "playful" in text_lower:
            bg, fg, border = "#E3F2FD", "#1565C0", "#BBDEFB"
        elif "nervous" in text_lower or "fearful" in text_lower:
            bg, fg, border = "#FFF3E0", "#E65100", "#FFE0B2"
        else:
            bg, fg, border = "#F5F5F5", "#424242", "#E0E0E0"

        lbl.setStyleSheet(f"background-color: {bg}; color: {fg}; border: 1px solid {border}; border-radius: 12px; padding: 4px 14px; font-weight: bold; font-size: 11px;")
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(5, 4, 5, 4)
        lay.addWidget(lbl)
        lay.addStretch() 
        return container

    def filter_table(self, text, table):
        """Universal function to search across any provided table."""
        search_text = text.lower()
        for row in range(table.rowCount()):
            match = False
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
                else:
                    # Check custom widgets (like the Behavior Profile pill containers)
                    widget = table.cellWidget(row, col)
                    if widget:
                        label = widget.findChild(QLabel)
                        if label and search_text in label.text().lower():
                            match = True
                            break
            table.setRowHidden(row, not match)

    def make_searchable(self, combo_box, allow_new=False):
        combo_box.setEditable(True)
        if not allow_new:
            combo_box.setInsertPolicy(QComboBox.NoInsert)
        completer = combo_box.completer()
        if completer:
            completer.setCompletionMode(QCompleter.PopupCompletion)
            completer.setFilterMode(Qt.MatchContains)
            completer.setCaseSensitivity(Qt.CaseInsensitive)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #3A271E; color: white;")
        side_layout = QVBoxLayout(sidebar)
        
        logo_lbl = QLabel("<h2>ResPAWnsible</h2><p style='color: #FFC107;'>Safety-First Boarding</p>")
        logo_lbl.setStyleSheet("margin-bottom: 15px;")
        side_layout.addWidget(logo_lbl)

        self.nav_btns = []
        nav_items = [("📊", "Dashboard"), ("📹", "Live Playrooms"), ("🐾", "Register Pet"), 
                     ("📋", "Pet Directory"), ("📅", "Bookings"), ("🚪", "Visitations"), ("🛡️", "Safety Reports")]
        
        self.stack = QStackedWidget()
        
        for i, (icon, nav) in enumerate(nav_items):
            btn = QPushButton(f"  {icon}   {nav}")
            btn.setCursor(Qt.PointingHandCursor if hasattr(Qt, 'PointingHandCursor') else 13)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            side_layout.addWidget(btn)
            self.nav_btns.append(btn)
            
            page = QWidget()
            p_layout = QVBoxLayout(page)
            if i == 0: self.build_dashboard_page(p_layout)
            elif i == 1: self.build_live_playrooms_page(p_layout)
            elif i == 2: self.build_registration_page(p_layout)
            elif i == 3: self.build_pets_page(p_layout)
            elif i == 4: self.build_bookings_page(p_layout)
            elif i == 5: self.build_visitations_page(p_layout)
            elif i == 6: self.build_safety_reports_page(p_layout)
            self.stack.addWidget(page)
            
        side_layout.addStretch()
        self.active_lbl = QLabel(f"Registered Pets<br><b style='font-size: 18px;'>{self.get_dashboard_count()}</b>")
        self.active_lbl.setStyleSheet("background-color: #2D1D16; padding: 15px; border-radius: 6px; border: 1px solid #4A352B;")
        side_layout.addWidget(self.active_lbl)
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack)
        
        self.switch_page(0)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_btns):
            if i == index:
                btn.setStyleSheet("text-align: left; background-color: #FFC107; color: #3A271E; padding: 12px; font-weight: bold; border-radius: 4px; border: none;")
            else:
                btn.setStyleSheet("text-align: left; background-color: transparent; color: white; padding: 12px; font-weight: bold; border-radius: 4px; border: none;")
        
        if index == 0: self.refresh_dashboard()
        if index == 2: 
            self.refresh_breed_dropdown()
            self.refresh_existing_owners()
            
        if index == 3: self.refresh_pets_table()
        if index == 4: self.refresh_bookings_module()
        if index == 5: self.refresh_visitations_module()
        if index == 6: self.refresh_safety_reports()

    # --- Safety Matrix Helper ---
    def run_safety_matrix(self, pet_id, room_id):
        self.c.execute("SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType FROM PET P LEFT JOIN BREED B ON P.PetID=B.PetID LEFT JOIN PET_TAG PT ON P.PetID=PT.PetID LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID=BT.TagID WHERE P.PetID=?;", (pet_id,))
        p_prof = self.c.fetchone()
        if not p_prof: return False, "Invalid Pet ID."
        
        self.c.execute("SELECT COUNT(*) FROM VISIT WHERE PetID=? AND (EndTime IS NULL OR EndTime = '');", (pet_id,))
        if self.c.fetchone()[0] > 0: return False, "Pet is already actively checked in."

        self.c.execute("SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType FROM VISIT V JOIN PET P ON V.PetID = P.PetID LEFT JOIN BREED B ON P.PetID = B.PetID LEFT JOIN PET_TAG PT ON P.PetID = PT.PetID LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID = BT.TagID WHERE V.RoomID=? AND (V.EndTime IS NULL OR V.EndTime = '');", (room_id,))
        occupants = self.c.fetchall()
        
        sp, sz = self.parse_species(p_prof[3]), "Small" if (p_prof[1] or 0) < 30 else "Large"
        for o in occupants:
            o_sp, o_sz = self.parse_species(o[3]), "Small" if (o[1] or 0) < 30 else "Large"
            if "Requires Solo Room" in [str(p_prof[2]), str(o[2])] or sp != o_sp:
                return False, "Safety Rule Violation (Isolation/Species mismatch)."
            if sp == "Dog" and (("Aggressive" in str(p_prof[2]) and "Calm" in str(o[2])) or ("Calm" in str(p_prof[2]) and "Aggressive" in str(o[2])) or (("Aggressive" in str(p_prof[2]) or "Aggressive" in str(o[2])) and sz != o_sz)):
                return False, "Safety Rule Violation (Behavior/Size conflict)."
        return True, p_prof[0]

    # --- Dashboard Page ---
    def build_dashboard_page(self, layout):
        layout.setContentsMargins(25, 25, 25, 25)
        layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 10px;'>📊 Operations Dashboard</h1>"))
        
        stats_layout = QHBoxLayout()
        self.dash_stats = {}
        for title in ["Total Registered Pets", "Active Visitations", "Safety Alerts", "Room Utilization"]:
            card = QFrame()
            card.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 15px;")
            c_layout = QVBoxLayout(card)
            c_layout.addWidget(QLabel(f"<span style='color: #757575; font-size: 13px; font-weight: bold;'>{title.upper()}</span>"))
            val_lbl = QLabel()
            self.dash_stats[title] = val_lbl 
            c_layout.addWidget(val_lbl)
            stats_layout.addWidget(card)
        layout.addLayout(stats_layout)
        
        bottom_layout = QHBoxLayout()
        
        self.dash_alerts_layout = QVBoxLayout()
        alerts_frame = QFrame()
        alerts_frame.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 20px;")
        alerts_frame.setLayout(self.dash_alerts_layout)
        bottom_layout.addWidget(alerts_frame, 1)

        self.dash_bookings_layout = QVBoxLayout()
        bookings_frame = QFrame()
        bookings_frame.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 20px;")
        bookings_frame.setLayout(self.dash_bookings_layout)
        bottom_layout.addWidget(bookings_frame, 1)
        
        self.dash_visitations_layout = QVBoxLayout()
        visitations_frame = QFrame()
        visitations_frame.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 20px;")
        visitations_frame.setLayout(self.dash_visitations_layout)
        bottom_layout.addWidget(visitations_frame, 1)
        
        layout.addLayout(bottom_layout)
        layout.addStretch()

    def refresh_dashboard(self):
        self.dash_stats["Total Registered Pets"].setText(f"<span style='font-size: 32px; font-weight: bold; color: #3A271E;'>{self.get_dashboard_count()}</span>")
        self.dash_stats["Active Visitations"].setText(f"<span style='font-size: 32px; font-weight: bold; color: #3A271E;'>{self.get_active_visits()}</span>")
        self.dash_stats["Room Utilization"].setText(f"<span style='font-size: 32px; font-weight: bold; color: #3A271E;'>{self.get_room_utilization()}</span>")
        
        alerts = self.generate_safety_alerts()
        self.dash_stats["Safety Alerts"].setText(f"<span style='font-size: 32px; font-weight: bold; color: {'#D32F2F' if alerts else '#3A271E'};'>{len(alerts)}</span>")
        
        while self.dash_alerts_layout.count():
            item = self.dash_alerts_layout.takeAt(0)
            if item.widget(): item.widget().setParent(None)
            
        self.dash_alerts_layout.addWidget(QLabel("<h3 style='color: #3A271E; margin-bottom: 10px;'>🛡️ Top Safety Priorities</h3>"))
        if not alerts: 
            self.dash_alerts_layout.addWidget(QLabel("<p style='color: #388E3C; font-weight: bold;'>✅ All playrooms are operating safely.</p>"))
        else:
            for severity, title, msg in alerts[:3]:
                color, border, t_color = ("#FFEBEE", "#EF9A9A", "#C62828") if severity == "CRITICAL" else ("#FFF8E1", "#FFE082", "#F57F17")
                lbl = QLabel(f"<b style='color: {t_color};'>⚠️ {title}</b><br><span style='color: #555;'>{msg}</span>")
                lbl.setStyleSheet(f"background: {color}; border: 1px solid {border}; padding: 10px; border-radius: 6px;")
                self.dash_alerts_layout.addWidget(lbl)
        self.dash_alerts_layout.addStretch()

        while self.dash_bookings_layout.count():
            item = self.dash_bookings_layout.takeAt(0)
            if item.widget(): item.widget().setParent(None)
            
        self.dash_bookings_layout.addWidget(QLabel("<h3 style='color: #3A271E; margin-bottom: 10px;'>📅 Upcoming Reservations</h3>"))
        try:
            self.c.execute("""SELECT P.Name, R.RoomName, B.StartDate, B.StartTime FROM BOOKING B 
                              JOIN PET P ON B.PetID = P.PetID JOIN PLAYROOM R ON B.RoomID = R.RoomID 
                              WHERE B.Status = 'Confirmed' AND B.StartDate >= DATE('now')
                              ORDER BY B.StartDate ASC, B.StartTime ASC LIMIT 4;""")
            upcoming = self.c.fetchall()
            if not upcoming:
                self.dash_bookings_layout.addWidget(QLabel("<p style='color: #757575;'>No upcoming reservations scheduled.</p>"))
            else:
                for pet_name, room_name, s_date, s_time in upcoming:
                    lbl = QLabel(f"<b>{pet_name}</b> ➔ {room_name}<br><span style='color: #757575;'>{s_date} | {s_time}</span>")
                    lbl.setStyleSheet("background: #F5F5F5; border-radius: 6px; padding: 10px; border: 1px solid #EAEAEA;")
                    self.dash_bookings_layout.addWidget(lbl)
        except Exception: pass
        self.dash_bookings_layout.addStretch()

        while self.dash_visitations_layout.count():
            item = self.dash_visitations_layout.takeAt(0)
            if item.widget(): item.widget().setParent(None)
            
        self.dash_visitations_layout.addWidget(QLabel("<h3 style='color: #3A271E; margin-bottom: 10px;'>🚪 Live Room Occupants</h3>"))
        try:
            self.c.execute("""SELECT P.Name, R.RoomName, V.StartTime FROM VISIT V
                              JOIN PET P ON V.PetID = P.PetID JOIN PLAYROOM R ON V.RoomID = R.RoomID
                              WHERE V.EndTime IS NULL OR V.EndTime = '' ORDER BY V.StartTime DESC LIMIT 4;""")
            active_occupants = self.c.fetchall()
            if not active_occupants:
                self.dash_visitations_layout.addWidget(QLabel("<p style='color: #757575;'>No active occupants inside facility.</p>"))
            else:
                for pet_name, room_name, start_time in active_occupants:
                    card_widget = QWidget()
                    card_lay = QHBoxLayout(card_widget)
                    card_lay.setContentsMargins(0, 0, 0, 0)
                    
                    info_text = QLabel(f"<b>{pet_name}</b> inside {room_name}<br><span style='color: #757575;'>🕒 Checked-In: {start_time}</span>")
                    view_btn = QPushButton("📺 Live View")
                    view_btn.setCursor(Qt.PointingHandCursor if hasattr(Qt, 'PointingHandCursor') else 13)
                    view_btn.setStyleSheet("background-color: #3A271E; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
                    
                    view_btn.clicked.connect(lambda checked, rm=room_name: self.zoom_into_room(rm))
                    
                    card_lay.addWidget(info_text, 1)
                    card_lay.addWidget(view_btn)
                    
                    frame_container = QFrame()
                    frame_container.setStyleSheet("background: #F5F5F5; border-radius: 6px; padding: 10px; border: 1px solid #EAEAEA;")
                    fc_lay = QVBoxLayout(frame_container)
                    fc_lay.setContentsMargins(5, 5, 5, 5)
                    fc_lay.addWidget(card_widget)
                    self.dash_visitations_layout.addWidget(frame_container)
        except Exception: pass
        self.dash_visitations_layout.addStretch()

    def zoom_into_room(self, room_name):
        self.switch_page(1) 
        self.expanded_cam = None
        for cam in self.cam_widgets:
            cam.show()
            
        for cam in self.cam_widgets:
            if room_name in cam.title.text():
                self.expanded_cam = cam
                for alternative_cam in self.cam_widgets:
                    if alternative_cam != cam:
                        alternative_cam.hide()
                break

    # --- Live Playrooms Page (TILED GRID) ---
    def build_live_playrooms_page(self, layout):
        layout.setContentsMargins(25, 25, 25, 25)
        layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 15px;'>📹 Live Playrooms</h1>"))
        
        self.cam_grid = QGridLayout()
        self.cam_grid.setSpacing(15)
        layout.addLayout(self.cam_grid)
        
        rooms = [
            "Friendly Room", "Calm Room", "Fearful Room", 
            "Aggressive Room 1", "Aggressive Room 2", "Aggressive Room 3", 
            "Solo Room 1", "Solo Room 2", "Solo Room 3"
        ]
        
        self.cam_widgets = []
        self.expanded_cam = None
        
        row, col = 0, 0
        for i, room in enumerate(rooms):
            safe_cam_id = 0 if i == 0 else None
            cam_widget = CameraFeed(camera_id=safe_cam_id, name=room)
            cam_widget.clicked_signal.connect(self.toggle_camera_zoom)
            
            self.cam_grid.addWidget(cam_widget, row, col)
            self.cam_widgets.append(cam_widget)
            
            col += 1
            if col > 2:
                col = 0
                row += 1
        layout.addStretch()

    def toggle_camera_zoom(self, clicked_cam):
        if self.expanded_cam is None:
            self.expanded_cam = clicked_cam
            for cam in self.cam_widgets:
                if cam != clicked_cam: cam.hide()
        else:
            self.expanded_cam = None
            for cam in self.cam_widgets: cam.show()

    # --- Safety Reports Page ---
    def build_safety_reports_page(self, layout):
        layout.setContentsMargins(25, 25, 25, 25)
        layout.addWidget(QLabel("<h1 style='color: #3A271E;'>🛡️ Facility Safety & Audit Reports</h1>"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.safety_layout = QVBoxLayout(container)
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def refresh_safety_reports(self):
        while self.safety_layout.count():
            item = self.safety_layout.takeAt(0)
            if item.widget(): item.widget().setParent(None)
            
        alerts = self.generate_safety_alerts()
        if not alerts:
            box = QLabel("<h2>✅ Zero Active Threats</h2><p>System audit cleared. All capacity and behavioral matrices are optimal.</p>")
            box.setStyleSheet("background: #E8F5E9; border: 2px solid #388E3C; color: #2E7D32; padding: 20px; border-radius: 8px;")
            self.safety_layout.addWidget(box)
        else:
            for severity, title, msg in alerts:
                box = QFrame()
                color, border, t_color = ("#FFEBEE", "#EF9A9A", "#C62828") if severity == "CRITICAL" else ("#FFF8E1", "#FFE082", "#F57F17")
                box.setStyleSheet(f"background-color: {color}; border: 1px solid {border}; border-left: 6px solid {border}; border-radius: 6px; padding: 15px;")
                b_lay = QVBoxLayout(box)
                b_lay.addWidget(QLabel(f"<h3 style='color: {t_color}; margin: 0;'>[{severity}] {title}</h3>"))
                b_lay.addWidget(QLabel(f"<span style='font-size: 13px; color: #555;'>{msg}</span>"))
                self.safety_layout.addWidget(box)
        self.safety_layout.addStretch()

    # --- Registration Page (COMPACT REDESIGN) ---
    def build_registration_page(self, layout):
        layout.setContentsMargins(25, 25, 25, 25)
        layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 5px;'>🐾 Register New Pet</h1>"))
        layout.addWidget(QLabel("<p style='color: #757575; margin-top: 0px;'>Add a new pet to the facility directory.</p>"))
        
        center_wrapper = QHBoxLayout()
        
        container = QFrame()
        container.setFixedWidth(650)
        container.setStyleSheet("""
            QFrame#MainCard {
                background-color: white; 
                border: 1px solid #EAEAEA; 
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background: transparent;
                font-weight: bold;
                color: #4A352B;
            }
        """)
        container.setObjectName("MainCard")
        
        main_form_lay = QVBoxLayout(container)
        main_form_lay.setContentsMargins(30, 30, 30, 30)
        main_form_lay.setSpacing(20)
        
        style = "padding: 10px; border: 1px solid #CCC; border-radius: 4px; background: #FDFDFD; color: #333;"
        
        self.inputs = {"First Name": QLineEdit(), "Last Name": QLineEdit(), "Phone": QLineEdit(), 
                       "Pet Name": QLineEdit(), "Weight (kg)": QLineEdit()}
        
        for widget in self.inputs.values(): 
            widget.setStyleSheet(style)
        self.inputs["Phone"].setInputMask("0999-999-9999")
        
        self.inputs["First Name"].textEdited.connect(lambda: self.auto_capitalize_fields(self.inputs["First Name"]))
        self.inputs["Last Name"].textEdited.connect(lambda: self.auto_capitalize_fields(self.inputs["Last Name"]))
        self.inputs["First Name"].editingFinished.connect(self.check_existing_owner)
        self.inputs["Last Name"].editingFinished.connect(self.check_existing_owner)
        
        owner_header = QLabel("<h3>👤 Owner Information</h3>")
        owner_header.setStyleSheet("color: #3A271E; border-bottom: 2px solid #FFC107; padding-bottom: 5px;")
        main_form_lay.addWidget(owner_header)
        
        mode_lay = QHBoxLayout()
        self.radio_new_owner = QRadioButton("Register New Owner")
        self.radio_existing_owner = QRadioButton("Select Existing Owner")
        self.radio_new_owner.setChecked(True)
        radio_style = "QRadioButton { font-weight: normal; color: #333; }"
        self.radio_new_owner.setStyleSheet(radio_style)
        self.radio_existing_owner.setStyleSheet(radio_style)
        
        mode_lay.addWidget(self.radio_new_owner)
        mode_lay.addWidget(self.radio_existing_owner)
        mode_lay.addStretch()
        main_form_lay.addLayout(mode_lay)
        
        self.new_owner_widget = QWidget()
        no_lay = QFormLayout(self.new_owner_widget)
        no_lay.setContentsMargins(0, 10, 0, 0)
        no_lay.setSpacing(15)
        no_lay.addRow("First Name:", self.inputs["First Name"])
        no_lay.addRow("Last Name:", self.inputs["Last Name"])
        no_lay.addRow("Mobile Number:", self.inputs["Phone"])
        main_form_lay.addWidget(self.new_owner_widget)
        
        self.existing_owner_widget = QWidget()
        eo_lay = QFormLayout(self.existing_owner_widget)
        eo_lay.setContentsMargins(0, 10, 0, 0)
        self.existing_owner_cb = QComboBox()
        self.existing_owner_cb.setStyleSheet(style)
        self.make_searchable(self.existing_owner_cb, allow_new=False)
        eo_lay.addRow("Select Owner:", self.existing_owner_cb)
        self.existing_owner_widget.hide()
        main_form_lay.addWidget(self.existing_owner_widget)
        
        self.radio_new_owner.toggled.connect(self.toggle_owner_mode)
        self.radio_existing_owner.toggled.connect(self.toggle_owner_mode)

        pet_header = QLabel("<br><h3>🐶 Pet Details</h3>")
        pet_header.setStyleSheet("color: #3A271E; border-bottom: 2px solid #FFC107; padding-bottom: 5px;")
        main_form_lay.addWidget(pet_header)
        
        pet_widget = QWidget()
        po_lay = QFormLayout(pet_widget)
        po_lay.setContentsMargins(0, 10, 0, 0)
        po_lay.setSpacing(15)
        po_lay.addRow("Pet Name:", self.inputs["Pet Name"])
        po_lay.addRow("Weight (kg):", self.inputs["Weight (kg)"])
        
        self.species_cb = QComboBox()
        self.species_cb.addItems(["Dog", "Cat", "Bird", "Rabbit", "Reptile", "Other"])
        self.species_cb.setStyleSheet(style)
        self.make_searchable(self.species_cb, allow_new=False)
        po_lay.addRow("Species:", self.species_cb)
        
        self.breed_cb = QComboBox()
        self.breed_cb.setStyleSheet(style)
        self.make_searchable(self.breed_cb, allow_new=True) 
        po_lay.addRow("Breed:", self.breed_cb)

        self.behavior_cb = QComboBox()
        self.behavior_cb.setStyleSheet(style)
        for t_id, t_name in self.tags: self.behavior_cb.addItem(t_name, t_id)
        self.make_searchable(self.behavior_cb, allow_new=False)
        po_lay.addRow("Behavior Profile:", self.behavior_cb)
        main_form_lay.addWidget(pet_widget)
        
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        btn = QPushButton("Complete Registration")
        btn.setFixedWidth(220)
        btn.setCursor(Qt.PointingHandCursor if hasattr(Qt, 'PointingHandCursor') else 13)
        btn.setStyleSheet("background-color: #FFC107; color: #3A271E; font-size: 14px; font-weight: bold; padding: 12px; border-radius: 6px; margin-top: 15px;")
        btn.clicked.connect(self.submit_data)
        btn_lay.addWidget(btn)
        
        main_form_lay.addLayout(btn_lay)
        center_wrapper.addWidget(container)
        center_wrapper.addStretch()
        layout.addLayout(center_wrapper)
        layout.addStretch()

    def toggle_owner_mode(self):
        if self.radio_new_owner.isChecked():
            self.new_owner_widget.show()
            self.existing_owner_widget.hide()
        else:
            self.new_owner_widget.hide()
            self.existing_owner_widget.show()
            self.refresh_existing_owners()

    def refresh_existing_owners(self):
        try:
            self.existing_owner_cb.clear()
            self.c.execute("""SELECT O.OwnerID, O.FirstName, O.LastName, P.PhoneNumber 
                              FROM OWNER O LEFT JOIN OWNER_PHONENO P ON O.OwnerID = P.OwnerID""")
            owners = self.c.fetchall()
            for o_id, fname, lname, phone in owners:
                display_text = f"{fname} {lname} - {phone or 'No Phone'}"
                self.existing_owner_cb.addItem(display_text, o_id)
        except Exception as e:
            print(f"Error loading existing owners: {e}")

    def auto_capitalize_fields(self, line_edit):
        cursor_pos = line_edit.cursorPosition()
        capitalized = line_edit.text().title()
        if line_edit.text() != capitalized:
            line_edit.setText(capitalized)
            line_edit.setCursorPosition(cursor_pos)

    def check_existing_owner(self):
        try:
            self.c.execute("""SELECT P.PhoneNumber FROM OWNER O JOIN OWNER_PHONENO P ON O.OwnerID = P.OwnerID 
                              WHERE O.FirstName = ? AND O.LastName = ? LIMIT 1;""", 
                           (self.inputs["First Name"].text().strip(), self.inputs["Last Name"].text().strip()))
            res = self.c.fetchone()
            if res: self.inputs["Phone"].setText(res[0])
        except Exception: pass

    def refresh_breed_dropdown(self):
        try:
            self.breed_cb.clear()
            self.c.execute("SELECT DISTINCT BreedType FROM BREED WHERE BreedType IS NOT NULL;")
            breeds = set()
            for row in self.c.fetchall():
                b_str = row[0]
                if " - " in b_str:
                    breeds.add(b_str.split(" - ", 1)[1])
                else:
                    breeds.add(b_str)
            self.breed_cb.addItems(sorted(list(breeds)))
        except Exception: pass

    def submit_data(self):
        try:
            if self.radio_new_owner.isChecked():
                for lbl in ["First Name", "Last Name", "Phone", "Pet Name", "Weight (kg)"]:
                    if not self.inputs[lbl].text().replace("-", "").strip():
                        return QMessageBox.warning(self, "Error", f"Missing required field: {lbl}")
                
                fname, lname, phone = self.inputs["First Name"].text().strip(), self.inputs["Last Name"].text().strip(), self.inputs["Phone"].text().strip()
                self.c.execute("SELECT O.OwnerID FROM OWNER O JOIN OWNER_PHONENO P ON O.OwnerID = P.OwnerID WHERE O.FirstName=? AND O.LastName=? AND P.PhoneNumber=?;", (fname, lname, phone))
                res = self.c.fetchone()
                
                if res: 
                    owner_id = res[0]
                else:
                    self.c.execute("INSERT INTO OWNER (FirstName, LastName) VALUES (?, ?);", (fname, lname))
                    owner_id = self.c.lastrowid 
                    self.c.execute("INSERT INTO OWNER_PHONENO (OwnerID, PhoneNumber) VALUES (?, ?);", (owner_id, phone))
            else:
                owner_idx = self.existing_owner_cb.findText(self.existing_owner_cb.currentText())
                if owner_idx < 0:
                    return QMessageBox.warning(self, "Error", "Please select a valid existing owner from the list.")
                owner_id = self.existing_owner_cb.itemData(owner_idx)
                
                for lbl in ["Pet Name", "Weight (kg)"]:
                    if not self.inputs[lbl].text().strip():
                        return QMessageBox.warning(self, "Error", f"Missing required field: {lbl}")
            
            species_text = self.species_cb.currentText().strip()
            breed_text = self.breed_cb.currentText().strip()
            if not species_text or not breed_text:
                return QMessageBox.warning(self, "Error", "Please specify both Species and Breed.")
                
            final_breed_string = f"{species_text} - {breed_text}"
            
            pet_id = self.generate_unique_pet_id()
            self.c.execute("INSERT INTO PET (PetID, OwnerID, Name, Weight_lbs) VALUES (?, ?, ?, ?);", 
                           (pet_id, owner_id, self.inputs["Pet Name"].text().strip(), float(self.inputs["Weight (kg)"].text() or 0)))
            self.c.execute("INSERT INTO BREED (PetID, BreedType) VALUES (?, ?);", (pet_id, final_breed_string))
            
            behav_idx = self.behavior_cb.findText(self.behavior_cb.currentText())
            if behav_idx < 0:
                return QMessageBox.warning(self, "Error", "Please select a valid Behavior Profile.")
            tag_id = self.behavior_cb.itemData(behav_idx)
            
            self.c.execute("INSERT INTO PET_TAG (PetID, TagID) VALUES (?, ?);", (pet_id, tag_id))
            self.conn.commit()
            
            QMessageBox.information(self, "Success", f"Pet registered successfully!\n\nSecure Pet Tracking ID: {pet_id}\n\nPlease save this ID for check-ins.")
            
            for w in self.inputs.values(): w.clear()
            self.breed_cb.clearEditText()
            self.refresh_dashboard()
            self.refresh_pets_table()
            
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Weight must be a valid number.")
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Database Error", str(e))

    def parse_species(self, b):
        b = str(b).lower()
        if "cat" in b or "feline" in b: return "Cat"
        if "bird" in b or "parrot" in b: return "Bird"
        if "rabbit" in b: return "Rabbit"
        if "reptile" in b: return "Reptile"
        return "Dog"

    # --- Pets Screen ---
    def build_pets_page(self, layout):
        layout.setContentsMargins(25, 25, 25, 25)
        layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 5px;'>📋 Pet Directory</h1>"))
        
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("🔍 Search by ID, Name, Owner, Breed, or Behavior...")
        search_bar.setStyleSheet("padding: 10px; border: 1px solid #CCC; border-radius: 6px; margin-bottom: 10px; font-size: 13px;")
        search_bar.textChanged.connect(lambda text: self.filter_table(text, self.pets_table))
        layout.addWidget(search_bar)
        
        self.pets_table = QTableWidget()
        self.pets_table.setColumnCount(6)
        self.pets_table.setHorizontalHeaderLabels(["Pet ID", "Pet Name", "Owner", "Weight (kg)", "Breed / Species", "Behavior Profile"])
        self.pets_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pets_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.pets_table.horizontalHeader().setStyleSheet(TABLE_HEADER_STYLE)
        self.pets_table.verticalHeader().setDefaultSectionSize(50) 
        self.pets_table.setAlternatingRowColors(True)
        self.pets_table.setStyleSheet("background-color: white; alternate-background-color: #FAFAFA; gridline-color: #E0E0E0; border-radius: 8px;")
        layout.addWidget(self.pets_table)

    def refresh_pets_table(self):
        try:
            self.pets_table.setSortingEnabled(False)
            self.c.execute("""SELECT P.PetID, P.Name, IFNULL(O.FirstName, '') || ' ' || IFNULL(O.LastName, ''), 
                                     P.Weight_lbs, B.BreedType, BT.Behavior 
                              FROM PET P
                              LEFT JOIN OWNER O ON P.OwnerID = O.OwnerID
                              LEFT JOIN BREED B ON P.PetID=B.PetID 
                              LEFT JOIN PET_TAG PT ON P.PetID=PT.PetID 
                              LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID=BT.TagID;""")
            rows = self.c.fetchall()
            self.pets_table.setRowCount(0)
            for r_idx, row in enumerate(rows):
                self.pets_table.insertRow(r_idx)
                for c_idx, val in enumerate(row):
                    if c_idx == 5 and val:
                        self.pets_table.setCellWidget(r_idx, c_idx, self.create_tag_pill(str(val)))
                    else:
                        item = QTableWidgetItem()
                        if isinstance(val, (int, float)):
                            item.setData(Qt.DisplayRole, val)
                        else:
                            item.setData(Qt.DisplayRole, str(val if val is not None else "N/A"))
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                        self.pets_table.setItem(r_idx, c_idx, item)
            self.pets_table.setSortingEnabled(True)
        except Exception: pass

    # --- Bookings Page ---
    def build_bookings_page(self, layout):
        layout.setContentsMargins(25, 25, 25, 25)
        layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 5px;'>📅 Advance Reservations Manager</h1>"))
        
        split_layout = QHBoxLayout()
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 15px;")
        lp_lay = QVBoxLayout(left_panel)
        lp_lay.addWidget(QLabel("<h3 style='color: #4A352B; margin-bottom: 5px;'>Upcoming Scheduled Slots</h3>"))
        
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("🔍 Search reservations...")
        search_bar.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 4px; margin-bottom: 10px;")
        search_bar.textChanged.connect(lambda text: self.filter_table(text, self.bookings_table))
        lp_lay.addWidget(search_bar)
        
        self.bookings_table = QTableWidget()
        self.bookings_table.setColumnCount(6)
        self.bookings_table.setHorizontalHeaderLabels(["Booking ID", "Pet Name", "Owner", "Room Slot", "Visit Date", "Arrival Time"])
        self.bookings_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bookings_table.horizontalHeader().setStyleSheet(TABLE_HEADER_STYLE)
        self.bookings_table.verticalHeader().setDefaultSectionSize(45)
        self.bookings_table.setAlternatingRowColors(True)
        self.bookings_table.setStyleSheet("background-color: white; alternate-background-color: #FAFAFA; gridline-color: #E0E0E0;")
        lp_lay.addWidget(self.bookings_table)
        
        action_lay = QHBoxLayout()
        action_lay.addStretch()
        
        cancel_btn = QPushButton("❌ Cancel Booking")
        cancel_btn.setStyleSheet("background-color: #EF5350; color: white; font-weight: bold; padding: 10px 15px; border-radius: 4px;")
        cancel_btn.clicked.connect(self.cancel_booking)
        action_lay.addWidget(cancel_btn)
        
        insta_btn = QPushButton("⚡ Insta Check-In Selected")
        insta_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px 15px; border-radius: 4px;")
        insta_btn.clicked.connect(self.insta_checkin_booking)
        action_lay.addWidget(insta_btn)
        
        lp_lay.addLayout(action_lay)
        split_layout.addWidget(left_panel, 6)
        
        right_panel = QFrame()
        right_panel.setFixedWidth(340)
        right_panel.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 20px;")
        rp_lay = QVBoxLayout(right_panel)
        rp_lay.addWidget(QLabel("<h3 style='color: #4A352B;'>Encode Phone Reservation</h3>"))
        
        form = QFormLayout()
        form.setSpacing(12)
        self.bk_pet_id, self.bk_room_cb = QLineEdit(), QComboBox()
        
        style = "padding: 8px; border: 1px solid #CCC; border-radius: 4px; background: white;"
        self.bk_start = QDateEdit()
        self.bk_start.setCalendarPopup(True)
        self.bk_start.calendarWidget().setStyleSheet("QCalendarWidget QWidget { color: black; }")
        self.bk_start.setDate(QDate.currentDate())
        self.bk_start.setMinimumDate(QDate.currentDate())
        
        self.bk_hour_cb, self.bk_min_cb, self.bk_period_cb = QComboBox(), QComboBox(), QComboBox()
        self.bk_hour_cb.addItems([f"{i:02d}" for i in range(1, 13)])
        self.bk_min_cb.addItems([f"{i:02d}" for i in range(0, 60, 5)])
        self.bk_period_cb.addItems(["AM", "PM"])
        
        for cb in (self.bk_hour_cb, self.bk_min_cb, self.bk_period_cb): 
            cb.setMinimumWidth(65)
            cb.setStyleSheet(style)
            self.make_searchable(cb, allow_new=False)
            
        self.make_searchable(self.bk_room_cb, allow_new=False)
        
        time_widget = QWidget()
        time_layout = QHBoxLayout(time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.addWidget(self.bk_hour_cb)
        time_layout.addWidget(QLabel("<b>:</b>"))
        time_layout.addWidget(self.bk_min_cb)
        time_layout.addWidget(self.bk_period_cb)
        
        for w in (self.bk_pet_id, self.bk_room_cb, self.bk_start): w.setStyleSheet(style)
        
        form.addRow("Pet ID:", self.bk_pet_id)
        form.addRow("Playroom:", self.bk_room_cb)
        form.addRow("Date:", self.bk_start)
        form.addRow("Time:", time_widget)
        rp_lay.addLayout(form)
        
        book_btn = QPushButton("Validate & Lock Spot")
        book_btn.setStyleSheet("background-color: #FFC107; font-weight: bold; padding: 12px; border-radius: 6px; margin-top: 10px;")
        book_btn.clicked.connect(self.process_booking)
        rp_lay.addWidget(book_btn)
        rp_lay.addStretch()
        
        split_layout.addWidget(right_panel, 4)
        layout.addLayout(split_layout)

    def refresh_bookings_module(self):
        try:
            self.bookings_table.setSortingEnabled(False)
            self.c.execute("""SELECT B.BookingID, P.Name, IFNULL(O.FirstName, '') || ' ' || IFNULL(O.LastName, ''), 
                                     R.RoomName, B.StartDate, B.StartTime 
                              FROM BOOKING B
                              JOIN PET P ON B.PetID = P.PetID 
                              LEFT JOIN OWNER O ON P.OwnerID = O.OwnerID
                              JOIN PLAYROOM R ON B.RoomID = R.RoomID
                              WHERE B.Status = 'Confirmed' ORDER BY B.StartDate ASC, B.StartTime ASC;""")
            bookings = self.c.fetchall()
            self.bookings_table.setRowCount(0)
            for r_idx, r_dat in enumerate(bookings):
                self.bookings_table.insertRow(r_idx)
                for c_idx, val in enumerate(r_dat):
                    item = QTableWidgetItem()
                    if isinstance(val, (int, float)):
                        item.setData(Qt.DisplayRole, val)
                    else:
                        item.setData(Qt.DisplayRole, str(val if val is not None else "N/A"))
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                    self.bookings_table.setItem(r_idx, c_idx, item)
            self.bookings_table.setSortingEnabled(True)
            
            self.bk_room_cb.clear()
            self.c.execute("SELECT RoomID, RoomName, MaxCapacity FROM PLAYROOM;")
            for r_id, r_name, r_cap in self.c.fetchall():
                self.bk_room_cb.addItem(f"{r_name} (Max: {r_cap})", r_id)
                
            curr = datetime.now()
            h = curr.hour % 12 or 12
            m = round(curr.minute / 5) * 5
            if m == 60: m = 55
            
            self.bk_hour_cb.setCurrentIndex(self.bk_hour_cb.findText(f"{h:02d}"))
            self.bk_min_cb.setCurrentIndex(self.bk_min_cb.findText(f"{m:02d}"))
            self.bk_period_cb.setCurrentIndex(self.bk_period_cb.findText("PM" if curr.hour >= 12 else "AM"))
            self.bk_start.setDate(QDate.currentDate())
        except Exception: pass

    def cancel_booking(self):
        r = self.bookings_table.currentRow()
        if r < 0: return QMessageBox.warning(self, "Selection Missing", "Please select a booking to cancel.")
        b_id = int(self.bookings_table.item(r, 0).text())
        reply = QMessageBox.question(self, "Confirm Cancellation", f"Are you sure you want to cancel Booking ID {b_id}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.c.execute("UPDATE BOOKING SET Status='Cancelled' WHERE BookingID=?;", (b_id,))
                self.conn.commit()
                self.refresh_bookings_module()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def insta_checkin_booking(self):
        r = self.bookings_table.currentRow()
        if r < 0: return QMessageBox.warning(self, "Selection Missing", "Please select a booking to check in.")
        b_id = int(self.bookings_table.item(r, 0).text())
        try:
            self.c.execute("SELECT PetID, RoomID, StartDate FROM BOOKING WHERE BookingID=?;", (b_id,))
            res = self.c.fetchone()
            if not res: return
            pet_id, room_id, b_date = res
            
            today = datetime.now().strftime("%Y-%m-%d")
            if b_date != today:
                if QMessageBox.question(self, "Date Mismatch", f"Booking is for {b_date}, not today. Proceed?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.No: return

            is_safe, msg = self.run_safety_matrix(pet_id, room_id)
            if not is_safe: return QMessageBox.critical(self, "DENIED", msg)
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Confirm Check-In Time")
            dialog.setFixedSize(320, 160)
            dialog.setStyleSheet("background: white; font-family: Arial;")
            l = QVBoxLayout(dialog)
            l.addWidget(QLabel(f"Validating check-in for <b>{msg}</b>.<br><br>Adjust actual arrival time below:"))
            
            time_edit = QTimeEdit()
            time_edit.setTime(QTime.currentTime())
            time_edit.setDisplayFormat("hh:mm A")
            time_edit.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 4px;")
            l.addWidget(time_edit)
            
            btn = QPushButton("Complete Check-In")
            btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")
            btn.clicked.connect(dialog.accept)
            l.addWidget(btn)
            
            if dialog.exec_() == QDialog.Accepted:
                actual_time = time_edit.time().toString("hh:mm A")
                self.c.execute("INSERT INTO VISIT (PetID, RoomID, VisitType, VisitDate, StartTime, Notes) VALUES (?, ?, ?, ?, ?, 'Insta Check-in.');", 
                               (pet_id, room_id, 'Reservation', today, actual_time))
                self.c.execute("UPDATE BOOKING SET Status='Checked-In' WHERE BookingID=?;", (b_id,))
                self.conn.commit()
                QMessageBox.information(self, "Success", f"{msg} successfully checked in!")
                self.refresh_bookings_module()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def process_booking(self):
        try:
            p_id_text = self.bk_pet_id.text().strip()
            visit_date = self.bk_start.date().toString("yyyy-MM-dd")
            arrival_time = f"{self.bk_hour_cb.currentText()}:{self.bk_min_cb.currentText()} {self.bk_period_cb.currentText()}"
            
            r_idx = self.bk_room_cb.findText(self.bk_room_cb.currentText())
            if r_idx < 0: return QMessageBox.warning(self, "Error", "Invalid Target Playroom selected.")
            room_id = self.bk_room_cb.itemData(r_idx)
            
            if not p_id_text: return QMessageBox.warning(self, "Input Error", "Please provide a Pet ID Number.")
                
            pet_id = int(p_id_text)
            self.c.execute("SELECT Name FROM PET WHERE PetID = ?;", (pet_id,))
            pet_data = self.c.fetchone()
            
            if not pet_data:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Pet Not Found")
                msg_box.setText(f"🛑 Pet ID '{pet_id}' does not exist.")
                msg_box.setInformativeText("Redirect to Registration page?")
                if msg_box.exec_() == msg_box.addButton("Register Pet", QMessageBox.YesRole): self.switch_page(2)
                return
            
            pet_name = pet_data[0]
            self.c.execute("SELECT RoomName, MaxCapacity FROM PLAYROOM WHERE RoomID = ?;", (room_id,))
            room_name, max_cap = self.c.fetchone()

            self.c.execute("SELECT COUNT(*) FROM BOOKING WHERE RoomID = ? AND Status = 'Confirmed' AND StartDate = ?;", (room_id, visit_date))
            if self.c.fetchone()[0] >= max_cap: return QMessageBox.critical(self, "Playroom Full", f"🛑 Overbooking Blocked!\n'{room_name}' is at capacity ({max_cap}) on {visit_date}.")
                
            self.c.execute("INSERT INTO BOOKING (PetID, RoomID, StartDate, StartTime, Status) VALUES (?, ?, ?, ?, 'Confirmed');", (pet_id, room_id, visit_date, arrival_time))
            self.conn.commit()
            QMessageBox.information(self, "Spot Reserved", f"🎉 Advance reservation confirmed for {pet_name} in {room_name}!")
            self.bk_pet_id.clear()
            self.refresh_bookings_module()
        except ValueError: QMessageBox.warning(self, "Input Error", "Pet ID must be an integer.")
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Database Error", str(e))

    # --- Visitations Screen ---
    def build_visitations_page(self, layout):
        layout.setContentsMargins(25, 25, 25, 25)
        layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 5px;'>🚪 Active Room Visitations Manager</h1>"))
        
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("🔍 Search active visitations...")
        search_bar.setStyleSheet("padding: 10px; border: 1px solid #CCC; border-radius: 6px; margin-bottom: 10px; font-size: 13px;")
        search_bar.textChanged.connect(lambda text: self.filter_table(text, self.visit_table))
        layout.addWidget(search_bar)
        
        split = QHBoxLayout()
        left = QFrame()
        left.setStyleSheet("background: white; padding: 15px; border-radius: 8px; border: 1px solid #EAEAEA;")
        lp = QVBoxLayout(left)
        self.visit_table = QTableWidget()
        self.visit_table.setColumnCount(7)
        self.visit_table.setHorizontalHeaderLabels(["ID", "Pet Name", "Owner", "Behavior Profile", "Room", "Type", "Start Time"])
        self.visit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.visit_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.visit_table.horizontalHeader().setStyleSheet(TABLE_HEADER_STYLE)
        self.visit_table.verticalHeader().setDefaultSectionSize(50)
        self.visit_table.setAlternatingRowColors(True)
        self.visit_table.setStyleSheet("background-color: white; alternate-background-color: #FAFAFA; gridline-color: #E0E0E0;")
        lp.addWidget(self.visit_table)
        
        co = QHBoxLayout()
        self.co_notes = QLineEdit()
        self.co_notes.setPlaceholderText("Enter departure notes...")
        self.co_notes.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 4px;")
        co_btn = QPushButton("Check-Out")
        co_btn.setStyleSheet("background: #EF5350; color: white; font-weight: bold; padding: 10px 15px; border-radius: 4px;")
        co_btn.clicked.connect(self.process_checkout)
        co.addWidget(self.co_notes, 3)
        co.addWidget(co_btn, 1)
        lp.addLayout(co)
        split.addWidget(left, 6)
        
        right = QFrame()
        right.setFixedWidth(340)
        right.setStyleSheet("background: white; padding: 20px; border-radius: 8px; border: 1px solid #EAEAEA;")
        rp = QVBoxLayout(right)
        rp.addWidget(QLabel("<h3 style='color: #4A352B;'>Walk-In Check-In</h3>"))
        
        self.v_form = QFormLayout()
        self.v_form.setSpacing(12)
        self.v_pet_id, self.v_room_cb, self.v_type = QLineEdit(), QComboBox(), QComboBox()
        self.v_type.addItems(["Walk-in", "Reservation"])
        
        style = "padding: 8px; border: 1px solid #CCC; border-radius: 4px; background: white;"
        for w in (self.v_pet_id, self.v_room_cb, self.v_type): w.setStyleSheet(style)
        
        self.make_searchable(self.v_room_cb, allow_new=False)
        self.make_searchable(self.v_type, allow_new=False)
        
        self.v_form.addRow("Pet ID:", self.v_pet_id)
        self.v_form.addRow("Playroom:", self.v_room_cb)
        self.v_form.addRow("Type:", self.v_type)
        rp.addLayout(self.v_form)
        
        cin_btn = QPushButton("Verify & Check-In")
        cin_btn.setStyleSheet("background: #4CAF50; color: white; font-weight: bold; padding: 12px; border-radius: 6px; margin-top: 10px;")
        cin_btn.clicked.connect(self.process_checkin)
        rp.addWidget(cin_btn)
        rp.addStretch()
        split.addWidget(right, 4)
        layout.addLayout(split)

    def refresh_visitations_module(self):
        try:
            self.visit_table.setSortingEnabled(False)
            self.c.execute("""SELECT V.VisitID, P.Name, IFNULL(O.FirstName, '') || ' ' || IFNULL(O.LastName, ''), 
                                     BT.Behavior, R.RoomName, V.VisitType, V.StartTime 
                              FROM VISIT V 
                              JOIN PET P ON V.PetID=P.PetID 
                              LEFT JOIN OWNER O ON P.OwnerID = O.OwnerID
                              LEFT JOIN PET_TAG PT ON P.PetID=PT.PetID 
                              LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID=BT.TagID
                              JOIN PLAYROOM R ON V.RoomID=R.RoomID 
                              WHERE V.EndTime IS NULL OR V.EndTime = '';""")
            rows = self.c.fetchall()
            self.visit_table.setRowCount(0)
            for r_idx, row in enumerate(rows):
                self.visit_table.insertRow(r_idx)
                for c_idx, val in enumerate(row):
                    if c_idx == 3 and val:
                        self.visit_table.setCellWidget(r_idx, c_idx, self.create_tag_pill(str(val)))
                    else:
                        item = QTableWidgetItem()
                        if isinstance(val, (int, float)):
                            item.setData(Qt.DisplayRole, val)
                        else:
                            item.setData(Qt.DisplayRole, str(val if val is not None else "N/A"))
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                        self.visit_table.setItem(r_idx, c_idx, item)
            self.visit_table.setSortingEnabled(True)
            
            self.v_room_cb.clear()
            self.c.execute("SELECT RoomID, RoomName, MaxCapacity FROM PLAYROOM;")
            for r_id, r_name, cap in self.c.fetchall():
                self.c.execute("SELECT COUNT(*) FROM VISIT WHERE RoomID=? AND (EndTime IS NULL OR EndTime = '');", (r_id,))
                self.v_room_cb.addItem(f"{r_name} (Capacity: {self.c.fetchone()[0]}/{cap})", r_id)
        except Exception: pass

    def process_checkin(self):
        p_id = self.v_pet_id.text().strip()
        if not p_id: return
        
        r_idx = self.v_room_cb.findText(self.v_room_cb.currentText())
        if r_idx < 0: return QMessageBox.warning(self, "Error", "Invalid Playroom selected.")
        r_id = self.v_room_cb.itemData(r_idx)
        
        try:
            is_safe, msg = self.run_safety_matrix(int(p_id), r_id)
            if not is_safe:
                return QMessageBox.critical(self, "DENIED", msg)

            self.c.execute("INSERT INTO VISIT (PetID, RoomID, VisitType, VisitDate, StartTime, Notes) VALUES (?, ?, ?, ?, ?, 'Cleared.');", 
                           (int(p_id), r_id, self.v_type.currentText(), datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S")))
            self.conn.commit()
            self.v_pet_id.clear()
            self.refresh_visitations_module()
            QMessageBox.information(self, "Check-In Success", f"Safety verified. {msg} tracked inside safely.")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def process_checkout(self):
        r = self.visit_table.currentRow()
        if r < 0: return QMessageBox.warning(self, "Selection Missing", "Select a row to check out.")
        try:
            self.c.execute("UPDATE VISIT SET EndTime=?, Notes=? WHERE VisitID=?;", (datetime.now().strftime("%H:%M:%S"), self.co_notes.text().strip(), int(self.visit_table.item(r, 0).text())))
            self.conn.commit()
            self.co_notes.clear()
            self.refresh_visitations_module()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def closeEvent(self, e): 
        if hasattr(self, 'cam_widgets'):
            for cam in self.cam_widgets:
                if hasattr(cam, 'thread'):
                    cam.thread.stop()
        self.conn.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ResPAWnsibleApp()
    window.show()
    sys.exit(app.exec_())