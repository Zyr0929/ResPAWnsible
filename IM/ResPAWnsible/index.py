import sys, os, sqlite3
import cv2
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
                             QPushButton, QMessageBox, QLabel, QFrame, QStackedWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QCompleter, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'ResPAWNsible(Real).db')

# --- Camera Threading Classes ---
class CameraFeed(QWidget):
    def __init__(self, camera_id=0, name="Camera"):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.title = QLabel(f"<b>{name}</b>")
        self.title.setStyleSheet("background: white; padding: 5px; border-radius: 3px;")
        self.layout.addWidget(self.title)
        self.feed_label = QLabel("Initializing Camera...")
        self.feed_label.setStyleSheet("background: black; color: white;")
        self.feed_label.setAlignment(Qt.AlignCenter)
        self.feed_label.setFixedSize(320, 240)
        self.layout.addWidget(self.feed_label)
        self.thread = VideoThread(camera_id)
        self.thread.frame_signal.connect(self.update_image)
        self.thread.start()

    def update_image(self, q_img): self.feed_label.setPixmap(QPixmap.fromImage(q_img))

class VideoThread(QThread):
    frame_signal = pyqtSignal(QImage)
    def __init__(self, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self._run = True
    def run(self):
        cap = cv2.VideoCapture(self.camera_id)
        while self._run:
            ret, frame = cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                q_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).scaled(320, 240, Qt.KeepAspectRatio)
                self.frame_signal.emit(q_img)
        cap.release()
    def stop(self):
        self._run = False
        self.wait()

