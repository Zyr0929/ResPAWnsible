from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QPushButton
from PyQt5.QtCore import Qt

def build_page(app, layout):
    layout.setContentsMargins(25, 25, 25, 25)
    layout.addWidget(QLabel("<h1 style='color: #3A271E; margin-bottom: 10px;'>📊 Operations Dashboard</h1>"))
    
    stats_layout = QHBoxLayout()
    app.dash_stats = {}
    for title in ["Total Registered Pets", "Active Visitations", "Safety Alerts", "Room Utilization"]:
        card = QFrame()
        card.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 15px;")
        c_layout = QVBoxLayout(card)
        c_layout.addWidget(QLabel(f"<span style='color: #757575; font-size: 13px; font-weight: bold;'>{title.upper()}</span>"))
        val_lbl = QLabel()
        app.dash_stats[title] = val_lbl 
        c_layout.addWidget(val_lbl)
        stats_layout.addWidget(card)
    layout.addLayout(stats_layout)
    
    bottom_layout = QHBoxLayout()
    app.dash_alerts_layout = QVBoxLayout()
    alerts_frame = QFrame()
    alerts_frame.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 20px;")
    alerts_frame.setLayout(app.dash_alerts_layout)
    bottom_layout.addWidget(alerts_frame, 1)

    app.dash_bookings_layout = QVBoxLayout()
    bookings_frame = QFrame()
    bookings_frame.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 20px;")
    bookings_frame.setLayout(app.dash_bookings_layout)
    bottom_layout.addWidget(bookings_frame, 1)
    
    app.dash_visitations_layout = QVBoxLayout()
    visitations_frame = QFrame()
    visitations_frame.setStyleSheet("background-color: white; border: 1px solid #EAEAEA; border-radius: 8px; padding: 20px;")
    visitations_frame.setLayout(app.dash_visitations_layout)
    bottom_layout.addWidget(visitations_frame, 1)
    
    layout.addLayout(bottom_layout)
    layout.addStretch()

def refresh(app):
    app.dash_stats["Total Registered Pets"].setText(f"<span style='font-size: 32px; font-weight: bold; color: #3A271E;'>{app.get_dashboard_count()}</span>")
    app.dash_stats["Active Visitations"].setText(f"<span style='font-size: 32px; font-weight: bold; color: #3A271E;'>{app.get_active_visits()}</span>")
    app.dash_stats["Room Utilization"].setText(f"<span style='font-size: 32px; font-weight: bold; color: #3A271E;'>{app.get_room_utilization()}</span>")
    
    alerts = app.generate_safety_alerts()
    app.dash_stats["Safety Alerts"].setText(f"<span style='font-size: 32px; font-weight: bold; color: {'#D32F2F' if alerts else '#3A271E'};'>{len(alerts)}</span>")
    
    while app.dash_alerts_layout.count():
        item = app.dash_alerts_layout.takeAt(0)
        if item.widget(): item.widget().setParent(None)
        
    app.dash_alerts_layout.addWidget(QLabel("<h3 style='color: #3A271E; margin-bottom: 10px;'>🛡️ Top Safety Priorities</h3>"))
    if not alerts: 
        app.dash_alerts_layout.addWidget(QLabel("<p style='color: #388E3C; font-weight: bold;'>✅ All playrooms are operating safely.</p>"))
    else:
        for severity, title, msg in alerts[:3]:
            color, border, t_color = ("#FFEBEE", "#EF9A9A", "#C62828") if severity == "CRITICAL" else ("#FFF8E1", "#FFE082", "#F57F17")
            lbl = QLabel(f"<b style='color: {t_color};'>⚠️ {title}</b><br><span style='color: #555;'>{msg}</span>")
            lbl.setStyleSheet(f"background: {color}; border: 1px solid {border}; padding: 10px; border-radius: 6px;")
            app.dash_alerts_layout.addWidget(lbl)
    app.dash_alerts_layout.addStretch()

    while app.dash_bookings_layout.count():
        item = app.dash_bookings_layout.takeAt(0)
        if item.widget(): item.widget().setParent(None)
        
    app.dash_bookings_layout.addWidget(QLabel("<h3 style='color: #3A271E; margin-bottom: 10px;'>📅 Upcoming Reservations</h3>"))
    try:
        app.c.execute("""SELECT P.Name, R.RoomName, B.StartDate, B.StartTime FROM BOOKING B 
                          JOIN PET P ON B.PetID = P.PetID JOIN PLAYROOM R ON B.RoomID = R.RoomID 
                          WHERE B.Status = 'Confirmed' AND B.StartDate >= DATE('now')
                          ORDER BY B.StartDate ASC, B.StartTime ASC LIMIT 4;""")
        upcoming = app.c.fetchall()
        if not upcoming:
            app.dash_bookings_layout.addWidget(QLabel("<p style='color: #757575;'>No upcoming reservations scheduled.</p>"))
        else:
            for pet_name, room_name, s_date, s_time in upcoming:
                lbl = QLabel(f"<b>{pet_name}</b> ➔ {room_name}<br><span style='color: #757575;'>{s_date} | {s_time}</span>")
                lbl.setStyleSheet("background: #F5F5F5; border-radius: 6px; padding: 10px; border: 1px solid #EAEAEA;")
                app.dash_bookings_layout.addWidget(lbl)
    except Exception: pass
    app.dash_bookings_layout.addStretch()

    while app.dash_visitations_layout.count():
        item = app.dash_visitations_layout.takeAt(0)
        if item.widget(): item.widget().setParent(None)
        
    app.dash_visitations_layout.addWidget(QLabel("<h3 style='color: #3A271E; margin-bottom: 10px;'>🚪 Live Room Occupants</h3>"))
    try:
        app.c.execute("""SELECT P.Name, R.RoomName, V.StartTime FROM VISIT V
                          JOIN PET P ON V.PetID = P.PetID JOIN PLAYROOM R ON V.RoomID = R.RoomID
                          WHERE V.EndTime IS NULL OR V.EndTime = '' ORDER BY V.StartTime DESC LIMIT 4;""")
        active_occupants = app.c.fetchall()
        if not active_occupants:
            app.dash_visitations_layout.addWidget(QLabel("<p style='color: #757575;'>No active occupants inside facility.</p>"))
        else:
            for pet_name, room_name, start_time in active_occupants:
                card_widget = QWidget()
                card_lay = QHBoxLayout(card_widget)
                card_lay.setContentsMargins(0, 0, 0, 0)
                
                info_text = QLabel(f"<b>{pet_name}</b> inside {room_name}<br><span style='color: #757575;'>🕒 Checked-In: {start_time}</span>")
                view_btn = QPushButton("📺 Live View")
                view_btn.setCursor(Qt.PointingHandCursor if hasattr(Qt, 'PointingHandCursor') else 13)
                view_btn.setStyleSheet("background-color: #3A271E; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
                view_btn.clicked.connect(lambda checked, rm=room_name: app.zoom_into_room(rm))
                
                card_lay.addWidget(info_text, 1)
                card_lay.addWidget(view_btn)
                
                frame_container = QFrame()
                frame_container.setStyleSheet("background: #F5F5F5; border-radius: 6px; padding: 10px; border: 1px solid #EAEAEA;")
                fc_lay = QVBoxLayout(frame_container)
                fc_lay.setContentsMargins(5, 5, 5, 5)
                fc_lay.addWidget(card_widget)
                app.dash_visitations_layout.addWidget(frame_container)
    except Exception: pass
    app.dash_visitations_layout.addStretch()