from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, 
                             QLineEdit, QComboBox, QPushButton, QMessageBox, 
                             QLabel, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDateEdit, QDialog, QTimeEdit)
from PyQt5.QtCore import Qt, QDate, QTime

TABLE_HEADER_STYLE = "QHeaderView::section { background-color: #4A352B; color: white; font-weight: bold; padding: 5px; border: none; }"

def build_page(app, layout):
    layout.setContentsMargins(25, 25, 25, 25)
    layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 5px;'>📅 Advance Reservations Manager</h1>"))
    
    split_layout = QHBoxLayout()
    left_panel = QFrame()
    left_panel.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 15px;")
    lp_lay = QVBoxLayout(left_panel)
    lp_lay.addWidget(QLabel("<h3 style='color: #4A352B; margin-bottom: 5px;'>Upcoming Scheduled Slots</h3>"))
    
    search_bar = QLineEdit()
    search_bar.setPlaceholderText("🔍 Search reservations...")
    search_bar.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 4px; margin-bottom: 10px;")
    search_bar.textChanged.connect(lambda text: app.filter_table(text, app.bookings_table))
    lp_lay.addWidget(search_bar)
    
    app.bookings_table = QTableWidget()
    app.bookings_table.setColumnCount(6)
    app.bookings_table.setHorizontalHeaderLabels(["Booking ID", "Pet Name", "Owner", "Room Slot", "Visit Date", "Arrival Time"])
    app.bookings_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    app.bookings_table.horizontalHeader().setStyleSheet(TABLE_HEADER_STYLE)
    app.bookings_table.verticalHeader().setDefaultSectionSize(45)
    app.bookings_table.setAlternatingRowColors(True)
    app.bookings_table.setStyleSheet("background-color: white; alternate-background-color: #FAFAFA; gridline-color: #E0E0E0;")
    lp_lay.addWidget(app.bookings_table)
    
    action_lay = QHBoxLayout()
    action_lay.addStretch()
    
    cancel_btn = QPushButton("❌ Cancel Booking")
    cancel_btn.setStyleSheet("background-color: #EF5350; color: white; font-weight: bold; padding: 10px 15px; border-radius: 4px;")
    cancel_btn.clicked.connect(lambda: cancel_booking(app))
    action_lay.addWidget(cancel_btn)
    
    insta_btn = QPushButton("⚡ Insta Check-In Selected")
    insta_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px 15px; border-radius: 4px;")
    insta_btn.clicked.connect(lambda: insta_checkin_booking(app))
    action_lay.addWidget(insta_btn)
    
    lp_lay.addLayout(action_lay)
    split_layout.addWidget(left_panel, 6)
    
    right_panel = QFrame()
    right_panel.setFixedWidth(340)
    right_panel.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 20px;")
    rp_lay = QVBoxLayout(right_panel)
    rp_lay.addWidget(QLabel("<h3 style='color: #4A352B;'>Encode Phone Reservation</h3>"))
    
    form = QFormLayout()
    form.setSpacing(12)
    app.bk_pet_id, app.bk_room_cb = QLineEdit(), QComboBox()
    
    style = "padding: 8px; border: 1px solid #CCC; border-radius: 4px; background: white;"
    app.bk_start = QDateEdit()
    app.bk_start.setCalendarPopup(True)
    app.bk_start.calendarWidget().setStyleSheet("QCalendarWidget QWidget { color: black; }")
    app.bk_start.setDate(QDate.currentDate())
    app.bk_start.setMinimumDate(QDate.currentDate())
    
    app.bk_hour_cb, app.bk_min_cb, app.bk_period_cb = QComboBox(), QComboBox(), QComboBox()
    app.bk_hour_cb.addItems([f"{i:02d}" for i in range(1, 13)])
    app.bk_min_cb.addItems([f"{i:02d}" for i in range(0, 60, 5)])
    app.bk_period_cb.addItems(["AM", "PM"])
    
    for cb in (app.bk_hour_cb, app.bk_min_cb, app.bk_period_cb): 
        cb.setMinimumWidth(65)
        cb.setStyleSheet(style)
        app.make_searchable(cb, allow_new=False)
        
    app.make_searchable(app.bk_room_cb, allow_new=False)
    
    time_widget = QWidget()
    time_layout = QHBoxLayout(time_widget)
    time_layout.setContentsMargins(0, 0, 0, 0)
    time_layout.addWidget(app.bk_hour_cb); time_layout.addWidget(QLabel("<b>:</b>"))
    time_layout.addWidget(app.bk_min_cb); time_layout.addWidget(app.bk_period_cb)
    
    for w in (app.bk_pet_id, app.bk_room_cb, app.bk_start): w.setStyleSheet(style)
    
    form.addRow("Pet ID:", app.bk_pet_id)
    form.addRow("Playroom:", app.bk_room_cb)
    form.addRow("Date:", app.bk_start)
    form.addRow("Time:", time_widget)
    rp_lay.addLayout(form)
    
    book_btn = QPushButton("Validate & Lock Spot")
    book_btn.setStyleSheet("background-color: #FFC107; font-weight: bold; padding: 12px; border-radius: 6px; margin-top: 10px;")
    book_btn.clicked.connect(lambda: process_booking(app))
    rp_lay.addWidget(book_btn)
    rp_lay.addStretch()
    
    split_layout.addWidget(right_panel, 4)
    layout.addLayout(split_layout)

