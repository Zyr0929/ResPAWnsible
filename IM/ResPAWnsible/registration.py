from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, 
                             QLineEdit, QComboBox, QPushButton, QMessageBox, 
                             QLabel, QFrame, QRadioButton)
from PyQt5.QtCore import Qt

def build_page(app, layout):
    layout.setContentsMargins(25, 25, 25, 25)
    layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 5px;'>🐾 Register New Pet</h1>"))
    layout.addWidget(QLabel("<p style='color: #757575; margin-top: 0px;'>Add a new pet to the facility directory.</p>"))
    
    center_wrapper = QHBoxLayout()
    container = QFrame()
    container.setFixedWidth(650)
    container.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px;")
    
    main_form_lay = QVBoxLayout(container)
    main_form_lay.setContentsMargins(30, 30, 30, 30)
    main_form_lay.setSpacing(20)
    
    style = "padding: 10px; border: 1px solid #CCC; border-radius: 4px; background: #FDFDFD; color: #333;"
    
    app.inputs = {"First Name": QLineEdit(), "Last Name": QLineEdit(), "Phone": QLineEdit(), "Pet Name": QLineEdit(), "Weight (kg)": QLineEdit()}
    for widget in app.inputs.values(): widget.setStyleSheet(style)
    
    app.inputs["Phone"].setInputMask("\\0\\900-000-0000")
    
    app.inputs["First Name"].textEdited.connect(lambda: auto_capitalize_fields(app, app.inputs["First Name"]))
    app.inputs["Last Name"].textEdited.connect(lambda: auto_capitalize_fields(app, app.inputs["Last Name"]))
    app.inputs["First Name"].editingFinished.connect(lambda: check_existing_owner(app))
    app.inputs["Last Name"].editingFinished.connect(lambda: check_existing_owner(app))

    owner_header = QLabel("<h3>👤 Owner Information</h3>")
    owner_header.setStyleSheet("color: #3A271E; border-bottom: 2px solid #FFC107; padding-bottom: 5px;")
    main_form_lay.addWidget(owner_header)
    
    mode_lay = QHBoxLayout()
    app.radio_new_owner = QRadioButton("Register New Owner")
    app.radio_existing_owner = QRadioButton("Select Existing Owner")
    app.radio_new_owner.setChecked(True)
    app.radio_new_owner.setStyleSheet("font-weight: normal; color: #333;")
    app.radio_existing_owner.setStyleSheet("font-weight: normal; color: #333;")
    
    mode_lay.addWidget(app.radio_new_owner)
    mode_lay.addWidget(app.radio_existing_owner)
    mode_lay.addStretch()
    main_form_lay.addLayout(mode_lay)
    
    app.new_owner_widget = QWidget()
    no_lay = QFormLayout(app.new_owner_widget)
    no_lay.setContentsMargins(0, 10, 0, 0)
    no_lay.setSpacing(15)
    no_lay.addRow("First Name:", app.inputs["First Name"])
    no_lay.addRow("Last Name:", app.inputs["Last Name"])
    no_lay.addRow("Mobile Number:", app.inputs["Phone"])
    main_form_lay.addWidget(app.new_owner_widget)
    
    app.existing_owner_widget = QWidget()
    eo_lay = QFormLayout(app.existing_owner_widget)
    eo_lay.setContentsMargins(0, 10, 0, 0)
    app.existing_owner_cb = QComboBox()
    app.existing_owner_cb.setStyleSheet(style)
    app.make_searchable(app.existing_owner_cb, allow_new=False)
    eo_lay.addRow("Select Owner:", app.existing_owner_cb)
    app.existing_owner_widget.hide()
    main_form_lay.addWidget(app.existing_owner_widget)
    
    app.radio_new_owner.toggled.connect(lambda: toggle_owner_mode(app))
    app.radio_existing_owner.toggled.connect(lambda: toggle_owner_mode(app))

    pet_header = QLabel("<br><h3>🐶 Pet Details</h3>")
    pet_header.setStyleSheet("color: #3A271E; border-bottom: 2px solid #FFC107; padding-bottom: 5px;")
    main_form_lay.addWidget(pet_header)
    
    pet_widget = QWidget()
    po_lay = QFormLayout(pet_widget)
    po_lay.setContentsMargins(0, 10, 0, 0)
    po_lay.setSpacing(15)
    po_lay.addRow("Pet Name:", app.inputs["Pet Name"])
    po_lay.addRow("Weight (kg):", app.inputs["Weight (kg)"])
    
    app.species_cb = QComboBox()
    app.species_cb.addItems(["Dog", "Cat", "Bird", "Rabbit", "Reptile", "Other"])
    app.species_cb.setStyleSheet(style)
    app.make_searchable(app.species_cb, allow_new=False)
    po_lay.addRow("Species:", app.species_cb)
    
    app.breed_cb = QComboBox()
    app.breed_cb.setStyleSheet(style)
    app.make_searchable(app.breed_cb, allow_new=True) 
    po_lay.addRow("Breed:", app.breed_cb)

    app.behavior_cb = QComboBox()
    app.behavior_cb.setStyleSheet(style)
    for t_id, t_name in app.tags: app.behavior_cb.addItem(t_name, t_id)
    app.make_searchable(app.behavior_cb, allow_new=False)
    po_lay.addRow("Behavior Profile:", app.behavior_cb)
    main_form_lay.addWidget(pet_widget)
    
    btn_lay = QHBoxLayout()
    btn_lay.addStretch()
    btn = QPushButton("Complete Registration")
    btn.setFixedWidth(220)
    btn.setCursor(Qt.PointingHandCursor if hasattr(Qt, 'PointingHandCursor') else 13)
    btn.setStyleSheet("background-color: #FFC107; color: #3A271E; font-size: 14px; font-weight: bold; padding: 12px; border-radius: 6px; margin-top: 15px;")
    btn.clicked.connect(lambda: submit_data(app))
    btn_lay.addWidget(btn)
    
    main_form_lay.addLayout(btn_lay)
    center_wrapper.addWidget(container)
    center_wrapper.addStretch()
    layout.addLayout(center_wrapper)
    layout.addStretch()

