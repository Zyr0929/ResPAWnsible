from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
from PyQt5.QtCore import Qt

def build_page(app, layout):
    layout.setContentsMargins(30, 30, 30, 30)

    title = QLabel("📋 Pet Directory")
    title.setObjectName("Header1")
    layout.addWidget(title)
    
    sub = QLabel("Search, view, and manage all registered pets.")
    sub.setStyleSheet("color: #757575; margin-top: 0px; margin-bottom: 15px;")
    layout.addWidget(sub)
    
    card = QFrame()
    card.setObjectName("MainCard")
    card_lay = QVBoxLayout(card)
    card_lay.setContentsMargins(25, 25, 25, 25)
    card_lay.setSpacing(15)
    
    search_bar = QLineEdit()
    search_bar.setPlaceholderText("🔍 Search by ID, Name, Owner, Breed, or Behavior...")
    search_bar.textChanged.connect(lambda text: app.filter_table(text, app.pets_table))
    card_lay.addWidget(search_bar)
    
    app.pets_table = QTableWidget()
    app.pets_table.setColumnCount(6)
    app.pets_table.setHorizontalHeaderLabels(["Pet ID", "Pet Name", "Owner", "Weight (kg)", "Breed / Species", "Behavior Profile"])
    header = app.pets_table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(1, QHeaderView.Stretch)
    header.setSectionResizeMode(2, QHeaderView.Stretch)
    header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(5, QHeaderView.Stretch)
    
    app.pets_table.verticalHeader().setVisible(False)
    app.pets_table.setFocusPolicy(Qt.NoFocus)
    app.pets_table.setShowGrid(False)
    app.pets_table.setAlternatingRowColors(True)
    app.pets_table.verticalHeader().setDefaultSectionSize(55)
    app.pets_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
    
    app.pets_table.setStyleSheet("""
        QTableWidget {
            background-color: white; 
            alternate-background-color: #FAFAFA;
            border: 1px solid #E5E0D8;
            border-radius: 6px;
            outline: none;
        }
        QTableWidget::item {
            border-bottom: 1px solid #F0EDE5;
            padding-left: 10px;
        }
        QTableWidget::item:selected {
            background-color: #FFF8E1;
            color: #3A271E;
        }
    """)

    app.pets_table.horizontalHeader().setStyleSheet("""
        QHeaderView::section { 
            background-color: #F0EDE5; 
            color: #3A271E; 
            font-weight: bold; 
            padding: 10px; 
            border: none; 
            border-bottom: 2px solid #D6D0C4;
        }
    """)
    
    app.pets_table.cellClicked.connect(lambda row, col: copy_to_clipboard(app, row, col))
    
    card_lay.addWidget(app.pets_table)
    layout.addWidget(card)

def refresh(app):
    try:
        app.pets_table.setSortingEnabled(False)
        app.c.execute("""SELECT P.PetID, P.Name, IFNULL(O.FirstName, '') || ' ' || IFNULL(O.LastName, ''), 
                                 P.Weight_lbs, B.BreedType, BT.Behavior 
                          FROM PET P
                          LEFT JOIN OWNER O ON P.OwnerID = O.OwnerID
                          LEFT JOIN BREED B ON P.PetID=B.PetID 
                          LEFT JOIN PET_TAG PT ON P.PetID=PT.PetID 
                          LEFT JOIN BEHAVIOR_TAG BT ON PT.TagID=BT.TagID;""")
        rows = app.c.fetchall()
        app.pets_table.setRowCount(0)
        for r_idx, row in enumerate(rows):
            app.pets_table.insertRow(r_idx)
            pet_id = row[0]  
            for c_idx, val in enumerate(row):
                if c_idx == 5 and val:
                    app.pets_table.setCellWidget(r_idx, c_idx, app.create_tag_pill(str(val), pet_id))
                else:
                    item = QTableWidgetItem()
                    if isinstance(val, (int, float)): item.setData(Qt.DisplayRole, val)
                    else: item.setData(Qt.DisplayRole, str(val if val is not None else "N/A"))
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                    app.pets_table.setItem(r_idx, c_idx, item)
        app.pets_table.setSortingEnabled(True)
    except Exception: pass

def copy_to_clipboard(app, row, col):
    text_to_copy = ""
    item = app.pets_table.item(row, col)
    
    if item and item.text():
        text_to_copy = item.text()
    else:
        widget = app.pets_table.cellWidget(row, col)
        if widget:
            label = widget.findChild(QLabel)
            if label:
                text_to_copy = label.text()
                
    if text_to_copy:
        clipboard = QApplication.clipboard()
        clipboard.setText(text_to_copy)
        # Briefly display a success message at the very bottom left corner of the window
        app.statusBar().setStyleSheet("color: #2E7D32; font-weight: bold; background: #E8F5E9;")
        app.statusBar().showMessage(f"📋 Copied '{text_to_copy}' to clipboard", 3000)