def refresh(app):
    try:
        app.bookings_table.setSortingEnabled(False)
        app.c.execute("""SELECT B.BookingID, P.Name, IFNULL(O.FirstName, '') || ' ' || IFNULL(O.LastName, ''), 
                                 R.RoomName, B.StartDate, B.StartTime 
                          FROM BOOKING B
                          JOIN PET P ON B.PetID = P.PetID 
                          LEFT JOIN OWNER O ON P.OwnerID = O.OwnerID
                          JOIN PLAYROOM R ON B.RoomID = R.RoomID
                          WHERE B.Status = 'Confirmed' ORDER BY B.StartDate ASC, B.StartTime ASC;""")
        bookings = app.c.fetchall()
        app.bookings_table.setRowCount(0)
        for r_idx, r_dat in enumerate(bookings):
            app.bookings_table.insertRow(r_idx)
            for c_idx, val in enumerate(r_dat):
                item = QTableWidgetItem()
                if isinstance(val, (int, float)): item.setData(Qt.DisplayRole, val)
                else: item.setData(Qt.DisplayRole, str(val if val is not None else "N/A"))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                app.bookings_table.setItem(r_idx, c_idx, item)
        app.bookings_table.setSortingEnabled(True)
        
        app.bk_room_cb.clear()
        app.c.execute("SELECT RoomID, RoomName, MaxCapacity FROM PLAYROOM;")
        for r_id, r_name, r_cap in app.c.fetchall():
            app.bk_room_cb.addItem(f"{r_name} (Max: {r_cap})", r_id)
            
        curr = datetime.now()
        h = curr.hour % 12 or 12
        m = round(curr.minute / 5) * 5
        if m == 60: m = 55
        
        app.bk_hour_cb.setCurrentIndex(app.bk_hour_cb.findText(f"{h:02d}"))
        app.bk_min_cb.setCurrentIndex(app.bk_min_cb.findText(f"{m:02d}"))
        app.bk_period_cb.setCurrentIndex(app.bk_period_cb.findText("PM" if curr.hour >= 12 else "AM"))
        app.bk_start.setDate(QDate.currentDate())
    except Exception: pass

def cancel_booking(app):
    r = app.bookings_table.currentRow()
    if r < 0: return QMessageBox.warning(app, "Selection Missing", "Please select a booking to cancel.")
    b_id = int(app.bookings_table.item(r, 0).text())
    reply = QMessageBox.question(app, "Confirm Cancellation", f"Are you sure you want to cancel Booking ID {b_id}?", QMessageBox.Yes | QMessageBox.No)
    if reply == QMessageBox.Yes:
        try:
            app.c.execute("UPDATE BOOKING SET Status='Cancelled' WHERE BookingID=?;", (b_id,))
            app.conn.commit()
            refresh(app)
        except Exception as e: QMessageBox.critical(app, "Error", str(e))

