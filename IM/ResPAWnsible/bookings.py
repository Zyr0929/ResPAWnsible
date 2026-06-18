from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, 
                             QLineEdit, QComboBox, QPushButton, QMessageBox, 
                             QLabel, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDateEdit, QDialog, QTimeEdit)
from PyQt5.QtCore import Qt, QDate, QTime

def apply_calendar_style(date_edit):
    calendar = date_edit.calendarWidget()
    calendar.setMinimumSize(325, 275) 
    calendar.setStyleSheet("""
        QCalendarWidget QWidget#qt_calendar_navigationbar { 
            background-color: #3A271E; 
            border: none; 
            padding: 10px; 
        }
        
        QCalendarWidget QToolButton { 
            color: white; 
            font-weight: bold; 
            font-size: 16px; 
            border: none; 
            padding: 5px;
        }
        QCalendarWidget QToolButton:hover { 
            background-color: #5D4037; 
            border-radius: 4px;
        }

        QCalendarWidget QTableView { 
            background-color: white; 
            selection-background-color: #FFC107; 
            selection-color: #3A271E; 
            font-size: 14px; 
            gridline-color: #F0EDE5;
        }

        QCalendarWidget QAbstractItemView:enabled { 
            color: #3A271E;
        }

        QCalendarWidget QAbstractItemView:disabled { 
            color: #D6D0C4; 
        }
    """)   

