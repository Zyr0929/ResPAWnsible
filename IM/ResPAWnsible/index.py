import sys, os, sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
                             QPushButton, QMessageBox, QLabel, QFrame, QStackedWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'ResPAWNsible(Real).db')

class ResPAWnsibleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ResPAWnsible - Safety-First Boarding")
        self.resize(1100, 650)
        self.setStyleSheet("background-color: #FDFBF7; font-family: Arial; font-size: 12px;")
        
        self.init_db()
        self.init_ui()

    def init_db(self):
        """Initializes database tables and default tags."""
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
                        ("Agressive / Territorial",), ("Requires Solo Room",)]
            self.c.executemany("INSERT INTO BEHAVIOR_TAG (Behavior) VALUES (?);", defaults)
            self.conn.commit()
            self.c.execute("SELECT TagID, Behavior FROM BEHAVIOR_TAG;")
            self.tags = self.c.fetchall()

    def get_dashboard_count(self):
        try:
            self.c.execute("SELECT COUNT(PetID) FROM PET;")
            return str(self.c.fetchone()[0])
        except sqlite3.OperationalError:
            return "0"

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Sidebar Navigation ---
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
            
            # Setup Page Shells
            page = QWidget()
            p_layout = QVBoxLayout(page)
            if i == 0: self.build_dashboard_page(p_layout)
            elif i == 2: self.build_registration_page(p_layout)
            elif i == 3: self.build_pets_page(p_layout)
            elif i == 5: self.build_visitations_page(p_layout)
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
        
        if index == 3: self.refresh_pets_table()
        if index == 5: self.refresh_visitations_module()

    # --- Dashboard Page ---
    def build_dashboard_page(self, layout):
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<h1 style='color: #333;'>Dashboard</h1>"))

        stats_layout = QHBoxLayout()
        for title, val in [("Total Registered Pets", self.get_dashboard_count()), ("Active Bookings", "0"), ("Safety Alerts", "0"), ("Room Utilization", "0%")]:
            card = QFrame()
            card.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 5px; padding: 10px;")
            c_layout = QVBoxLayout(card)
            c_layout.addWidget(QLabel(f"<span style='color: #666; font-size: 12px;'>{title}</span>"))
            c_layout.addWidget(QLabel(f"<span style='font-size: 26px; font-weight: bold; color: #333;'>{val}</span>"))
            stats_layout.addWidget(card)
        layout.addLayout(stats_layout)

        bottom_layout = QHBoxLayout()
        for title, msg in [("Recent Safety Alerts", "⚠️ Database Notice: Active tables loaded."), ("Upcoming Check-ins", "All playrooms synchronized successfully.")]:
            box = QFrame()
            box.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 5px; padding: 15px;")
            b_lay = QVBoxLayout(box)
            b_lay.addWidget(QLabel(f"<h3>{title}</h3>"))
            b_lay.addWidget(QLabel(f"<p style='color: #555;'>{msg}</p>"))
            b_lay.addStretch()
            bottom_layout.addWidget(box)
        layout.addLayout(bottom_layout)

    # --- Registration Page ---
    def build_registration_page(self, layout):
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<h1 style='color: #333;'>🐾 Register New Pet</h1>"))
        
        container = QFrame()
        container.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 5px; padding: 20px;")
        form = QFormLayout(container)
        
        self.inputs = {"First Name": QLineEdit(), "Last Name": QLineEdit(), "Phone": QLineEdit(),
                       "Pet Name": QLineEdit(), "Weight (lbs)": QLineEdit(), "Breed": QLineEdit()}
        
        style = "padding: 5px; border: 1px solid #CCC; border-radius: 3px;"
        for label, widget in self.inputs.items():
            widget.setStyleSheet(style)
            form.addRow(f"{label}:", widget)

        self.behavior_cb = QComboBox()
        self.behavior_cb.setStyleSheet(style)
        for tag_id, tag_name in self.tags:
            self.behavior_cb.addItem(tag_name, tag_id)
        form.addRow("Behavior Tag:", self.behavior_cb)
        
        btn = QPushButton("Submit Registration")
        btn.setStyleSheet("background-color: #FFC107; font-weight: bold; padding: 10px; border-radius: 5px; border: none;")
        btn.clicked.connect(self.submit_data)
        form.addRow("", btn)
        
        layout.addWidget(container)
        layout.addStretch()

    def submit_data(self):
        try:
            self.c.execute("INSERT INTO OWNER (FirstName, LastName) VALUES (?, ?);", (self.inputs["First Name"].text(), self.inputs["Last Name"].text()))
            owner_id = self.c.lastrowid 
            self.c.execute("INSERT INTO OWNER_PHONENO (OwnerID, PhoneNumber) VALUES (?, ?);", (owner_id, self.inputs["Phone"].text()))
            
            weight = float(self.inputs["Weight (lbs)"].text() or 0)
            self.c.execute("INSERT INTO PET (OwnerID, Name, Weight_lbs) VALUES (?, ?, ?);", (owner_id, self.inputs["Pet Name"].text(), weight))
            pet_id = self.c.lastrowid  
            self.c.execute("INSERT INTO BREED (PetID, BreedType) VALUES (?, ?);", (pet_id, self.inputs["Breed"].text()))
            
            self.c.execute("INSERT INTO PET_TAG (PetID, TagID) VALUES (?, ?);", (pet_id, self.behavior_cb.currentData()))
            self.conn.commit()
            
            QMessageBox.information(self, "Success", f"Registered {self.inputs['Pet Name'].text()} successfully!")
            self.active_lbl.setText(f"Registered Pets<br><b>{self.get_dashboard_count()} Pets</b>")
            for widget in self.inputs.values(): widget.clear()
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Error", f"Registration Failed:\n{e}")

    # --- Registered Pets Screen ---
    def build_pets_page(self, layout):
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<h1 style='color: #333;'>📋 Registered Pet Directory</h1>"))
        
        self.pets_table = QTableWidget()
        self.pets_table.setColumnCount(5)
        self.pets_table.setHorizontalHeaderLabels(["Pet ID", "Name", "Weight (lbs)", "Breed / Species", "Behavior Profile"])
        self.pets_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pets_table.setStyleSheet("background-color: white; gridline-color: #E0E0E0;")
        layout.addWidget(self.pets_table)

    def refresh_pets_table(self):
        try:
            query = """
                SELECT P.PetID, P.Name, P.Weight_lbs, B.BreedType, BT.Behavior
                FROM PET P
                LEFT JOIN BREED B ON P.PetID = B.PetID
                LEFT JOIN PET_TAG PT ON P.PetID = PT.PetID
                LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID = BT.TagID;
            """
            self.c.execute(query)
            rows = self.c.fetchall()
            self.pets_table.setRowCount(0)
            for row_idx, row_data in enumerate(rows):
                self.pets_table.insertRow(row_idx)
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value if value is not None else "N/A"))
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    self.pets_table.setItem(row_idx, col_idx, item)
        except Exception as e:
            print(f"Directory load error: {e}")

    # --- Visitations Screen ---
    def build_visitations_page(self, layout):
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<h1 style='color: #333;'>🚪 Active Room Visitations Manager</h1>"))
        
        split_layout = QHBoxLayout()
        
        # Left Panel: Ongoing Table
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 5px; padding: 10px;")
        lp_lay = QVBoxLayout(left_panel)
        lp_lay.addWidget(QLabel("<h3>Current Live Occupants</h3>"))
        
        self.visit_table = QTableWidget()
        self.visit_table.setColumnCount(5)
        self.visit_table.setHorizontalHeaderLabels(["Visit ID", "Pet", "Room", "Type", "Started At"])
        self.visit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lp_lay.addWidget(self.visit_table)
        
        co_form = QHBoxLayout()
        self.co_notes = QLineEdit()
        self.co_notes.setPlaceholderText("Enter departure notes...")
        self.co_notes.setStyleSheet("padding: 5px; border: 1px solid #CCC; border-radius: 3px;")
        co_btn = QPushButton("Check-Out Selected Row")
        co_btn.setStyleSheet("background-color: #E57373; font-weight: bold; padding: 6px; border-radius: 3px; border: none;")
        co_btn.clicked.connect(self.process_checkout)
        co_form.addWidget(self.co_notes, 3)
        co_form.addWidget(co_btn, 1)
        lp_lay.addLayout(co_form)
        split_layout.addWidget(left_panel, 6)
        
        # Right Panel: Check In Formulation Form
        right_panel = QFrame()
        right_panel.setFixedWidth(340)
        right_panel.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 5px; padding: 15px;")
        rp_lay = QVBoxLayout(right_panel)
        rp_lay.addWidget(QLabel("<h3>New Room Check-In</h3>"))
        
        self.v_form = QFormLayout()
        self.v_pet_id = QLineEdit()
        self.v_room_cb = QComboBox()
        
        # Updated to Dropdown Selector instead of QLineEdit string input
        self.v_type = QComboBox()
        self.v_type.addItems(["Reservation", "Walk-in"])
        
        style = "padding: 5px; border: 1px solid #CCC; border-radius: 3px; background: white;"
        self.v_pet_id.setStyleSheet(style)
        self.v_room_cb.setStyleSheet(style)
        self.v_type.setStyleSheet(style)
        
        self.v_form.addRow("Pet ID Number:", self.v_pet_id)
        self.v_form.addRow("Target Playroom:", self.v_room_cb)
        self.v_form.addRow("Visitation Type:", self.v_type)
        rp_lay.addLayout(self.v_form)
        
        cin_btn = QPushButton("Run Verification & Check-In")
        cin_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; border-radius: 4px; border: none;")
        cin_btn.clicked.connect(self.process_checkin)
        rp_lay.addWidget(cin_btn)
        rp_lay.addStretch()
        
        split_layout.addWidget(right_panel, 4)
        layout.addLayout(split_layout)

    def parse_species(self, breed_string):
        lowered = str(breed_string).lower()
        if "cat" in lowered or "feline" in lowered: return "Cat"
        if "bird" in lowered or "parrot" in lowered: return "Bird"
        return "Dog"

    def refresh_visitations_module(self):
        try:
            v_query = """
                SELECT V.VisitID, P.Name, R.RoomName, V.VisitType, V.StartTime
                FROM VISIT V
                JOIN PET P ON V.PetID = P.PetID
                JOIN PLAYROOM R ON V.RoomID = R.RoomID
                WHERE V.EndTime IS NULL OR V.EndTime = '';
            """
            self.c.execute(v_query)
            visits = self.c.fetchall()
            self.visit_table.setRowCount(0)
            for r_idx, r_dat in enumerate(visits):
                self.visit_table.insertRow(r_idx)
                for c_idx, val in enumerate(r_dat):
                    item = QTableWidgetItem(str(val))
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    self.visit_table.setItem(r_idx, c_idx, item)
            
            self.v_room_cb.clear()
            self.c.execute("SELECT RoomID, RoomName, MaxCapacity FROM PLAYROOM;")
            for r_id, r_name, r_cap in self.c.fetchall():
                self.c.execute("SELECT COUNT(*) FROM VISIT WHERE RoomID = ? AND (EndTime IS NULL OR EndTime = '');", (r_id,))
                current_count = self.c.fetchone()[0]
                self.v_room_cb.addItem(f"{r_name} ({current_count}/{r_cap})", r_id)
        except Exception as e:
            print(f"Visitations reload failure: {e}")

    def process_checkin(self):
        """Implements safe room matrix validation rules securely."""
        try:
            p_id_text = self.v_pet_id.text().strip()
            if not p_id_text: return
            pet_id = int(p_id_text)
            room_id = self.v_room_cb.currentData()
            
            # Grabs selection text directly from the UI dropdown choice configuration
            visit_type = self.v_type.currentText()
            
            if not room_id:
                QMessageBox.warning(self, "Setup Missing", "No playrooms configured in database layout.")
                return

            self.c.execute("""
                SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType 
                FROM PET P
                LEFT JOIN BREED B ON P.PetID = B.PetID
                LEFT JOIN PET_TAG PT ON P.PetID = PT.PetID
                LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID = BT.TagID
                WHERE P.PetID = ?;
            """, (pet_id,))
            pet_profile = self.c.fetchone()
            
            if not pet_profile:
                QMessageBox.warning(self, "Invalid Request", "That Pet ID number doesn't exist.")
                return
                
            pet_name, pet_weight, pet_behavior, breed_type = pet_profile
            pet_species = self.parse_species(breed_type)
            pet_size = "Small" if (pet_weight or 0) < 30 else "Large"
            
            self.c.execute("""
                SELECT P.Name, P.Weight_lbs, BT.Behavior, B.BreedType 
                FROM VISIT V
                JOIN PET P ON V.PetID = P.PetID
                LEFT JOIN BREED B ON P.PetID = B.PetID
                LEFT JOIN PET_TAG PT ON P.PetID = PT.PetID
                LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID = BT.TagID
                WHERE V.RoomID = ? AND (V.EndTime IS NULL OR V.EndTime = '');
            """, (room_id,))
            occupants = self.c.fetchall()
            
            is_safe = True
            reason = ""
            
            for occ_name, occ_weight, occ_behavior, occ_breed in occupants:
                occ_species = self.parse_species(occ_breed)
                occ_size = "Small" if (occ_weight or 0) < 30 else "Large"
                
                if "Requires Solo Room" in [str(pet_behavior), str(occ_behavior)]:
                    is_safe, reason = False, "This room is occupied, and isolation markers prevent co-habitation."
                    break
                if pet_species != occ_species:
                    is_safe, reason = False, f"Species Mismatch! Cannot blend {pet_species} and {occ_species} types."
                    break
                if pet_species == "Dog":
                    if "Aggressive" in str(pet_behavior) and "Calm" in str(occ_behavior):
                        is_safe, reason = False, f"{pet_name} is Aggressive, but {occ_name} is registered Calm."
                        break
                    if "Calm" in str(pet_behavior) and "Aggressive" in str(occ_behavior):
                        is_safe, reason = False, f"The room currently holds {occ_name}, who is flagged Aggressive."
                        break
                    if "Aggressive" in str(pet_behavior) or "Aggressive" in str(occ_behavior):
                        if pet_size != occ_size:
                            is_safe, reason = False, f"Size/Aggression Conflict! Cannot mix {pet_size} and {occ_size} weights."
                            break

            if not is_safe:
                QMessageBox.critical(self, "CHECK-IN DENIED", f"Safety Threshold Violation:\n\n{reason}")
                return
                
            current_date = datetime.now().strftime("%Y-%m-%d")
            start_time = datetime.now().strftime("%H:%M:%S")
            self.c.execute("""
                INSERT INTO VISIT (PetID, RoomID, VisitType, VisitDate, StartTime, EndTime, Notes)
                VALUES (?, ?, ?, ?, ?, NULL, 'Validated clear via systematic safety matrix rules.');
            """, (pet_id, room_id, visit_type, current_date, start_time))
            self.conn.commit()
            
            QMessageBox.information(self, "Check-In Success", f"Safety validation verified. {pet_name} tracked inside safely.")
            self.v_pet_id.clear()
            self.refresh_visitations_module()
            
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Error", f"Operational failure: {e}")

    def process_checkout(self):
        try:
            curr_row = self.visit_table.currentRow()
            if curr_row < 0:
                QMessageBox.warning(self, "Selection Missing", "Please select a row inside the Live Occupants matrix first.")
                return
                
            v_id = int(self.visit_table.item(curr_row, 0).text())
            notes = self.co_notes.text().strip() or "Standard check-out completed."
            current_time = datetime.now().strftime("%H:%M:%S")
            
            self.c.execute("UPDATE VISIT SET EndTime = ?, Notes = ? WHERE VisitID = ?;", (current_time, notes, v_id))
            self.conn.commit()
            
            QMessageBox.information(self, "Checked Out", f"Visit ID {v_id} successfully closed.")
            self.co_notes.clear()
            self.refresh_visitations_module()
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Error", f"Check-out execution failed:\n{e}")

    def closeEvent(self, event):
        self.conn.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ResPAWnsibleApp()
    window.show()
    sys.exit(app.exec_())