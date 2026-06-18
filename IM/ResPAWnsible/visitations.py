from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, 
                             QLineEdit, QComboBox, QPushButton, QMessageBox, 
                             QLabel, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView)
from PyQt5.QtCore import Qt

TABLE_HEADER_STYLE = "QHeaderView::section { background-color: #4A352B; color: white; font-weight: bold; padding: 5px; border: none; }"

def build_page(app, layout):
    layout.setContentsMargins(25, 25, 25, 25)
    layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 5px;'>🚪 Active Room Visitations Manager</h1>"))
    
    search_bar = QLineEdit()
    search_bar.setPlaceholderText("🔍 Search active visitations...")
    search_bar.setStyleSheet("padding: 10px; border: 1px solid #CCC; border-radius: 6px; margin-bottom: 10px; font-size: 13px;")
    search_bar.textChanged.connect(lambda text: app.filter_table(text, app.visit_table))
    layout.addWidget(search_bar)
    
    split = QHBoxLayout()
    left = QFrame()
    left.setStyleSheet("background: white; padding: 15px; border-radius: 8px; border: 1px solid #EAEAEA;")
    lp = QVBoxLayout(left)
    app.visit_table = QTableWidget()
    app.visit_table.setColumnCount(7)
    app.visit_table.setHorizontalHeaderLabels(["ID", "Pet Name", "Owner", "Behavior Profile", "Room", "Type", "Start Time"])
    app.visit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    app.visit_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
    app.visit_table.horizontalHeader().setStyleSheet(TABLE_HEADER_STYLE)
    app.visit_table.verticalHeader().setDefaultSectionSize(50)
    app.visit_table.setAlternatingRowColors(True)
    app.visit_table.setStyleSheet("background-color: white; alternate-background-color: #FAFAFA; gridline-color: #E0E0E0;")
    lp.addWidget(app.visit_table)
    
    co = QHBoxLayout()
    app.co_notes = QLineEdit()
    app.co_notes.setPlaceholderText("Enter departure notes...")
    app.co_notes.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 4px;")
    co_btn = QPushButton("Check-Out")
    co_btn.setStyleSheet("background: #EF5350; color: white; font-weight: bold; padding: 10px 15px; border-radius: 4px;")
    co_btn.clicked.connect(lambda: process_checkout(app))
    co.addWidget(app.co_notes, 3)
    co.addWidget(co_btn, 1)
    lp.addLayout(co)
    split.addWidget(left, 6)
    
    right = QFrame()
    right.setFixedWidth(340)
    right.setStyleSheet("background: white; padding: 20px; border-radius: 8px; border: 1px solid #EAEAEA;")
    rp = QVBoxLayout(right)
    rp.addWidget(QLabel("<h3 style='color: #4A352B;'>Walk-In Check-In</h3>"))
    
    app.v_form = QFormLayout()
    app.v_form.setSpacing(12)
    app.v_pet_id, app.v_room_cb, app.v_type = QLineEdit(), QComboBox(), QComboBox()
    app.v_type.addItems(["Walk-in", "Reservation"])
    
    style = "padding: 8px; border: 1px solid #CCC; border-radius: 4px; background: white;"
    for w in (app.v_pet_id, app.v_room_cb, app.v_type): w.setStyleSheet(style)
    
    app.make_searchable(app.v_room_cb, allow_new=False)
    app.make_searchable(app.v_type, allow_new=False)
    
    app.v_form.addRow("Pet ID:", app.v_pet_id)
    app.v_form.addRow("Playroom:", app.v_room_cb)
    app.v_form.addRow("Type:", app.v_type)
    rp.addLayout(app.v_form)
    
    cin_btn = QPushButton("Verify & Check-In")
    cin_btn.setStyleSheet("background: #4CAF50; color: white; font-weight: bold; padding: 12px; border-radius: 6px; margin-top: 10px;")
    cin_btn.clicked.connect(lambda: process_checkin(app))
    rp.addWidget(cin_btn)
    rp.addStretch()
    split.addWidget(right, 4)
    layout.addLayout(split)

def refresh(app):
    try:
        app.visit_table.setSortingEnabled(False)
        app.c.execute("""SELECT V.VisitID, P.Name, IFNULL(O.FirstName, '') || ' ' || IFNULL(O.LastName, ''), 
                                 BT.Behavior, R.RoomName, V.VisitType, V.StartTime 
                          FROM VISIT V 
                          JOIN PET P ON V.PetID=P.PetID 
                          LEFT JOIN OWNER O ON P.OwnerID = O.OwnerID
                          LEFT JOIN PET_TAG PT ON P.PetID=PT.PetID 
                          LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID=BT.TagID
                          JOIN PLAYROOM R ON V.RoomID=R.RoomID 
                          WHERE V.EndTime IS NULL OR V.EndTime = '';""")
        rows = app.c.fetchall()
        app.visit_table.setRowCount(0)
        for r_idx, row in enumerate(rows):
            app.visit_table.insertRow(r_idx)
            for c_idx, val in enumerate(row):
                if c_idx == 3 and val:
                    app.visit_table.setCellWidget(r_idx, c_idx, app.create_tag_pill(str(val)))
                else:
                    item = QTableWidgetItem()
                    if isinstance(val, (int, float)): item.setData(Qt.DisplayRole, val)
                    else: item.setData(Qt.DisplayRole, str(val if val is not None else "N/A"))
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                    app.visit_table.setItem(r_idx, c_idx, item)
        app.visit_table.setSortingEnabled(True)
        
        app.v_room_cb.clear()
        app.c.execute("SELECT RoomID, RoomName, MaxCapacity FROM PLAYROOM;")
        for r_id, r_name, cap in app.c.fetchall():
            app.c.execute("SELECT COUNT(*) FROM VISIT WHERE RoomID=? AND (EndTime IS NULL OR EndTime = '');", (r_id,))
            app.v_room_cb.addItem(f"{r_name} (Capacity: {app.c.fetchone()[0]}/{cap})", r_id)
    except Exception: pass

def process_checkin(app):
    p_id = app.v_pet_id.text().strip()
    if not p_id: return
    
    r_idx = app.v_room_cb.findText(app.v_room_cb.currentText())
    if r_idx < 0: return QMessageBox.warning(app, "Error", "Invalid Playroom selected.")
    r_id = app.v_room_cb.itemData(r_idx)
    
    try:
        is_safe, msg = app.run_safety_matrix(int(p_id), r_id)
        if not is_safe: return QMessageBox.critical(app, "DENIED", msg)

        app.c.execute("INSERT INTO VISIT (PetID, RoomID, VisitType, VisitDate, StartTime, Notes) VALUES (?, ?, ?, ?, ?, 'Cleared.');", 
                       (int(p_id), r_id, app.v_type.currentText(), datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S")))
        app.conn.commit()
        app.v_pet_id.clear()
        refresh(app)
        QMessageBox.information(app, "Check-In Success", f"Safety verified. {msg} tracked inside safely.")
    except Exception as e: QMessageBox.critical(app, "Error", str(e))

def process_checkout(app):
    r = app.visit_table.currentRow()
    if r < 0: return QMessageBox.warning(app, "Selection Missing", "Select a row to check out.")
    try:
        app.c.execute("UPDATE VISIT SET EndTime=?, Notes=? WHERE VisitID=?;", (datetime.now().strftime("%H:%M:%S"), app.co_notes.text().strip(), int(app.visit_table.item(r, 0).text())))
        app.conn.commit()
        app.co_notes.clear()
        refresh(app)
    except Exception as e: QMessageBox.critical(app, "Error", str(e))