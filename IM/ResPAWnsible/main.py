import sys, os, sqlite3, random
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QPushButton, QLabel, QFrame, 
                             QStackedWidget, QComboBox, QCompleter)
from PyQt5.QtCore import Qt

import dashboard
import playrooms
import registration
import directory
import bookings
import visitations
import safety

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'ResPAWnsible(Real).db')

class ResPAWnsibleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ResPAWnsible - Safety-First Boarding")
        self.resize(1200, 700)
        self.setStyleSheet("background-color: #FDFBF7; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px;")
        self.init_db()
        self.init_ui()

        self.setStyleSheet("""
            QMainWindow { 
                background-color: #FDFBF7; 
                font-family: 'Segoe UI', Arial, sans-serif; 
            }
            /* The sleek white container cards */
            QFrame#MainCard { 
                background-color: #FFFFFF; 
                border-radius: 12px; 
                border: 1px solid #E5E0D8; 
            }
            QLabel { 
                color: #3A271E; 
                font-size: 13px; 
            }
            QLabel#Header1 { 
                font-size: 26px; 
                font-weight: 800; 
                color: #3A271E; 
            }
            QLabel#SubHeader { 
                font-size: 16px; 
                font-weight: bold; 
                color: #3A271E; 
                border-bottom: 2px solid #FFC107; 
                padding-bottom: 5px; 
            }
            
            /* Modern, padded input fields */
            QLineEdit, QComboBox, QDateEdit, QTimeEdit {
                padding: 10px; 
                border: 1px solid #D6D0C4; 
                border-radius: 6px; 
                background-color: #FCFAFA; 
                color: #333; 
                font-size: 13px;
            }
            
            /* Make them pop when clicked */
            QLineEdit:focus, QComboBox:focus { 
                border: 2px solid #FFC107; 
                background-color: #FFFFFF; 
            }
            
            /* Locked fields look clearly un-editable */
            QLineEdit:read-only { 
                background-color: #F0EDE5; 
                color: #8C7B70; 
                border: 1px dashed #D6D0C4; 
            }
            
            QComboBox QAbstractItemView { 
                border: 1px solid #D6D0C4; 
                selection-background-color: #FFC107; 
                selection-color: #3A271E; 
            }
            
            /* Brand Action Buttons */
            QPushButton#PrimaryBtn { 
                background-color: #FFC107; 
                color: #3A271E; 
                font-weight: bold; 
                font-size: 14px; 
                padding: 12px; 
                border-radius: 6px; 
                border: none; 
            }
            QPushButton#PrimaryBtn:hover { background-color: #E6AE06; }
            QPushButton#PrimaryBtn:pressed { background-color: #CC9A04; }
            
            /* Custom sleek radio buttons with PERFECT inner dots */
            QRadioButton { 
                font-size: 13px; 
                color: #3A271E; 
                spacing: 8px; 
            }
            QRadioButton::indicator { 
                width: 14px; 
                height: 14px; 
                border-radius: 8px; /* Makes it completely circular */
                border: 2px solid #D6D0C4; 
                background-color: white; 
            }
            QRadioButton::indicator:checked { 
                border: 2px solid #FFC107; 
                /* Magic radial gradient paints an orange dot surrounded by a white gap */
                background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #FFC107, stop:0.5 #FFC107, stop:0.6 white, stop:1 white);
            }
            QComboBox QLineEdit {
                background-color: transparent;
                border: none;
                color: #333;
            }
            QComboBox QLineEdit:read-only {
                background-color: transparent;
                selection-background-color: transparent;
                selection-color: #333;
            }
        """)

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
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            
            self.c.execute("SELECT RoomID, RoomName, MaxCapacity FROM PLAYROOM;")
            for r_id, r_name, r_cap in self.c.fetchall():
                
                self.c.execute("""SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType FROM VISIT V JOIN PET P ON V.PetID = P.PetID
                                  LEFT JOIN PET_TAG PT ON P.PetID = PT.PetID LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID = BT.TagID
                                  LEFT JOIN BREED B ON P.PetID = B.PetID WHERE V.RoomID = ? AND (V.EndTime IS NULL OR V.EndTime = '');""", (r_id,))
                occupants = self.c.fetchall()
                count = len(occupants)
                
                self.c.execute("SELECT StartTime FROM BOOKING WHERE RoomID = ? AND Status = 'Confirmed' AND StartDate = ?;", (r_id, today_str))
                upcoming_count = 0
                for (b_time,) in self.c.fetchall():
                    try:
                        b_dt = datetime.strptime(b_time, "%I:%M %p").replace(year=now.year, month=now.month, day=now.day)
                        time_diff = (b_dt - now).total_seconds() / 3600
                        if 0 <= time_diff <= 2: 
                            upcoming_count += 1
                    except: pass
                
                total_projected = count + upcoming_count
                
                if r_cap and count >= r_cap: 
                    alerts.append(("CRITICAL", "Capacity Overflow", f"{r_name} is currently FULL ({count}/{r_cap}). No further admittance allowed."))
                elif r_cap and total_projected > r_cap:
                    alerts.append(("CRITICAL", "Impending Overflow", f"{r_name} has {count} pet(s), but {upcoming_count} booking(s) are arriving within 2 hours. This will exceed the max capacity of {r_cap}!"))
                elif r_cap and total_projected == r_cap and upcoming_count > 0:
                    alerts.append(("WARNING", "Approaching Capacity", f"{r_name} has {count} pet(s) with {upcoming_count} incoming booking(s) soon. It will be full (Max: {r_cap})."))
                elif r_cap > 1 and count >= r_cap - 1: 
                    alerts.append(("WARNING", "Near Capacity", f"{r_name} is almost full ({count}/{r_cap}). Consider redirecting walk-ins."))
                
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
        except Exception as e: print(e)
        return alerts

    def create_tag_pill(self, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)    
        text_lower = text.lower()
        if "aggressive" in text_lower or "solo" in text_lower: bg, fg, border = "#FFEBEE", "#C62828", "#FFCDD2"
        elif "calm" in text_lower: bg, fg, border = "#F3E5F5", "#6A1B9A", "#E1BEE7"
        elif "hyperactive" in text_lower or "playful" in text_lower: bg, fg, border = "#E3F2FD", "#1565C0", "#BBDEFB"
        elif "nervous" in text_lower or "fearful" in text_lower: bg, fg, border = "#FFF3E0", "#E65100", "#FFE0B2"
        else: bg, fg, border = "#F5F5F5", "#424242", "#E0E0E0"

        lbl.setStyleSheet(f"background-color: {bg}; color: {fg}; border: 1px solid {border}; border-radius: 12px; padding: 4px 14px; font-weight: bold; font-size: 11px;")
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(5, 2, 5, 2)
        
        lay.addStretch()
        lay.addWidget(lbl)
        lay.addStretch()
        
        return container

    def filter_table(self, text, table):
        search_text = text.lower()
        for row in range(table.rowCount()):
            match = False
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
                else:
                    widget = table.cellWidget(row, col)
                    if widget:
                        label = widget.findChild(QLabel)
                        if label and search_text in label.text().lower():
                            match = True
                            break
            table.setRowHidden(row, not match)
            
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
            if i == 0: dashboard.build_page(self, p_layout)
            elif i == 1: playrooms.build_page(self, p_layout)
            elif i == 2: registration.build_page(self, p_layout)
            elif i == 3: directory.build_page(self, p_layout)
            elif i == 4: bookings.build_page(self, p_layout)
            elif i == 5: visitations.build_page(self, p_layout)
            elif i == 6: safety.build_page(self, p_layout)
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
        
        if index == 0: dashboard.refresh(self)
        elif index == 2: registration.refresh(self)
        elif index == 3: directory.refresh(self)
        elif index == 4: bookings.refresh(self)
        elif index == 5: visitations.refresh(self)
        elif index == 6: safety.refresh(self)

    def run_safety_matrix(self, pet_id, room_id, check_occupants=True):
        self.c.execute("SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType FROM PET P LEFT JOIN BREED B ON P.PetID=B.PetID LEFT JOIN PET_TAG PT ON P.PetID=PT.PetID LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID=BT.TagID WHERE P.PetID=?;", (pet_id,))
        p_prof = self.c.fetchone()
        if not p_prof: return False, "Invalid Pet ID."
        
        pet_name = p_prof[0]
        behavior = str(p_prof[2]).lower()
        
        if check_occupants:
            self.c.execute("SELECT COUNT(*) FROM VISIT WHERE PetID=? AND (EndTime IS NULL OR EndTime = '');", (pet_id,))
            if self.c.fetchone()[0] > 0: return False, "Pet is already actively checked in."

        self.c.execute("SELECT RoomName FROM PLAYROOM WHERE RoomID=?;", (room_id,))
        room_name = str(self.c.fetchone()[0]).lower()
        
        if "aggressive" in room_name and "aggressive" not in behavior:
            return False, f"Behavior Mismatch: '{room_name.title()}' is strictly reserved for Aggressive pets only."
        if "aggressive" in behavior and "aggressive" not in room_name and "solo" not in room_name:
            return False, f"Behavior Mismatch: {pet_name} (Aggressive) MUST be assigned to an Aggressive Room or Solo Room."
        
        if "fearful" in room_name and "fearful" not in behavior and "nervous" not in behavior:
            return False, f"Behavior Mismatch: '{room_name.title()}' is strictly reserved for Nervous/Fearful pets only."
        if ("fearful" in behavior or "nervous" in behavior) and "fearful" not in room_name and "solo" not in room_name:
            return False, f"Behavior Mismatch: {pet_name} (Nervous/Fearful) MUST be assigned to the Fearful Room or a Solo Room."
            
        if "calm" in room_name and "calm" not in behavior and "friendly" not in behavior:
            return False, f"Behavior Mismatch: '{room_name.title()}' is strictly reserved for Calm or Friendly pets only."

        if "hyperactive" in behavior or "playful" in behavior:
            if "friendly" not in room_name and "solo" not in room_name:
                return False, f"Behavior Mismatch: {pet_name} (Hyperactive/Playful) MUST be assigned to the Friendly Room or a Solo Room."
                
        if "calm" in behavior or "friendly" in behavior:
            if "calm" not in room_name and "friendly" not in room_name and "solo" not in room_name:
                return False, f"Behavior Mismatch: {pet_name} (Friendly/Calm) should be assigned to the Calm, Friendly, or Solo rooms."
                
        if check_occupants:
            if "solo" in room_name:
                self.c.execute("SELECT COUNT(*) FROM VISIT WHERE RoomID=? AND (EndTime IS NULL OR EndTime = '');", (room_id,))
                if self.c.fetchone()[0] >= 1:
                    return False, f"Capacity Overflow: {room_name.title()} is a single-occupancy room and is currently occupied."

            self.c.execute("SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType FROM VISIT V JOIN PET P ON V.PetID = P.PetID LEFT JOIN BREED B ON P.PetID = B.PetID LEFT JOIN PET_TAG PT ON P.PetID = PT.PetID LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID = BT.TagID WHERE V.RoomID=? AND (V.EndTime IS NULL OR V.EndTime = '');", (room_id,))
            occupants = self.c.fetchall()
            
            sp, sz = self.parse_species(p_prof[3]), "Small" if (p_prof[1] or 0) < 30 else "Large"
            for o in occupants:
                o_sp, o_sz = self.parse_species(o[3]), "Small" if (o[1] or 0) < 30 else "Large"
                if sp != o_sp:
                    return False, f"Species Mismatch: Cannot mix a {sp} with a {o_sp} in the same playroom."

        return True, p_prof[0]

    def parse_species(self, b):
        b = str(b).lower()
        if "cat" in b or "feline" in b: return "Cat"
        if "bird" in b or "parrot" in b: return "Bird"
        if "rabbit" in b: return "Rabbit"
        if "reptile" in b: return "Reptile"
        return "Dog"

    def zoom_into_room(self, room_name):
        self.switch_page(1) 
        self.expanded_cam = None
        for cam in self.cam_widgets: cam.show()
        for cam in self.cam_widgets:
            if room_name in cam.title.text():
                self.expanded_cam = cam
                for alternative_cam in self.cam_widgets:
                    if alternative_cam != cam: alternative_cam.hide()
                break

    def closeEvent(self, e): 
        if hasattr(self, 'cam_widgets'):
            for cam in self.cam_widgets:
                if hasattr(cam, 'thread'): cam.thread.stop()
        self.conn.close()

    def make_searchable(self, combobox, allow_new=False, locked=False):
        combobox.setEditable(True)
        
        if locked:
            combobox.lineEdit().setReadOnly(True)
            combobox.lineEdit().setCursor(Qt.PointingHandCursor if hasattr(Qt, 'PointingHandCursor') else 13)
            combobox.lineEdit().mousePressEvent = lambda e: combobox.showPopup()
        else:
            completer = QCompleter(combobox.model(), self)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            combobox.setCompleter(completer)
            
        if not allow_new:
            combobox.setInsertPolicy(QComboBox.NoInsert)

if __name__ == '__main__':
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)
    
    window = ResPAWnsibleApp()
    window.show()
    sys.exit(app.exec_())