def toggle_owner_mode(app):
    if app.radio_new_owner.isChecked():
        app.new_owner_widget.show()
        app.existing_owner_widget.hide()
    else:
        app.new_owner_widget.hide()
        app.existing_owner_widget.show()
        refresh_existing_owners(app)

def refresh(app):
    refresh_existing_owners(app)
    refresh_breed_dropdown(app)

def refresh_existing_owners(app):
    try:
        app.existing_owner_cb.clear()
        app.c.execute("""SELECT O.OwnerID, O.FirstName, O.LastName, P.PhoneNumber 
                          FROM OWNER O LEFT JOIN OWNER_PHONENO P ON O.OwnerID = P.OwnerID""")
        owners = app.c.fetchall()
        for o_id, fname, lname, phone in owners:
            display_text = f"{fname} {lname} - {phone or 'No Phone'}"
            app.existing_owner_cb.addItem(display_text, o_id)
    except Exception: pass

def auto_capitalize_fields(app, line_edit):
    cursor_pos = line_edit.cursorPosition()
    capitalized = line_edit.text().title()
    if line_edit.text() != capitalized:
        line_edit.setText(capitalized)
        line_edit.setCursorPosition(cursor_pos)

def check_existing_owner(app):
    try:
        app.c.execute("""SELECT P.PhoneNumber FROM OWNER O JOIN OWNER_PHONENO P ON O.OwnerID = P.OwnerID 
                          WHERE O.FirstName = ? AND O.LastName = ? LIMIT 1;""", 
                       (app.inputs["First Name"].text().strip(), app.inputs["Last Name"].text().strip()))
        res = app.c.fetchone()
        if res: app.inputs["Phone"].setText(res[0])
    except Exception: pass

