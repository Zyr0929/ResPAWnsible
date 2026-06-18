from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, 
                             QLineEdit, QComboBox, QPushButton, QMessageBox, 
                             QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt

def build_page(app, layout):
    layout.setContentsMargins(30, 30, 30, 30)
    
    title = QLabel("🚪 Active Room Visitations Manager")
    title.setObjectName("Header1")
    layout.addWidget(title)
    
    sub = QLabel("Monitor active pets in playrooms and process departures.")
    sub.setStyleSheet("color: #757575; margin-top: 0px; margin-bottom: 15px;")
    layout.addWidget(sub)
    
    split = QHBoxLayout()
    
    left_panel = QFrame()
    left_panel.setObjectName("MainCard")
    lp_lay = QVBoxLayout(left_panel)
    lp_lay.setContentsMargins(20, 20, 20, 20)
    
    lp_header = QLabel("Active Room Visitations")
    lp_header.setObjectName("SubHeader")
    lp_lay.addWidget(lp_header)
    
    search_bar = QLineEdit()
    search_bar.setPlaceholderText("🔍 Search active visitations...")
    search_bar.textChanged.connect(lambda text: app.filter_table(text, app.visit_table))
    lp_lay.addWidget(search_bar)
    
    app.visit_table = QTableWidget()
    app.visit_table.setColumnCount(7)
    app.visit_table.setHorizontalHeaderLabels(["Visit ID", "Pet Name", "Owner", "Behavior", "Room", "Type", "Start Time"])
    
    header = app.visit_table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(1, QHeaderView.Stretch)
    header.setSectionResizeMode(2, QHeaderView.Stretch)
    header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(4, QHeaderView.Stretch)
    header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
    header.setDefaultAlignment(Qt.AlignCenter)
    
    app.visit_table.verticalHeader().setVisible(False)
    app.visit_table.setFocusPolicy(Qt.NoFocus)
    app.visit_table.setShowGrid(False)
    app.visit_table.setAlternatingRowColors(True)
    app.visit_table.verticalHeader().setDefaultSectionSize(50)
    app.visit_table.setStyleSheet("""
        QTableWidget { background-color: white; alternate-background-color: #FAFAFA; border: 1px solid #E5E0D8; border-radius: 6px; outline: none; }
        QTableWidget::item { border-bottom: 1px solid #F0EDE5; padding-left: 10px; }
        QTableWidget::item:selected { background-color: #FFF8E1; color: #3A271E; }
    """)
    app.visit_table.horizontalHeader().setStyleSheet("""
        QHeaderView::section { background-color: #F0EDE5; color: #3A271E; font-weight: bold; padding: 10px; border: none; border-bottom: 2px solid #D6D0C4; }
    """)
    lp_lay.addWidget(app.visit_table)
    
    co_lay = QHBoxLayout()
    app.co_notes = QLineEdit()
    app.co_notes.setPlaceholderText("Enter departure notes...")
    co_btn = QPushButton("Check-Out")
    co_btn.setStyleSheet("background: #EF5350; color: white; font-weight: bold; padding: 10px 20px; border-radius: 6px;")
    co_btn.clicked.connect(lambda: process_checkout(app))
    co_lay.addWidget(app.co_notes, 3)
    co_lay.addWidget(co_btn, 1)
    lp_lay.addLayout(co_lay)
    
    split.addWidget(left_panel, 6)
    
    right_panel = QFrame()
    right_panel.setObjectName("MainCard")
    right_panel.setMinimumWidth(340)
    rp_lay = QVBoxLayout(right_panel)
    rp_lay.setContentsMargins(25, 25, 25, 25)
    
    rp_header = QLabel("Walk-In Check-In")
    rp_header.setObjectName("SubHeader")
    rp_lay.addWidget(rp_header)
    
    form = QFormLayout()
    form.setSpacing(15)
    app.v_pet_id = QLineEdit()
    app.v_room_cb = QComboBox()
    app.make_searchable(app.v_room_cb, allow_new=False, locked=True)
    
    form.addRow("Pet ID:", app.v_pet_id)
    form.addRow("Playroom:", app.v_room_cb)
    rp_lay.addLayout(form)
    
    cin_btn = QPushButton("Verify & Check-In")
    cin_btn.setObjectName("PrimaryBtn")
    cin_btn.clicked.connect(lambda: process_checkin(app))
    rp_lay.addWidget(cin_btn)
    rp_lay.addStretch()
    
    split.addWidget(right_panel, 4)
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
                    app.visit_table.setCellWidget(r_idx, c_idx, app.create_tag_pill(str(val), 0))
                else:
                    item = QTableWidgetItem(str(val if val is not None else "N/A"))
                    item.setTextAlignment(Qt.AlignCenter)
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
        if not is_safe:
            return QMessageBox.critical(app, "DENIED", msg)

        visit_id = app.generate_unique_visit_id()

        app.c.execute("INSERT INTO VISIT (VisitID, PetID, RoomID, VisitType, VisitDate, StartTime, Notes) VALUES (?, ?, ?, ?, ?, ?, 'Cleared.');", 
                       (visit_id, int(p_id), r_id, 'Walk-in', datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S")))
        app.conn.commit()
        app.v_pet_id.clear()
        refresh(app)
        QMessageBox.information(app, "Check-In Success", f"Safety verified. {msg} tracked inside safely.\n\nVisit Tracking ID: {visit_id}")
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