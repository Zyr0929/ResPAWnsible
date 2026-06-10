import sys, os, sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
                             QPushButton, QMessageBox, QLabel, QFrame, QStackedWidget)
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'ResPAWNsible(Real).db')
<<<<<<< HEAD
conn = sqlite3.connect(db_path)

c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON;")

def get_or_create_behavior_tags():
    """Silently ensures default tags exist and returns them without terminal warnings."""
    # Added ORDER BY to keep the terminal menu perfectly sorted numerically
    c.execute("SELECT TagID, Behavior FROM BEHAVIOR_TAG ORDER BY TagID ASC;")
    tags = c.fetchall()
    
    if not tags:
        defaults = [
            ("Calm / Friendly",), 
            ("Nervous / Fearful",), 
            ("Hyperactive / Playful",), 
            ("Aggressive / Territorial",),
            ("Requires Solo Room",)
        ]
        c.executemany("INSERT INTO BEHAVIOR_TAG (Behavior) VALUES (?);", defaults)
        conn.commit()
        c.execute("SELECT TagID, Behavior FROM BEHAVIOR_TAG ORDER BY TagID ASC;")
        tags = c.fetchall()
    return tags

print("PET REGISTRATION")

try:
    print("Owner Information")
    first_name = input("Enter Owner First Name: ").strip()
    last_name = input("Enter Owner Last Name: ").strip()
    phone_number = input("Enter Owner Phone Number: ").strip()
    
    c.execute("INSERT INTO OWNER (FirstName, LastName) VALUES (?, ?);", (first_name, last_name))
    owner_id = c.lastrowid 
    c.execute("INSERT INTO OWNER_PHONENO (OwnerID, PhoneNumber) VALUES (?, ?);", (owner_id, phone_number))
    
    print("\nPet Information")
    pet_name = input("Enter Pet Name: ").strip()
    weight = float(input("Enter Pet Weight (lbs): "))
    
    # breed
    breed_type = input("Enter Species & Breed (e.g., Dog - Golden Retriever, Cat - Siamese): ").strip()
    
    c.execute("INSERT INTO PET (OwnerID, Name, Weight_lbs) VALUES (?, ?, ?);", (owner_id, pet_name, weight))
    pet_id = c.lastrowid  
    c.execute("INSERT INTO BREED (PetID, BreedType) VALUES (?, ?);", (pet_id, breed_type))
    
    print("\nAssign Behavior Tag")
    available_tags = get_or_create_behavior_tags()
    
    valid_ids = []
    for tag_id, behavior_name in available_tags:
        print(f" [{tag_id}] {behavior_name}")
        valid_ids.append(tag_id)
=======

class ResPAWnsibleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ResPAWnsible - Safety-First Boarding")
        self.resize(1000, 600)
        self.setStyleSheet("background-color: #FDFBF7; font-family: Arial;")
