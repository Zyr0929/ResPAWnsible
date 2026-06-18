from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QComboBox)
from PyQt5.QtCore import Qt

def build_page(app, layout):
    layout.setContentsMargins(30, 30, 30, 30)
    
    title = QLabel("🕰️ Visitation History")
    title.setObjectName("Header1")
    layout.addWidget(title)
    
    sub = QLabel("Review past pet visits and activity logs.")
    sub.setStyleSheet("color: #757575; margin-top: 0px; margin-bottom: 15px;")
    layout.addWidget(sub)
    
    card = QFrame()
    card.setObjectName("MainCard")
    card_lay = QVBoxLayout(card)
    card_lay.setContentsMargins(25, 25, 25, 25)
    
    controls_layout = QHBoxLayout()
    
    app.history_filter_cb = QComboBox()
    app.history_filter_cb.addItems(["All Time", "Today", "Last 7 Days", "Last 30 Days"])
    app.history_filter_cb.setStyleSheet("padding: 8px; border: 1px solid #D6D0C4; border-radius: 6px;")
    app.history_filter_cb.currentTextChanged.connect(lambda: refresh(app))
    controls_layout.addWidget(app.history_filter_cb)
    
    search_bar = QLineEdit()
    search_bar.setPlaceholderText("🔍 Search history...")
    search_bar.textChanged.connect(lambda text: app.filter_table(text, app.history_table))
    controls_layout.addWidget(search_bar, 3)
    
    card_lay.addLayout(controls_layout)
    
    app.history_table = QTableWidget()
    app.history_table.setColumnCount(9)
    app.history_table.setHorizontalHeaderLabels(["ID", "Date", "Pet Name", "Owner", "Room", "Type", "Check-In", "Check-Out", "Notes"])

    header = app.history_table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Stretch)
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
    header.setDefaultAlignment(Qt.AlignCenter)
    
    app.history_table.verticalHeader().setVisible(False)
    app.history_table.setFocusPolicy(Qt.NoFocus)
    app.history_table.setShowGrid(False)
    app.history_table.setAlternatingRowColors(True)
    app.history_table.verticalHeader().setDefaultSectionSize(50)
    app.history_table.setStyleSheet("""
        QTableWidget { background-color: white; alternate-background-color: #FAFAFA; border: 1px solid #E5E0D8; border-radius: 6px; outline: none; }
        QTableWidget::item { border-bottom: 1px solid #F0EDE5; padding-left: 10px; }
        QTableWidget::item:selected { background-color: #FFF8E1; color: #3A271E; }
    """)
    app.history_table.horizontalHeader().setStyleSheet("""
        QHeaderView::section { background-color: #F0EDE5; color: #3A271E; font-weight: bold; padding: 10px; border: none; border-bottom: 2px solid #D6D0C4; }
    """)
    
    card_lay.addWidget(app.history_table)
    layout.addWidget(card)

def refresh(app):
    try:
        app.history_table.setSortingEnabled(False)
        timeframe = app.history_filter_cb.currentText()
        date_condition = ""
        if timeframe == "Today": date_condition = "WHERE V.VisitDate = date('now', 'localtime')"
        elif timeframe == "Last 7 Days": date_condition = "WHERE V.VisitDate >= date('now', '-7 days', 'localtime')"
        elif timeframe == "Last 30 Days": date_condition = "WHERE V.VisitDate >= date('now', '-30 days', 'localtime')"
            
        app.c.execute(f"""SELECT V.VisitID, V.VisitDate, P.Name, IFNULL(O.FirstName, '') || ' ' || IFNULL(O.LastName, ''),
                                 R.RoomName, V.VisitType, V.StartTime, IFNULL(V.EndTime, 'Active'), IFNULL(V.Notes, '')
                          FROM VISIT V
                          JOIN PET P ON V.PetID = P.PetID
                          LEFT JOIN OWNER O ON P.OwnerID = O.OwnerID
                          JOIN PLAYROOM R ON V.RoomID = R.RoomID
                          {date_condition} ORDER BY V.VisitDate DESC, V.VisitID DESC;""")
        rows = app.c.fetchall()
        app.history_table.setRowCount(0)
        for r_idx, row in enumerate(rows):
            app.history_table.insertRow(r_idx)
            for c_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val if val is not None else "N/A"))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignCenter)
                app.history_table.setItem(r_idx, c_idx, item)
        app.history_table.setSortingEnabled(True)
    except Exception as e: print(f"History load error: {e}")