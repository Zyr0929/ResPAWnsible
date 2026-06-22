from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, 
                             QLineEdit, QPushButton, QMessageBox, QLabel, QFrame, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox)
from PyQt5.QtCore import Qt

def build_page(app, layout):
    layout.setContentsMargins(30, 30, 30, 30)
    
    title = QLabel("🏢 Facility Manager")
    title.setObjectName("Header1")
    layout.addWidget(title)
    
    sub = QLabel("Configure playrooms, capacities, and specialized safety zones.")
    sub.setStyleSheet("color: #757575; margin-top: 0px; margin-bottom: 20px;")
    layout.addWidget(sub)
    
    split = QHBoxLayout()
    split.setSpacing(20)

    left = QFrame()
    left.setObjectName("MainCard")
    lp = QVBoxLayout(left)
    lp.setContentsMargins(20, 20, 20, 20)
    
    app.room_table = QTableWidget()
    app.room_table.setColumnCount(3)
    app.room_table.setHorizontalHeaderLabels(["Room ID", "Room Name", "Max Capacity"])
    
    header = app.room_table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Stretch)
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
    header.setDefaultAlignment(Qt.AlignCenter)
    
    app.room_table.verticalHeader().setVisible(False) 
    app.room_table.setFocusPolicy(Qt.NoFocus)   
    app.room_table.setShowGrid(False)           
    app.room_table.setAlternatingRowColors(True)
    app.room_table.verticalHeader().setDefaultSectionSize(50)
    app.room_table.setSelectionBehavior(QTableWidget.SelectRows)
    app.room_table.setStyleSheet("""
        QTableWidget { background-color: white; alternate-background-color: #FAFAFA; border: 1px solid #E5E0D8; border-radius: 6px; outline: none; }
        QTableWidget::item { border-bottom: 1px solid #F0EDE5; padding-left: 10px; }
        QTableWidget::item:selected { background-color: #FFF8E1; color: #3A271E; }
    """)
    app.room_table.horizontalHeader().setStyleSheet("""
        QHeaderView::section { background-color: #F0EDE5; color: #3A271E; font-weight: bold; padding: 10px; border: none; border-bottom: 2px solid #D6D0C4; }
    """)
    
    app.room_table.clicked.connect(lambda *args: load_room(app))
    lp.addWidget(app.room_table)
    split.addWidget(left, 6)

    right = QFrame()
    right.setObjectName("MainCard")
    right.setMinimumWidth(360)
    rp = QVBoxLayout(right)
    rp.setContentsMargins(30, 30, 30, 30)
    
    rp_header = QLabel("Edit Room Details")
    rp_header.setObjectName("SubHeader")
    rp.addWidget(rp_header)
    
    info = QLabel("<i>Note: To enforce safety rules, include keywords like 'Aggressive', 'Fearful', 'Calm', or 'Solo' in the room name.</i>")
    info.setWordWrap(True)
    info.setStyleSheet("color: #8C7B70; margin-bottom: 20px; margin-top: 10px; font-size: 12px;")
    rp.addWidget(info)
    
    app.rm_form = QFormLayout()
    app.rm_form.setSpacing(18)
    
    app.r_id = QLineEdit()
    app.r_id.setReadOnly(True)
    app.r_id.setPlaceholderText("Select a room to edit")
    app.r_id.setStyleSheet("padding: 10px; border: 1px dashed #D6D0C4; background-color: #FAFAFA; color: #999; border-radius: 6px;")
    
    app.r_name = QLineEdit()
    
    app.r_cap = QSpinBox()
    app.r_cap.setRange(1, 100)
    app.r_cap.setStyleSheet("""
        QSpinBox { padding: 8px 10px; border: 1px solid #D6D0C4; border-radius: 6px; background-color: white; }
        QSpinBox::up-button, QSpinBox::down-button { width: 24px; background-color: #F0EDE5; border-left: 1px solid #D6D0C4; }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #E5E0D8; }
    """)
    
    app.rm_form.addRow("Room ID:", app.r_id)
    app.rm_form.addRow("Room Name:", app.r_name)
    app.rm_form.addRow("Capacity:", app.r_cap)
    rp.addLayout(app.rm_form)
    
    rp.addSpacing(20)
    
    btn_lay = QHBoxLayout()
    btn_lay.setSpacing(10)
    
    clear_btn = QPushButton("➕ New Room")
    clear_btn.setStyleSheet("""
        QPushButton { background-color: #F0EDE5; color: #3A271E; font-weight: bold; padding: 12px; border-radius: 6px; border: none; }
        QPushButton:hover { background-color: #E5E0D8; }
    """)
    clear_btn.clicked.connect(lambda *args: create_new_room_instantly(app))
    
    save_btn = QPushButton("💾 Update Room")
    save_btn.setObjectName("PrimaryBtn")
    save_btn.clicked.connect(lambda *args: save_room(app))
    
    btn_lay.addWidget(clear_btn, 1)
    btn_lay.addWidget(save_btn, 2)
    
    rp.addLayout(btn_lay)
    rp.addStretch()
    
    split.addWidget(right, 4)

    layout.addLayout(split)