>>>>>>> 5174ff63bf68c6bb4cbcf7d5fc88a17e79f080cb
        
        self.init_db()
        self.init_ui()

    def init_db(self):
        """Initializes DB connection and ensures default tags exist."""
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

    def get_dashboard_data(self):
        """Fetches total pets for the sidebar/dashboard."""
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

        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background-color: #3A271E; color: white;")
        side_layout = QVBoxLayout(sidebar)
        side_layout.addWidget(QLabel("<h2>ResPAWnsible</h2><p>Safety-First Boarding</p>"))

        self.nav_btns = []
        nav_items = ["Dashboard", "Live Playrooms", "Register Pet", "Bookings", "Safety Reports"]
        self.stack = QStackedWidget()
        
        for i, nav in enumerate(nav_items):
            btn = QPushButton(f"   {nav}")
            btn.setCursor(Qt.PointingHandCursor if hasattr(Qt, 'PointingHandCursor') else 13)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            side_layout.addWidget(btn)
            self.nav_btns.append(btn)
            
            # Setup Pages
            page = QWidget()
            p_layout = QVBoxLayout(page)
            if i == 0: self.build_dashboard_page(p_layout)
            elif i == 2: self.build_registration_page(p_layout)
            else: p_layout.addWidget(QLabel(f"<h1 style='color: #333;'>{nav} Page (Under Construction)</h1>"))
            self.stack.addWidget(page)
            
        side_layout.addStretch()
        self.active_lbl = QLabel(f"Registered Pets<br><b>{self.get_dashboard_data()} Pets</b>")
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

    def build_dashboard_page(self, layout):
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(QLabel("<h1 style='color: #333;'>Dashboard</h1>"))

        # Top Stats
        stats_layout = QHBoxLayout()
        for title, val in [("Total Registered Pets", self.get_dashboard_data()), ("Active Bookings", "0"), ("Safety Alerts", "0"), ("Room Utilization", "0%")]:
            card = QFrame()
            card.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 5px; padding: 10px;")
            c_layout = QVBoxLayout(card)
            c_layout.addWidget(QLabel(f"<span style='color: #666; font-size: 12px;'>{title}</span>"))
            c_layout.addWidget(QLabel(f"<span style='font-size: 26px; font-weight: bold; color: #333;'>{val}</span>"))
            stats_layout.addWidget(card)
        layout.addLayout(stats_layout)

        bottom_layout = QHBoxLayout()
        
        alerts = QFrame()
        alerts.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 5px; padding: 10px;")
        a_layout = QVBoxLayout(alerts)
        a_layout.addWidget(QLabel("<h3 style='color: #333;'>Recent Safety Alerts</h3>"))
        for title, desc in [("Database Notice", "Booking tables need to be created.<br><span style='color:#999; font-size: 10px;'>Just now</span>")]:
            box = QLabel(f"⚠️ <b>{title}</b><br><span style='color:#666; font-size: 11px;'>{desc}</span>")
            box.setStyleSheet("background-color: #FFFDF0; border: 1px solid #F4E8B0; padding: 8px; border-radius: 3px;")
            a_layout.addWidget(box)
        a_layout.addStretch()
        bottom_layout.addWidget(alerts)

        checkins = QFrame()
        checkins.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 5px; padding: 10px;")
        ch_layout = QVBoxLayout(checkins)
        ch_layout.addWidget(QLabel("<h3 style='color: #333;'>Upcoming Check-ins</h3>"))
        row = QLabel("<span>(No Booking Table Yet)</span>")
        row.setStyleSheet("background-color: #F5F5F5; padding: 10px; border-radius: 3px;")
        ch_layout.addWidget(row)
        ch_layout.addStretch()
        bottom_layout.addWidget(checkins)

        layout.addLayout(bottom_layout)

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
        btn.setStyleSheet("background-color: #FFC107; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn.clicked.connect(self.submit_data)
        form.addRow("", btn)
        
        layout.addWidget(container)
        layout.addStretch()

    def submit_data(self):
        try:
            self.c.execute("INSERT INTO OWNER (FirstName, LastName) VALUES (?, ?);", 
                           (self.inputs["First Name"].text(), self.inputs["Last Name"].text()))
            owner_id = self.c.lastrowid 
            self.c.execute("INSERT INTO OWNER_PHONENO (OwnerID, PhoneNumber) VALUES (?, ?);", 
                           (owner_id, self.inputs["Phone"].text()))
            
            weight = float(self.inputs["Weight (lbs)"].text() or 0)
            self.c.execute("INSERT INTO PET (OwnerID, Name, Weight_lbs) VALUES (?, ?, ?);", 
                           (owner_id, self.inputs["Pet Name"].text(), weight))
            pet_id = self.c.lastrowid  
            self.c.execute("INSERT INTO BREED (PetID, BreedType) VALUES (?, ?);", 
                           (pet_id, self.inputs["Breed"].text()))
            
            self.c.execute("INSERT INTO PET_TAG (PetID, TagID) VALUES (?, ?);", 
                           (pet_id, self.behavior_cb.currentData()))
            
            self.conn.commit()
            QMessageBox.information(self, "Success", f"Registered {self.inputs['Pet Name'].text()} successfully!")
            
            self.active_lbl.setText(f"Registered Pets<br><b>{self.get_dashboard_data()} Pets</b>")
            for widget in self.inputs.values(): widget.clear()
            
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Error", f"Database Error:\n{e}")

    def closeEvent(self, event):
        self.conn.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ResPAWnsibleApp()
    window.show()
    sys.exit(app.exec_())