# --- Main Application ---
class ResPAWnsibleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ResPAWnsible - Safety-First Boarding")
        self.resize(1150, 650)
        self.setStyleSheet("background-color: #FDFBF7; font-family: Arial; font-size: 12px;")
        self.init_db()
        self.init_ui()

    def init_db(self):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys = ON;")
        try: self.c.execute("SELECT TagID, Behavior FROM BEHAVIOR_TAG;")
        except sqlite3.OperationalError:
            self.tags = []
            return
        self.tags = self.c.fetchall()
        if not self.tags:
            defaults = [("Calm / Friendly",), ("Nervous / Fearful",), ("Hyperactive / Playful",), ("Agressive / Territorial",), ("Requires Solo Room",)]
            self.c.executemany("INSERT INTO BEHAVIOR_TAG (Behavior) VALUES (?);", defaults)
            self.conn.commit()
            self.c.execute("SELECT TagID, Behavior FROM BEHAVIOR_TAG;")
            self.tags = self.c.fetchall()

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
                
                # Capacity Rules (Fixed to ignore solo rooms for "almost full" warnings)
                if r_cap and count >= r_cap: 
                    alerts.append(("CRITICAL", "Capacity Overflow", f"{r_name} is FULL ({count}/{r_cap}). No further admittance allowed."))
                elif r_cap > 1 and count >= r_cap - 1: 
                    alerts.append(("WARNING", "Near Capacity", f"{r_name} is almost full ({count}/{r_cap}). Consider redirecting check-ins to another room."))
                
                if count < 2: continue
                solo = [p for p in occupants if "Requires Solo Room" in str(p[2])]
                if solo: alerts.append(("CRITICAL", "Isolation Breach", f"{solo[0][0]} requires a solo room, but {count-1} other pets are inside {r_name}."))
                species = set([self.parse_species(p[3]) for p in occupants])
                if len(species) > 1: alerts.append(("CRITICAL", "Species Mismatch", f"{r_name} contains mixed species: {', '.join(species)}."))
                dogs = [p for p in occupants if self.parse_species(p[3]) == "Dog"]
                aggr = [p for p in dogs if "Agressive" in str(p[2]) or "Aggressive" in str(p[2])]
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
        if "agressive" in text_lower or "aggressive" in text_lower or "solo" in text_lower:
            bg, fg, border = "#FFEBEE", "#C62828", "#FFCDD2"
        elif "calm" in text_lower:
            bg, fg, border = "#F3E5F5", "#6A1B9A", "#E1BEE7"
        elif "hyperactive" in text_lower or "playful" in text_lower:
            bg, fg, border = "#E3F2FD", "#1565C0", "#BBDEFB"
        elif "nervous" in text_lower or "fearful" in text_lower:
            bg, fg, border = "#FFF3E0", "#E65100", "#FFE0B2"
        else:
            bg, fg, border = "#F5F5F5", "#424242", "#E0E0E0"

        lbl.setStyleSheet(f"background-color: {bg}; color: {fg}; border: 1px solid {border}; border-radius: 10px; padding: 4px 12px; font-weight: bold; font-size: 11px;")
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(5, 2, 5, 2)
        lay.addWidget(lbl)
        lay.addStretch() 
        return container

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background-color: #3A271E; color: white;")
        side_layout = QVBoxLayout(sidebar)
        side_layout.addWidget(QLabel("<h2>ResPAWnsible</h2><p>Safety-First Boarding</p>"))

        self.nav_btns = []
        nav_items = ["Dashboard", "Live Playrooms", "Register Pet", "Pets", "Bookings", "Visitations", "Safety Reports"]
        self.stack = QStackedWidget()
        
        for i, nav in enumerate(nav_items):
            btn = QPushButton(f"   {nav}")
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
            elif i == 5: self.build_visitations_page(p_layout)
            elif i == 6: self.build_safety_reports_page(p_layout)
            else: p_layout.addWidget(QLabel(f"<h1 style='color: #333;'>{nav} Page (Under Construction)</h1>"))
            self.stack.addWidget(page)
            
        side_layout.addStretch()
        self.active_lbl = QLabel(f"Registered Pets<br><b>{self.get_dashboard_count()} Pets</b>")
        self.active_lbl.setStyleSheet("background-color: #4A352B; padding: 10px; border-radius: 3px;")
        side_layout.addWidget(self.active_lbl)
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack)
        
        self.switch_page(0)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_btns):
            bg = "#FFC107" if i == index else "#3A271E"
            fg = "black" if i == index else "white"
            btn.setStyleSheet(f"text-align: left; background-color: {bg}; color: {fg}; padding: 10px; font-weight: bold; border-radius: 3px; border: none;")
        
        if index == 0: self.refresh_dashboard()
        if index == 2: self.refresh_breed_completer()
        if index == 3: self.refresh_pets_table()
        if index == 5: self.refresh_visitations_module()
        if index == 6: self.refresh_safety_reports()

    # --- Dashboard Page ---
    def build_dashboard_page(self, layout):
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<h1 style='color: #333;'>Dashboard</h1>"))
        stats_layout = QHBoxLayout()
        self.dash_stats = {}
        for title in ["Total Registered Pets", "Active Visitations", "Safety Alerts", "Room Utilization"]:
            card = QFrame()
            card.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 5px; padding: 10px;")
            c_layout = QVBoxLayout(card)
            c_layout.addWidget(QLabel(f"<span style='color: #666; font-size: 12px;'>{title}</span>"))
            val_lbl = QLabel()
            self.dash_stats[title] = val_lbl 
            c_layout.addWidget(val_lbl)
            stats_layout.addWidget(card)
        layout.addLayout(stats_layout)
        self.dash_alerts_layout = QVBoxLayout()
        alerts_frame = QFrame()
        alerts_frame.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 5px; padding: 15px;")
        alerts_frame.setLayout(self.dash_alerts_layout)
        layout.addWidget(alerts_frame)
        layout.addStretch()

    def refresh_dashboard(self):
        self.dash_stats["Total Registered Pets"].setText(f"<span style='font-size: 26px; font-weight: bold; color: #333;'>{self.get_dashboard_count()}</span>")
        self.dash_stats["Active Visitations"].setText(f"<span style='font-size: 26px; font-weight: bold; color: #333;'>{self.get_active_visits()}</span>")
        self.dash_stats["Room Utilization"].setText(f"<span style='font-size: 26px; font-weight: bold; color: #333;'>{self.get_room_utilization()}</span>")
        alerts = self.generate_safety_alerts()
        self.dash_stats["Safety Alerts"].setText(f"<span style='font-size: 26px; font-weight: bold; color: {'#E57373' if alerts else '#333'};'>{len(alerts)}</span>")
        for i in reversed(range(self.dash_alerts_layout.count())): 
            self.dash_alerts_layout.itemAt(i).widget().setParent(None)
        self.dash_alerts_layout.addWidget(QLabel("<h3>Top Safety Priorities</h3>"))
        if not alerts: self.dash_alerts_layout.addWidget(QLabel("<p style='color: #4CAF50;'>✅ All playrooms are operating safely within defined parameters.</p>"))
        else:
            for severity, title, msg in alerts[:3]:
                color, border = ("#FFEBEE", "#E57373") if severity == "CRITICAL" else ("#FFFDF0", "#FFC107")
                lbl = QLabel(f"<b>⚠️ {title}</b><br><span style='color: #555;'>{msg}</span>")
                lbl.setStyleSheet(f"background: {color}; border: 1px solid {border}; padding: 8px; border-radius: 3px;")
                self.dash_alerts_layout.addWidget(lbl)

    # --- Live Playrooms Page ---
    def build_live_playrooms_page(self, layout):
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<h1 style='color: #333;'>📹 Live Playroom Cameras</h1>"))
        cam_layout = QHBoxLayout()
        cam_layout.addWidget(CameraFeed(camera_id=0, name="Playroom A"))
        cam_layout.addWidget(CameraFeed(camera_id=1, name="Playroom B"))
        cam_layout.addStretch()
        layout.addLayout(cam_layout)
        layout.addStretch()

    # --- Safety Reports Page ---
    def build_safety_reports_page(self, layout):
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<h1 style='color: #333;'>🛡️ Facility Safety & Audit Reports</h1>"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.safety_layout = QVBoxLayout(container)
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def refresh_safety_reports(self):
        for i in reversed(range(self.safety_layout.count())): 
            w = self.safety_layout.itemAt(i).widget()
            if w: w.setParent(None)
        alerts = self.generate_safety_alerts()
        if not alerts:
            box = QLabel("<h2>✅ Zero Active Threats</h2><p>System audit cleared. All capacity and behavioral matrices are optimal.</p>")
            box.setStyleSheet("background: #E8F5E9; border: 2px solid #4CAF50; color: #2E7D32; padding: 20px; border-radius: 5px;")
            self.safety_layout.addWidget(box)
        else:
            for severity, title, msg in alerts:
                box = QFrame()
                color, border, t_color = ("#FFEBEE", "#E57373", "#C62828") if severity == "CRITICAL" else ("#FFFDF0", "#FFC107", "#F57F17")
                box.setStyleSheet(f"background-color: {color}; border: 1px solid {border}; border-left: 5px solid {border}; border-radius: 3px; padding: 15px;")
                b_lay = QVBoxLayout(box)
                b_lay.addWidget(QLabel(f"<h3 style='color: {t_color}; margin: 0;'>[{severity}] {title}</h3>"))
                b_lay.addWidget(QLabel(f"<span style='font-size: 13px;'>{msg}</span>"))
                self.safety_layout.addWidget(box)
        self.safety_layout.addStretch()

    # --- Registration Page ---
    def build_registration_page(self, layout):
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<h1 style='color: #333;'>🐾 Register New Pet</h1>"))
        container = QFrame()
        container.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 5px; padding: 20px;")
        form = QFormLayout(container)
        self.inputs = {"First Name": QLineEdit(), "Last Name": QLineEdit(), "Phone": QLineEdit(), "Pet Name": QLineEdit(), "Weight (kg)": QLineEdit(), "Breed": QLineEdit()}
        style = "padding: 5px; border: 1px solid #CCC; border-radius: 3px; background: white;"
        for widget in self.inputs.values(): widget.setStyleSheet(style)
        self.inputs["Phone"].setInputMask("9999-999-9999")
        self.inputs["First Name"].textEdited.connect(lambda: self.auto_capitalize_fields(self.inputs["First Name"]))
        self.inputs["Last Name"].textEdited.connect(lambda: self.auto_capitalize_fields(self.inputs["Last Name"]))
        self.inputs["First Name"].editingFinished.connect(self.check_existing_owner)
        self.inputs["Last Name"].editingFinished.connect(self.check_existing_owner)

        form.addRow(QLabel("<h3>👤 Owner Information</h3>"))
        form.addRow("First Name:", self.inputs["First Name"])
        form.addRow("Last Name:", self.inputs["Last Name"])
        form.addRow("Phone Number:", self.inputs["Phone"])
        form.addRow(QLabel("<br>"))
        form.addRow(QLabel("<h3>🐶 Pet Details</h3>"))
        form.addRow("Pet Name:", self.inputs["Pet Name"])
        form.addRow("Weight (kg):", self.inputs["Weight (kg)"])
        form.addRow("Breed Type:", self.inputs["Breed"])

        self.behavior_cb = QComboBox()
        self.behavior_cb.setStyleSheet(style)
        for t_id, t_name in self.tags: self.behavior_cb.addItem(t_name, t_id)
        form.addRow("Behavior Tag:", self.behavior_cb)
        btn = QPushButton("Submit Registration")
        btn.setStyleSheet("background-color: #FFC107; font-weight: bold; padding: 10px; border-radius: 5px; border: none;")
        btn.clicked.connect(self.submit_data)
        form.addRow("", btn)
        layout.addWidget(container)
        layout.addStretch()

    def auto_capitalize_fields(self, line_edit):
        cursor_pos = line_edit.cursorPosition()
        capitalized = line_edit.text().title()
        if line_edit.text() != capitalized:
            line_edit.setText(capitalized)
            line_edit.setCursorPosition(cursor_pos)

    def check_existing_owner(self):
        try:
            self.c.execute("""SELECT P.PhoneNumber FROM OWNER O JOIN OWNER_PHONENO P ON O.OwnerID = P.OwnerID WHERE O.FirstName = ? AND O.LastName = ? LIMIT 1;""", (self.inputs["First Name"].text().strip(), self.inputs["Last Name"].text().strip()))
            res = self.c.fetchone()
            if res: self.inputs["Phone"].setText(res[0])
        except Exception: pass

    def refresh_breed_completer(self):
        try:
            self.c.execute("SELECT DISTINCT BreedType FROM BREED WHERE BreedType IS NOT NULL;")
            completer = QCompleter([row[0] for row in self.c.fetchall()], self)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.inputs["Breed"].setCompleter(completer)
        except Exception: pass

    def submit_data(self):
        for lbl, w in self.inputs.items():
            if not w.text().replace("-", "").strip():
                QMessageBox.warning(self, "Error", f"Missing field: {lbl}")
                return
        try:
            fname, lname, phone = self.inputs["First Name"].text().strip(), self.inputs["Last Name"].text().strip(), self.inputs["Phone"].text().strip()
            self.c.execute("SELECT O.OwnerID FROM OWNER O JOIN OWNER_PHONENO P ON O.OwnerID = P.OwnerID WHERE O.FirstName=? AND O.LastName=? AND P.PhoneNumber=?;", (fname, lname, phone))
            res = self.c.fetchone()
            if res: owner_id = res[0]
            else:
                self.c.execute("INSERT INTO OWNER (FirstName, LastName) VALUES (?, ?);", (fname, lname))
                owner_id = self.c.lastrowid 
                self.c.execute("INSERT INTO OWNER_PHONENO (OwnerID, PhoneNumber) VALUES (?, ?);", (owner_id, phone))
            
            self.c.execute("INSERT INTO PET (OwnerID, Name, Weight_lbs) VALUES (?, ?, ?);", (owner_id, self.inputs["Pet Name"].text().strip(), float(self.inputs["Weight (kg)"].text() or 0)))
            pet_id = self.c.lastrowid  
            self.c.execute("INSERT INTO BREED (PetID, BreedType) VALUES (?, ?);", (pet_id, self.inputs["Breed"].text().strip()))
            self.c.execute("INSERT INTO PET_TAG (PetID, TagID) VALUES (?, ?);", (pet_id, self.behavior_cb.currentData()))
            self.conn.commit()
            QMessageBox.information(self, "Success", "Registered successfully!")
            for w in self.inputs.values(): w.clear()
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Error", str(e))

    # --- Pets Screen ---
    def build_pets_page(self, layout):
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<h1 style='color: #333;'>📋 Pet Directory</h1>"))
        self.pets_table = QTableWidget()
        self.pets_table.setColumnCount(5)
        self.pets_table.setHorizontalHeaderLabels(["Pet ID", "Name", "Weight (kg)", "Breed / Species", "Behavior Profile"])
        self.pets_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pets_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.pets_table.verticalHeader().setDefaultSectionSize(45) 
        self.pets_table.setStyleSheet("background-color: white; gridline-color: #E0E0E0;")
        layout.addWidget(self.pets_table)

    def refresh_pets_table(self):
        try:
            self.c.execute("""SELECT P.PetID, P.Name, P.Weight_lbs, B.BreedType, BT.Behavior FROM PET P
                              LEFT JOIN BREED B ON P.PetID=B.PetID LEFT JOIN PET_TAG PT ON P.PetID=PT.PetID LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID=BT.TagID;""")
            rows = self.c.fetchall()
            self.pets_table.setRowCount(0)
            for r_idx, row in enumerate(rows):
                self.pets_table.insertRow(r_idx)
                for c_idx, val in enumerate(row):
                    if c_idx == 4 and val:
                        self.pets_table.setCellWidget(r_idx, c_idx, self.create_tag_pill(str(val)))
                    else:
                        item = QTableWidgetItem(str(val if val is not None else "N/A"))
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                        self.pets_table.setItem(r_idx, c_idx, item)
        except Exception: pass

    # --- Visitations Screen ---
    def build_visitations_page(self, layout):
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<h1 style='color: #333;'>🚪 Active Room Visitations Manager</h1>"))
        split = QHBoxLayout()
        
        left = QFrame()
        left.setStyleSheet("background: white; padding: 10px; border-radius: 5px;")
        lp = QVBoxLayout(left)
        self.visit_table = QTableWidget()
        self.visit_table.setColumnCount(6)
        self.visit_table.setHorizontalHeaderLabels(["ID", "Pet", "Behavior Profile", "Room", "Type", "Start Time"])
        self.visit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.visit_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.visit_table.verticalHeader().setDefaultSectionSize(45)
        lp.addWidget(self.visit_table)
        
        co = QHBoxLayout()
        self.co_notes = QLineEdit()
        self.co_notes.setPlaceholderText("Notes...")
        self.co_notes.setStyleSheet("padding: 5px; border: 1px solid #CCC;")
        co_btn = QPushButton("Check-Out")
        co_btn.setStyleSheet("background: #E57373; font-weight: bold; padding: 6px;")
        co_btn.clicked.connect(self.process_checkout)
        co.addWidget(self.co_notes, 3)
        co.addWidget(co_btn, 1)
        lp.addLayout(co)
        split.addWidget(left, 6)
        
        right = QFrame()
        right.setFixedWidth(340)
        right.setStyleSheet("background: white; padding: 15px; border-radius: 5px;")
        rp = QVBoxLayout(right)
        self.v_form = QFormLayout()
        self.v_pet_id, self.v_room_cb, self.v_type = QLineEdit(), QComboBox(), QComboBox()
        self.v_type.addItems(["Reservation", "Walk-in"])
        for w in (self.v_pet_id, self.v_room_cb, self.v_type): w.setStyleSheet("padding: 5px; border: 1px solid #CCC; background: white;")
        
        self.v_form.addRow("Pet ID:", self.v_pet_id)
        self.v_form.addRow("Playroom:", self.v_room_cb)
        self.v_form.addRow("Type:", self.v_type)
        rp.addLayout(self.v_form)
        
        cin_btn = QPushButton("Check-In")
        cin_btn.setStyleSheet("background: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        cin_btn.clicked.connect(self.process_checkin)
        rp.addWidget(cin_btn)
        rp.addStretch()
        split.addWidget(right, 4)
        layout.addLayout(split)

    def parse_species(self, b):
        b = str(b).lower()
        if "cat" in b or "feline" in b: return "Cat"
        if "bird" in b or "parrot" in b: return "Bird"
        return "Dog"

    def refresh_visitations_module(self):
        try:
            self.c.execute("""SELECT V.VisitID, P.Name, BT.Behavior, R.RoomName, V.VisitType, V.StartTime FROM VISIT V 
                              JOIN PET P ON V.PetID=P.PetID LEFT JOIN PET_TAG PT ON P.PetID=PT.PetID LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID=BT.TagID
                              JOIN PLAYROOM R ON V.RoomID=R.RoomID WHERE V.EndTime IS NULL OR V.EndTime = '';""")
            rows = self.c.fetchall()
            self.visit_table.setRowCount(0)
            for r_idx, row in enumerate(rows):
                self.visit_table.insertRow(r_idx)
                for c_idx, val in enumerate(row):
                    if c_idx == 2 and val:
                        self.visit_table.setCellWidget(r_idx, c_idx, self.create_tag_pill(str(val)))
                    else:
                        item = QTableWidgetItem(str(val))
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                        self.visit_table.setItem(r_idx, c_idx, item)
            
            self.v_room_cb.clear()
            self.c.execute("SELECT RoomID, RoomName, MaxCapacity FROM PLAYROOM;")
            for r_id, r_name, cap in self.c.fetchall():
                self.c.execute("SELECT COUNT(*) FROM VISIT WHERE RoomID=? AND (EndTime IS NULL OR EndTime = '');", (r_id,))
                self.v_room_cb.addItem(f"{r_name} ({self.c.fetchone()[0]}/{cap})", r_id)
        except Exception: pass

    def process_checkin(self):
        p_id = self.v_pet_id.text().strip()
        if not p_id: return
        r_id = self.v_room_cb.currentData()
        if not r_id: return
        try:
            self.c.execute("SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType FROM PET P LEFT JOIN BREED B ON P.PetID=B.PetID LEFT JOIN PET_TAG PT ON P.PetID=PT.PetID LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID=BT.TagID WHERE P.PetID=?;", (int(p_id),))
            p_prof = self.c.fetchone()
            if not p_prof: return QMessageBox.warning(self, "Error", "Invalid Pet ID.")
            
            self.c.execute("SELECT COUNT(*) FROM VISIT WHERE PetID=? AND (EndTime IS NULL OR EndTime = '');", (int(p_id),))
            if self.c.fetchone()[0] > 0: return QMessageBox.warning(self, "Blocked", "Pet already checked in.")

            self.c.execute("SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType FROM VISIT V JOIN PET P ON V.PetID=P.PetID LEFT JOIN BREED B ON P.PetID=B.PetID LEFT JOIN PET_TAG PT ON P.PetID=PT.PetID LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID=BT.TagID WHERE V.RoomID=? AND (V.EndTime IS NULL OR V.EndTime = '');", (r_id,))
            occupants = self.c.fetchall()
            
            sp, sz = self.parse_species(p_prof[3]), "Small" if (p_prof[1] or 0) < 30 else "Large"
            for o in occupants:
                o_sp, o_sz = self.parse_species(o[3]), "Small" if (o[1] or 0) < 30 else "Large"
                if "Requires Solo Room" in [str(p_prof[2]), str(o[2])] or sp != o_sp:
                    return QMessageBox.critical(self, "DENIED", "Safety Rule Violation (Isolation/Species).")
                if sp == "Dog" and (("Aggressive" in str(p_prof[2]) and "Calm" in str(o[2])) or ("Calm" in str(p_prof[2]) and "Aggressive" in str(o[2])) or (("Agressive" in str(p_prof[2]) or "Agressive" in str(o[2]) or "Aggressive" in str(p_prof[2]) or "Aggressive" in str(o[2])) and sz != o_sz)):
                    return QMessageBox.critical(self, "DENIED", "Safety Rule Violation (Behavior/Size Mismatch).")

            self.c.execute("INSERT INTO VISIT (PetID, RoomID, VisitType, VisitDate, StartTime, Notes) VALUES (?, ?, ?, ?, ?, 'Cleared.');", (int(p_id), r_id, self.v_type.currentText(), datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S")))
            self.conn.commit()
            self.v_pet_id.clear()
            self.refresh_visitations_module()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def process_checkout(self):
        r = self.visit_table.currentRow()
        if r < 0: return
        try:
            self.c.execute("UPDATE VISIT SET EndTime=?, Notes=? WHERE VisitID=?;", (datetime.now().strftime("%H:%M:%S"), self.co_notes.text().strip(), int(self.visit_table.item(r, 0).text())))
            self.conn.commit()
            self.co_notes.clear()
            self.refresh_visitations_module()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def closeEvent(self, e): self.conn.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ResPAWnsibleApp()
    window.show()
    sys.exit(app.exec_())