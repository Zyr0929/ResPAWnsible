from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox)
from PyQt5.QtCore import Qt

TABLE_HEADER_STYLE = "QHeaderView::section { background-color: #4A352B; color: white; font-weight: bold; padding: 5px; border: none; }"

def build_page(app, layout):
    layout.setContentsMargins(25, 25, 25, 25)
    layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 5px;'>🕰️ Visitation History</h1>"))
    
    controls_layout = QHBoxLayout()
    
    app.history_filter_cb = QComboBox()
    app.history_filter_cb.addItems(["All Time", "Today", "Last 7 Days", "Last 30 Days"])
    app.history_filter_cb.setStyleSheet("padding: 10px; border: 1px solid #CCC; border-radius: 6px; font-size: 13px; background: white;")
    app.history_filter_cb.currentTextChanged.connect(lambda: refresh(app))
    controls_layout.addWidget(app.history_filter_cb, 1)
    
    search_bar = QLineEdit()
    search_bar.setPlaceholderText("🔍 Search history by ID, Pet Name, Owner, or Room...")
    search_bar.setStyleSheet("padding: 10px; border: 1px solid #CCC; border-radius: 6px; font-size: 13px; background: white;")
    search_bar.textChanged.connect(lambda text: app.filter_table(text, app.history_table))
    controls_layout.addWidget(search_bar, 3)
    
    layout.addLayout(controls_layout)
    layout.addSpacing(10)
    
    app.history_table = QTableWidget()
    app.history_table.setColumnCount(9)
    app.history_table.setHorizontalHeaderLabels(["ID", "Date", "Pet Name", "Owner", "Room", "Type", "Check-In", "Check-Out", "Notes"])
    app.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    app.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
    app.history_table.horizontalHeader().setStyleSheet(TABLE_HEADER_STYLE)
    
    # THIS HIDES THE ROW NUMBERS ON THE LEFT
    app.history_table.verticalHeader().setVisible(False) 
    
    app.history_table.verticalHeader().setDefaultSectionSize(45)
    app.history_table.setAlternatingRowColors(True)
    app.history_table.setStyleSheet("background-color: white; alternate-background-color: #FAFAFA; gridline-color: #E0E0E0; border-radius: 8px;")
    layout.addWidget(app.history_table)

def refresh(app):
    try:
        app.history_table.setSortingEnabled(False)
        timeframe = app.history_filter_cb.currentText()
        
        date_condition = ""
        if timeframe == "Today":
            date_condition = "WHERE V.VisitDate = date('now', 'localtime')"
        elif timeframe == "Last 7 Days":
            date_condition = "WHERE V.VisitDate >= date('now', '-7 days', 'localtime')"
        elif timeframe == "Last 30 Days":
            date_condition = "WHERE V.VisitDate >= date('now', '-30 days', 'localtime')"
            
        query = f"""SELECT V.VisitID, V.VisitDate, P.Name, IFNULL(O.FirstName, '') || ' ' || IFNULL(O.LastName, ''),
                           R.RoomName, V.VisitType, V.StartTime, IFNULL(V.EndTime, 'Active'), IFNULL(V.Notes, '')
                    FROM VISIT V
                    JOIN PET P ON V.PetID = P.PetID
                    LEFT JOIN OWNER O ON P.OwnerID = O.OwnerID
                    JOIN PLAYROOM R ON V.RoomID = R.RoomID
                    {date_condition}
                    ORDER BY V.VisitDate DESC, V.VisitID DESC;"""
                    
        app.c.execute(query)
        rows = app.c.fetchall()
        app.history_table.setRowCount(0)
        
        for r_idx, row in enumerate(rows):
            app.history_table.insertRow(r_idx)
            for c_idx, val in enumerate(row):
                item = QTableWidgetItem()
                if isinstance(val, (int, float)): 
                    item.setData(Qt.DisplayRole, val)
                else: 
                    item.setData(Qt.DisplayRole, str(val))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                app.history_table.setItem(r_idx, c_idx, item)
                
        app.history_table.setSortingEnabled(True)
    except Exception as e: 
        print(f"History load error: {e}")