def build_page(app, layout):
    layout.setContentsMargins(30, 30, 30, 30)
    
    title = QLabel("📅 Advance Reservations Manager")
    title.setObjectName("Header1")
    layout.addWidget(title)
    
    sub = QLabel("Schedule and manage upcoming playroom visits.")
    sub.setStyleSheet("color: #757575; margin-top: 0px; margin-bottom: 15px;")
    layout.addWidget(sub)
    
    split_layout = QHBoxLayout()
    
    left_panel = QFrame()
    left_panel.setObjectName("MainCard")
    lp_lay = QVBoxLayout(left_panel)
    lp_lay.setContentsMargins(20, 20, 20, 20)
    
    lp_header = QLabel("Upcoming Scheduled Slots")
    lp_header.setObjectName("SubHeader")
    lp_lay.addWidget(lp_header)
    
    search_bar = QLineEdit()
    search_bar.setPlaceholderText("🔍 Search reservations...")
    search_bar.textChanged.connect(lambda text: app.filter_table(text, app.bookings_table))
    lp_lay.addWidget(search_bar)
    
    app.bookings_table = QTableWidget()
    app.bookings_table.setColumnCount(6)
    app.bookings_table.setHorizontalHeaderLabels(["Booking ID", "Pet Name", "Owner", "Room Slot", "Visit Date", "Arrival Time"])
    
    header = app.bookings_table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(1, QHeaderView.Stretch)
    header.setSectionResizeMode(2, QHeaderView.Stretch)
    header.setSectionResizeMode(3, QHeaderView.Stretch)
    header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
    header.setDefaultAlignment(Qt.AlignCenter)
    
    app.bookings_table.verticalHeader().setVisible(False)
    app.bookings_table.setFocusPolicy(Qt.NoFocus)
    app.bookings_table.setShowGrid(False)
    app.bookings_table.setAlternatingRowColors(True)
    app.bookings_table.verticalHeader().setDefaultSectionSize(50)
    app.bookings_table.setStyleSheet("""
        QTableWidget { background-color: white; alternate-background-color: #FAFAFA; border: 1px solid #E5E0D8; border-radius: 6px; outline: none; }
        QTableWidget::item { border-bottom: 1px solid #F0EDE5; padding-left: 10px; }
        QTableWidget::item:selected { background-color: #FFF8E1; color: #3A271E; }
    """)
    app.bookings_table.horizontalHeader().setStyleSheet("""
        QHeaderView::section { background-color: #F0EDE5; color: #3A271E; font-weight: bold; padding: 10px; border: none; border-bottom: 2px solid #D6D0C4; }
    """)
    lp_lay.addWidget(app.bookings_table)
    
    action_lay = QHBoxLayout()
    action_lay.addStretch()
    
    cancel_btn = QPushButton("❌ Cancel Booking")
    cancel_btn.setStyleSheet("background-color: #FFEBEE; color: #C62828; font-weight: bold; padding: 10px 20px; border-radius: 6px; border: 1px solid #EF9A9A;")
    cancel_btn.setCursor(Qt.PointingHandCursor if hasattr(Qt, 'PointingHandCursor') else 13)
    cancel_btn.clicked.connect(lambda: cancel_booking(app))
    action_lay.addWidget(cancel_btn)
    
    insta_btn = QPushButton("⚡ Check-In Selected")
    insta_btn.setStyleSheet("background-color: #E8F5E9; color: #2E7D32; font-weight: bold; padding: 10px 20px; border-radius: 6px; border: 1px solid #A5D6A7;")
    insta_btn.setCursor(Qt.PointingHandCursor if hasattr(Qt, 'PointingHandCursor') else 13)
    insta_btn.clicked.connect(lambda: insta_checkin_booking(app))
    action_lay.addWidget(insta_btn)
    
    lp_lay.addLayout(action_lay)
    split_layout.addWidget(left_panel, 6)
    
    right_panel = QFrame()
    right_panel.setObjectName("MainCard")
    right_panel.setMinimumWidth(380) 
    right_panel.setMaximumWidth(450)
    
    rp_lay = QVBoxLayout(right_panel)
    rp_lay.setContentsMargins(25, 25, 25, 25)
    
    rp_header = QLabel("Encode Reservation")
    rp_header.setObjectName("SubHeader")
    rp_lay.addWidget(rp_header)
    rp_lay.addSpacing(10)
    
    form = QFormLayout()
    form.setSpacing(15)
    
    app.bk_pet_id = QLineEdit()
    app.bk_room_cb = QComboBox()
    app.make_searchable(app.bk_room_cb, allow_new=False, locked=True)
    
    app.bk_start = QDateEdit()
    app.bk_start.setCalendarPopup(True) 
    app.bk_start.setDate(QDate.currentDate())
    app.bk_start.setMinimumDate(QDate.currentDate())
    apply_calendar_style(app.bk_start)
    app.bk_start.setFocusPolicy(Qt.NoFocus)
    
    app.bk_hour_cb, app.bk_min_cb, app.bk_period_cb = QComboBox(), QComboBox(), QComboBox()
    app.bk_hour_cb.addItems([f"{i:02d}" for i in range(1, 13)])
    app.bk_min_cb.addItems([f"{i:02d}" for i in range(0, 60, 5)])
    app.bk_period_cb.addItems(["AM", "PM"])
    
    for cb in (app.bk_hour_cb, app.bk_min_cb, app.bk_period_cb): 
        app.make_searchable(cb, allow_new=False, locked=True)
        
    time_widget = QWidget()
    time_layout = QHBoxLayout(time_widget)
    time_layout.setContentsMargins(0, 0, 0, 0)
    time_layout.setSpacing(8)
    time_layout.addWidget(app.bk_hour_cb)
    time_layout.addWidget(QLabel("<b>:</b>"))
    time_layout.addWidget(app.bk_min_cb)
    time_layout.addWidget(app.bk_period_cb)
    
    form.addRow("Pet ID:", app.bk_pet_id)
    form.addRow("Playroom:", app.bk_room_cb)
    form.addRow("Date:", app.bk_start)
    form.addRow("Time:", time_widget)
    rp_lay.addLayout(form)
    
    rp_lay.addSpacing(20)
    book_btn = QPushButton("Validate & Lock Spot")
    book_btn.setObjectName("PrimaryBtn")
    book_btn.setCursor(Qt.PointingHandCursor if hasattr(Qt, 'PointingHandCursor') else 13)
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
                item.setTextAlignment(Qt.AlignCenter)
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
        dialog.setStyleSheet("background: white; font-family: 'Segoe UI', Arial;")
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

            visit_id = app.generate_unique_visit_id()
            
            app.c.execute("INSERT INTO VISIT (VisitID, PetID, RoomID, VisitType, VisitDate, StartTime, Notes) VALUES (?, ?, ?, ?, ?, ?, 'Insta Check-in.');", 
                           (visit_id, pet_id, room_id, 'Reservation', today, actual_time))
            app.c.execute("UPDATE BOOKING SET Status='Checked-In' WHERE BookingID=?;", (b_id,))
            app.conn.commit()
            QMessageBox.information(app, "Success", f"{msg} successfully checked in!\n\nVisit Tracking ID: {visit_id}")
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
            
        booking_id = app.generate_unique_booking_id()
        
        app.c.execute("INSERT INTO BOOKING (BookingID, PetID, RoomID, StartDate, StartTime, Status) VALUES (?, ?, ?, ?, ?, 'Confirmed');", 
                      (booking_id, pet_id, room_id, visit_date, arrival_time))
        app.conn.commit()
        QMessageBox.information(app, "Spot Reserved", f"🎉 Advance reservation confirmed for {pet_name} in {room_name}!\n\nBooking Tracking ID: {booking_id}")
        app.bk_pet_id.clear()
        refresh(app)
        
    except ValueError: QMessageBox.warning(app, "Input Error", "Pet ID must be an integer.")
    except Exception as e: app.conn.rollback(); QMessageBox.critical(app, "Database Error", str(e))