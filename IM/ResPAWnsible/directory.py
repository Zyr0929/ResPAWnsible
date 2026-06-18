from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt

TABLE_HEADER_STYLE = "QHeaderView::section { background-color: #4A352B; color: white; font-weight: bold; padding: 5px; border: none; }"

def build_page(app, layout):
    layout.setContentsMargins(25, 25, 25, 25)
    layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 5px;'>📋 Pet Directory</h1>"))
    
    search_bar = QLineEdit()
    search_bar.setPlaceholderText("🔍 Search by ID, Name, Owner, Breed, or Behavior...")
    search_bar.setStyleSheet("padding: 10px; border: 1px solid #CCC; border-radius: 6px; margin-bottom: 10px; font-size: 13px;")
    search_bar.textChanged.connect(lambda text: app.filter_table(text, app.pets_table))
    layout.addWidget(search_bar)
    
    app.pets_table = QTableWidget()
    app.pets_table.setColumnCount(6)
    app.pets_table.setHorizontalHeaderLabels(["Pet ID", "Pet Name", "Owner", "Weight (kg)", "Breed / Species", "Behavior Profile"])
    app.pets_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    app.pets_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
    app.pets_table.horizontalHeader().setStyleSheet(TABLE_HEADER_STYLE)
    app.pets_table.verticalHeader().setDefaultSectionSize(50) 
    app.pets_table.setAlternatingRowColors(True)
    app.pets_table.setStyleSheet("background-color: white; alternate-background-color: #FAFAFA; gridline-color: #E0E0E0; border-radius: 8px;")
    
    # Enable the copy-to-clipboard functionality when a cell is clicked
    app.pets_table.cellClicked.connect(lambda row, col: copy_to_clipboard(app, row, col))
    
    layout.addWidget(app.pets_table)

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
            for c_idx, val in enumerate(row):
                if c_idx == 5 and val:
                    app.pets_table.setCellWidget(r_idx, c_idx, app.create_tag_pill(str(val)))
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
    """Copies the text of the clicked cell to the system clipboard and notifies the user."""
    text_to_copy = ""
    item = app.pets_table.item(row, col)
    
    if item and item.text():
        text_to_copy = item.text()
    else:
        # If the user clicked the custom behavior pill, extract its label text
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