def refresh(app):
    try:
        app.c.execute("SELECT RoomID, RoomName, MaxCapacity FROM PLAYROOM;")
        rows = app.c.fetchall()
        
        app.room_table.setRowCount(0)
        app.room_table.setRowCount(len(rows))
        
        for i, r in enumerate(rows):
            for j, val in enumerate(r):
                item = QTableWidgetItem(str(val if val is not None else ""))
                item.setForeground(Qt.black)
                item.setTextAlignment(Qt.AlignCenter)
                app.room_table.setItem(i, j, item)
                
    except Exception as e:
        print(f"Error loading rooms: {e}")

def load_room(app):
    r = app.room_table.currentRow()
    if r < 0: return
    try:
        app.r_id.setText(app.room_table.item(r, 0).text())
        app.r_name.setText(app.room_table.item(r, 1).text())
        app.r_cap.setValue(int(app.room_table.item(r, 2).text()))
    except Exception as e:
        print(f"Selection error: {e}")

def create_new_room_instantly(app):
    try:
        print("DEBUG: Generating instant room...")
        app.c.execute("SELECT MAX(RoomID) FROM PLAYROOM;")
        max_id = app.c.fetchone()[0]
        next_id = 1 if max_id is None else max_id + 1
        
        current_name = app.r_name.text().strip()
        current_cap = app.r_cap.value()
        
        if current_name:
            room_name = current_name
            room_cap = current_cap
            print(f"DEBUG: Using pre-typed data: '{room_name}' with capacity {room_cap}")
        else:
            room_name = f"New Room {next_id}"
            room_cap = 1
            print(f"DEBUG: No data typed. Using default: '{room_name}'")

        app.c.execute("INSERT INTO PLAYROOM (RoomID, RoomName, MaxCapacity) VALUES (?, ?, ?);", 
                      (next_id, room_name, room_cap))
        app.conn.commit()
        
        refresh(app)
        
        for row in range(app.room_table.rowCount()):
            if app.room_table.item(row, 0).text() == str(next_id):
                app.room_table.selectRow(row)
                load_room(app)
                break
                
        if not current_name:
            app.r_name.setFocus()
            app.r_name.selectAll()
            
    except Exception as e:
        print(f"DEBUG CREATE ERROR: {e}")
        QMessageBox.critical(app, "Database Error", str(e))

def save_room(app):
    r_id = app.r_id.text()
    r_name = app.r_name.text().strip()
    r_cap = app.r_cap.value()
    
    if not r_id:
        return QMessageBox.warning(app, "Missing Info", "Please select a room from the table to update.")
        
    if not r_name: 
        return QMessageBox.warning(app, "Missing Info", "Room Name cannot be empty.")
        
    try:
        app.c.execute("UPDATE PLAYROOM SET RoomName=?, MaxCapacity=? WHERE RoomID=?;", 
                      (r_name, r_cap, r_id))
        app.conn.commit()
        
        refresh(app)

        for row in range(app.room_table.rowCount()):
            if app.room_table.item(row, 0).text() == r_id:
                app.room_table.selectRow(row)
                break
                
        QMessageBox.information(app, "Success", "Room successfully updated!")
        
    except Exception as e: 
        print(f"DEBUG UPDATE ERROR: {e}")
        QMessageBox.critical(app, "Database Error", str(e))