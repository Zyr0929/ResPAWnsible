from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, 
                             QLineEdit, QPushButton, QMessageBox, QLabel, QFrame, 
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt

def build_page(app, layout):
    layout.setContentsMargins(30, 30, 30, 30)
    
    title = QLabel("👥 Owner Manager")
    title.setObjectName("Header1")
    layout.addWidget(title)
    
    sub = QLabel("View and update registered owner contact information.")
    sub.setStyleSheet("color: #757575; margin-top: 0px; margin-bottom: 15px;")
    layout.addWidget(sub)
    
    split = QHBoxLayout()

    left = QFrame()
    left.setObjectName("MainCard")
    lp = QVBoxLayout(left)
    lp.setContentsMargins(20, 20, 20, 20)
    
    app.owner_table = QTableWidget()
    app.owner_table.setColumnCount(4)
    app.owner_table.setHorizontalHeaderLabels(["ID", "First Name", "Last Name", "Contact"])
    
    header = app.owner_table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Stretch)
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
    header.setDefaultAlignment(Qt.AlignCenter)
    
    app.owner_table.verticalHeader().setVisible(False) 
    app.owner_table.setFocusPolicy(Qt.NoFocus)   
    app.owner_table.setShowGrid(False)           
    app.owner_table.setAlternatingRowColors(True)
    app.owner_table.verticalHeader().setDefaultSectionSize(50)
    
    app.owner_table.setStyleSheet("""
        QTableWidget { background-color: white; alternate-background-color: #FAFAFA; border: 1px solid #E5E0D8; border-radius: 6px; outline: none; }
        QTableWidget::item { border-bottom: 1px solid #F0EDE5; padding-left: 10px; }
        QTableWidget::item:selected { background-color: #FFF8E1; color: #3A271E; }
    """)
    app.owner_table.horizontalHeader().setStyleSheet("""
        QHeaderView::section { background-color: #F0EDE5; color: #3A271E; font-weight: bold; padding: 10px; border: none; border-bottom: 2px solid #D6D0C4; }
    """)
    
    app.owner_table.clicked.connect(lambda idx: load_owner_to_form(app))
    lp.addWidget(app.owner_table)
    split.addWidget(left, 6)

    right = QFrame()
    right.setObjectName("MainCard")
    right.setMinimumWidth(340)
    rp = QVBoxLayout(right)
    rp.setContentsMargins(25, 25, 25, 25)
    
    rp_header = QLabel("Edit Details")
    rp_header.setObjectName("SubHeader")
    rp.addWidget(rp_header)
    
    app.own_form = QFormLayout()
    app.own_form.setSpacing(15)
    
    app.o_id = QLineEdit(); app.o_id.setReadOnly(True)
    app.o_first = QLineEdit()
    app.o_last = QLineEdit()
    app.o_phone = QLineEdit()
    
    app.own_form.addRow("Owner ID:", app.o_id)
    app.own_form.addRow("First Name:", app.o_first)
    app.own_form.addRow("Last Name:", app.o_last)
    app.own_form.addRow("Phone:", app.o_phone)
    rp.addLayout(app.own_form)
    
    save_btn = QPushButton("💾 Save Changes")
    save_btn.setObjectName("PrimaryBtn")
    save_btn.clicked.connect(lambda: save_owner(app))
    rp.addWidget(save_btn)
    rp.addStretch()
    
    split.addWidget(right, 4)
    layout.addLayout(split)

def refresh(app):
    try:
        query = """
            SELECT O.OwnerID, O.FirstName, O.LastName, GROUP_CONCAT(OP.PhoneNumber, ', ')
            FROM OWNER O
            LEFT JOIN OWNER_PHONENO OP ON O.OwnerID = OP.OwnerID
            GROUP BY O.OwnerID;
        """
        app.c.execute(query)
        rows = app.c.fetchall()
        
        app.owner_table.setRowCount(0)
        app.owner_table.setRowCount(len(rows))
        
        for i, r in enumerate(rows):
            for j, val in enumerate(r):
                item = QTableWidgetItem(str(val if val is not None else ""))
                item.setForeground(Qt.black)
                item.setTextAlignment(Qt.AlignCenter)
                app.owner_table.setItem(i, j, item)
                
    except Exception as e:
        print(f"Error loading owners: {e}")

def load_owner_to_form(app):
    r = app.owner_table.currentRow()
    if r < 0: return
    
    try:
        id_item = app.owner_table.item(r, 0)
        first_item = app.owner_table.item(r, 1)
        last_item = app.owner_table.item(r, 2)
        phone_item = app.owner_table.item(r, 3)
        
        app.o_id.setText(id_item.text() if id_item else "")
        app.o_first.setText(first_item.text() if first_item else "")
        app.o_last.setText(last_item.text() if last_item else "")
        app.o_phone.setText(phone_item.text() if phone_item else "")
    except Exception as e:
        print(f"Selection error: {e}")

def save_owner(app):
    o_id = app.o_id.text()
    if not o_id: 
        return QMessageBox.warning(app, "Missing Selection", "Please select an owner from the table first.")
        
    try:
        app.c.execute("UPDATE OWNER SET FirstName=?, LastName=? WHERE OwnerID=?;", 
                      (app.o_first.text(), app.o_last.text(), o_id))

        app.c.execute("DELETE FROM OWNER_PHONENO WHERE OwnerID=?;", (o_id,))
        
        new_phone = app.o_phone.text().strip()
        if new_phone:
            for phone in new_phone.split(','):
                app.c.execute("INSERT INTO OWNER_PHONENO (OwnerID, PhoneNumber) VALUES (?, ?);", 
                              (o_id, phone.strip()))
        
        app.conn.commit()
        QMessageBox.information(app, "Success", "Owner info successfully updated!")

        app.o_id.clear(); app.o_first.clear(); app.o_last.clear(); app.o_phone.clear()
        refresh(app)
        
    except Exception as e: 
        QMessageBox.critical(app, "Database Error", str(e))