def insta_checkin_booking(app):
    r = app.bookings_table.currentRow()
    if r < 0: return QMessageBox.warning(app, "Selection Missing", "Please select a booking to check in.")
    b_id = int(app.bookings_table.item(r, 0).text())
    try:
        app.c.execute("SELECT PetID, RoomID, StartDate FROM BOOKING WHERE BookingID=?;", (b_id,))
        res = app.c.fetchone()
        if not res: return
        pet_id, room_id, b_date = res
        
        today = datetime.now().strftime("%Y-%m-%d")
        if b_date != today:
            if QMessageBox.question(app, "Date Mismatch", f"Booking is for {b_date}, not today. Proceed?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.No: return

        is_safe, msg = app.run_safety_matrix(pet_id, room_id, check_occupants=True)
        if not is_safe: return QMessageBox.critical(app, "DENIED", msg)
        
        dialog = QDialog(app)
        dialog.setWindowTitle("Confirm Check-In Time")
        dialog.setFixedSize(320, 160)
        dialog.setStyleSheet("background: white; font-family: Arial;")
        l = QVBoxLayout(dialog)
        l.addWidget(QLabel(f"Validating check-in for <b>{msg}</b>.<br><br>Adjust actual arrival time below:"))
        
        time_edit = QTimeEdit()
        time_edit.setTime(QTime.currentTime())
        time_edit.setDisplayFormat("hh:mm A")
        time_edit.setStyleSheet("padding: 8px; border: 1px solid #CCC; border-radius: 4px;")
        l.addWidget(time_edit)
        
        btn = QPushButton("Complete Check-In")
        btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")
        btn.clicked.connect(dialog.accept)
        l.addWidget(btn)
        
        if dialog.exec_() == QDialog.Accepted:
            actual_time = time_edit.time().toString("hh:mm A")
            app.c.execute("INSERT INTO VISIT (PetID, RoomID, VisitType, VisitDate, StartTime, Notes) VALUES (?, ?, ?, ?, ?, 'Insta Check-in.');", 
                           (pet_id, room_id, 'Reservation', today, actual_time))
            app.c.execute("UPDATE BOOKING SET Status='Checked-In' WHERE BookingID=?;", (b_id,))
            app.conn.commit()
            QMessageBox.information(app, "Success", f"{msg} successfully checked in!")
            refresh(app)
    except Exception as e: QMessageBox.critical(app, "Error", str(e))

def process_booking(app):
    try:
        p_id_text = app.bk_pet_id.text().strip()
        visit_date = app.bk_start.date().toString("yyyy-MM-dd")
        arrival_time = f"{app.bk_hour_cb.currentText()}:{app.bk_min_cb.currentText()} {app.bk_period_cb.currentText()}"
        
        r_idx = app.bk_room_cb.findText(app.bk_room_cb.currentText())
        if r_idx < 0: return QMessageBox.warning(app, "Error", "Invalid Target Playroom selected.")
        room_id = app.bk_room_cb.itemData(r_idx)
        
        if not p_id_text: return QMessageBox.warning(app, "Input Error", "Please provide a Pet ID Number.")
            
        pet_id = int(p_id_text)
        
        app.c.execute("SELECT Name FROM PET WHERE PetID = ?;", (pet_id,))
        pet_data = app.c.fetchone()
        if not pet_data:
            msg_box = QMessageBox(app)
            msg_box.setWindowTitle("Pet Not Found")
            msg_box.setText(f"🛑 Pet ID '{pet_id}' does not exist.")
            if msg_box.exec_() == msg_box.addButton("Register Pet", QMessageBox.YesRole): app.switch_page(2)
            return
        pet_name = pet_data[0]

        is_safe, msg = app.run_safety_matrix(pet_id, room_id, check_occupants=False)
        if not is_safe:
            return QMessageBox.critical(app, "Booking Denied", msg)

        app.c.execute("SELECT StartTime FROM BOOKING WHERE PetID = ? AND StartDate = ? AND Status = 'Confirmed';", (pet_id, visit_date))
        existing_bookings = app.c.fetchall()
        if existing_bookings:
            for (b_time,) in existing_bookings:
                if b_time == arrival_time:
                    return QMessageBox.critical(app, "Double Booking Blocked", f"🛑 {pet_name} is already booked at exactly {arrival_time} on {visit_date}.")
            
            reply = QMessageBox.question(app, "Duplicate Daily Booking", 
                f"⚠️ {pet_name} is already booked on {visit_date} at a different time.\n\nAre you sure you want to book this pet again today?", 
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No: return

        app.c.execute("SELECT RoomName, MaxCapacity FROM PLAYROOM WHERE RoomID = ?;", (room_id,))
        room_name, max_cap = app.c.fetchone()
        
        app.c.execute("SELECT StartTime FROM BOOKING WHERE RoomID = ? AND Status = 'Confirmed' AND StartDate = ?;", (room_id, visit_date))
        room_bookings_today = app.c.fetchall()
        
        arrival_dt = datetime.strptime(arrival_time, "%I:%M %p")
        same_hour_count = 0
        for (b_time,) in room_bookings_today:
            try:
                b_dt = datetime.strptime(b_time, "%I:%M %p")
                if b_dt.hour == arrival_dt.hour:
                    same_hour_count += 1
            except: pass
            
        if same_hour_count >= max_cap:
            return QMessageBox.critical(app, "Playroom Full", f"🛑 Overbooking Blocked!\n'{room_name}' is at capacity ({max_cap}/{max_cap}) for the {arrival_dt.strftime('%I %p')} hour block on {visit_date}.")
            
        app.c.execute("INSERT INTO BOOKING (PetID, RoomID, StartDate, StartTime, Status) VALUES (?, ?, ?, ?, 'Confirmed');", (pet_id, room_id, visit_date, arrival_time))
        app.conn.commit()
        QMessageBox.information(app, "Spot Reserved", f"🎉 Advance reservation confirmed for {pet_name} in {room_name}!")
        app.bk_pet_id.clear()
        refresh(app)
        
    except ValueError: QMessageBox.warning(app, "Input Error", "Pet ID must be an integer.")
    except Exception as e: app.conn.rollback(); QMessageBox.critical(app, "Database Error", str(e))