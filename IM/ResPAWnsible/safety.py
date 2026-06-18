from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea

def build_page(app, layout):
    layout.setContentsMargins(25, 25, 25, 25)
    layout.addWidget(QLabel("<h1 style='color: #3A271E;'>🛡️ Facility Safety & Audit Reports</h1>"))
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("border: none; background: transparent;")
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    app.safety_layout = QVBoxLayout(container)
    scroll.setWidget(container)
    layout.addWidget(scroll)

def refresh(app):
    while app.safety_layout.count():
        item = app.safety_layout.takeAt(0)
        if item.widget(): item.widget().setParent(None)
        
    alerts = app.generate_safety_alerts()
    if not alerts:
        box = QLabel("<h2>✅ Zero Active Threats</h2><p>System audit cleared. All capacity and behavioral matrices are optimal.</p>")
        box.setStyleSheet("background: #E8F5E9; border: 2px solid #388E3C; color: #2E7D32; padding: 20px; border-radius: 8px;")
        app.safety_layout.addWidget(box)
    else:
        for severity, title, msg in alerts:
            box = QFrame()
            color, border, t_color = ("#FFEBEE", "#EF9A9A", "#C62828") if severity == "CRITICAL" else ("#FFF8E1", "#FFE082", "#F57F17")
            box.setStyleSheet(f"background-color: {color}; border: 1px solid {border}; border-left: 6px solid {border}; border-radius: 6px; padding: 15px;")
            b_lay = QVBoxLayout(box)
            b_lay.addWidget(QLabel(f"<h3 style='color: {t_color}; margin: 0;'>[{severity}] {title}</h3>"))
            b_lay.addWidget(QLabel(f"<span style='font-size: 13px; color: #555;'>{msg}</span>"))
            app.safety_layout.addWidget(box)
    app.safety_layout.addStretch()