def refresh_breed_dropdown(app):
    try:
        app.breed_cb.clear()
        app.c.execute("SELECT DISTINCT BreedType FROM BREED WHERE BreedType IS NOT NULL;")
        breeds = set()
        for row in app.c.fetchall():
            b_str = row[0]
            if " - " in b_str: breeds.add(b_str.split(" - ", 1)[1])
            else: breeds.add(b_str)
        app.breed_cb.addItems(sorted(list(breeds)))
    except Exception: pass

def submit_data(app):
    try:
        if app.radio_new_owner.isChecked():
            for lbl in ["First Name", "Last Name", "Phone", "Pet Name", "Weight (kg)"]:
                if not app.inputs[lbl].text().replace("-", "").strip():
                    return QMessageBox.warning(app, "Error", f"Missing required field: {lbl}")
            
            phone_raw = app.inputs["Phone"].text().replace("-", "").strip()
            if len(phone_raw) != 11 or not phone_raw.startswith("09"):
                return QMessageBox.warning(app, "Error", "Phone number must be a valid 11-digit number starting with 09.")
            
            fname, lname, phone = app.inputs["First Name"].text().strip(), app.inputs["Last Name"].text().strip(), app.inputs["Phone"].text().strip()
            app.c.execute("SELECT O.OwnerID FROM OWNER O JOIN OWNER_PHONENO P ON O.OwnerID = P.OwnerID WHERE O.FirstName=? AND O.LastName=? AND P.PhoneNumber=?;", (fname, lname, phone))
            res = app.c.fetchone()
            
            if res: owner_id = res[0]
            else:
                app.c.execute("INSERT INTO OWNER (FirstName, LastName) VALUES (?, ?);", (fname, lname))
                owner_id = app.c.lastrowid 
                app.c.execute("INSERT INTO OWNER_PHONENO (OwnerID, PhoneNumber) VALUES (?, ?);", (owner_id, phone))
        else:
            owner_idx = app.existing_owner_cb.findText(app.existing_owner_cb.currentText())
            if owner_idx < 0: return QMessageBox.warning(app, "Error", "Please select a valid existing owner from the list.")
            owner_id = app.existing_owner_cb.itemData(owner_idx)
            
            for lbl in ["Pet Name", "Weight (kg)"]:
                if not app.inputs[lbl].text().strip(): return QMessageBox.warning(app, "Error", f"Missing required field: {lbl}")
        
        species_text = app.species_cb.currentText().strip()
        breed_text = app.breed_cb.currentText().strip()
        if not species_text or not breed_text: return QMessageBox.warning(app, "Error", "Please specify both Species and Breed.")
            
        final_breed_string = f"{species_text} - {breed_text}"
        pet_id = app.generate_unique_pet_id()
        app.c.execute("INSERT INTO PET (PetID, OwnerID, Name, Weight_lbs) VALUES (?, ?, ?, ?);", 
                       (pet_id, owner_id, app.inputs["Pet Name"].text().strip(), float(app.inputs["Weight (kg)"].text() or 0)))
        app.c.execute("INSERT INTO BREED (PetID, BreedType) VALUES (?, ?);", (pet_id, final_breed_string))
        
        behav_idx = app.behavior_cb.findText(app.behavior_cb.currentText())
        if behav_idx < 0: return QMessageBox.warning(app, "Error", "Please select a valid Behavior Profile.")
        tag_id = app.behavior_cb.itemData(behav_idx)
        
        app.c.execute("INSERT INTO PET_TAG (PetID, TagID) VALUES (?, ?);", (pet_id, tag_id))
        app.conn.commit()
        QMessageBox.information(app, "Success", f"Pet registered successfully!\n\nSecure Pet Tracking ID: {pet_id}\n\nPlease save this ID for check-ins.")
        for w in app.inputs.values(): w.clear()
        app.breed_cb.clearEditText()
    except ValueError: QMessageBox.warning(app, "Input Error", "Weight must be a valid number.")
    except Exception as e: app.conn.rollback(); QMessageBox.critical(app, "Database Error", str(e))