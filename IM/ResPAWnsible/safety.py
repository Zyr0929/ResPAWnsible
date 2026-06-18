from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QScrollArea)
from PyQt5.QtCore import Qt

def build_page(app, layout):
    layout.setContentsMargins(30, 30, 30, 30)
    
    title = QLabel("🛡️ Facility Safety & Audit Reports")
    title.setObjectName("Header1")
    layout.addWidget(title)
    
    sub = QLabel("Real-time monitoring of facility capacity and behavioral compliance.")
    sub.setStyleSheet("color: #757575; margin-bottom: 20px;")
    layout.addWidget(sub)
    
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("border: none; background: transparent;")
    
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    main_scroll_lay = QVBoxLayout(container)
    
    app.safety_layout = QVBoxLayout()
    app.safety_layout.setSpacing(15)
    main_scroll_lay.addLayout(app.safety_layout)
    main_scroll_lay.addStretch()
    
    scroll.setWidget(container)
    layout.addWidget(scroll)

def refresh(app):
    while app.safety_layout.count():
        item = app.safety_layout.takeAt(0)
        if item.widget(): item.widget().deleteLater()
        
    alerts = app.generate_safety_alerts()
    
    if not alerts:
        box = QFrame()
        box.setObjectName("MainCard")
        box.setStyleSheet("background: #F1F8E9; border: 1px solid #C8E6C9; border-left: 6px solid #4CAF50; padding: 20px; border-radius: 6px;")
        lay = QVBoxLayout(box)
        lay.addWidget(QLabel("<h3 style='color: #2E7D32; margin: 0;'>✅ Zero Active Threats</h3>"))
        lay.addWidget(QLabel("<p style='color: #558B2F;'>System audit cleared. All capacity and behavioral matrices are optimal.</p>"))
        app.safety_layout.addWidget(box)
    else:
        for severity, title, msg in alerts:
            box = QFrame()
            box.setStyleSheet("""
                QFrame {
                    background-color: white; 
                    border: 1px solid #E5E0D8; 
                    border-radius: 8px;
                }
            """)
            
            main_lay = QHBoxLayout(box)
            main_lay.setContentsMargins(0, 0, 0, 0)
            main_lay.setSpacing(0)
            
            strip = QFrame()
            color, t_color = ("#EF9A9A", "#C62828") if severity == "CRITICAL" else ("#FFE082", "#F57F17")
            strip.setStyleSheet(f"background-color: {color}; border-top-left-radius: 8px; border-bottom-left-radius: 8px;")
            strip.setFixedWidth(8)
            main_lay.addWidget(strip)
            
            content_lay = QVBoxLayout()
            content_lay.setContentsMargins(15, 10, 15, 10)

            title_lbl = QLabel(f"<b>[{severity}] {title}</b>")
            title_lbl.setStyleSheet(f"color: {t_color}; background: transparent; border: none; font-size: 14px;")
            
            msg_lbl = QLabel(msg)
            msg_lbl.setStyleSheet("color: #3A271E; background: transparent; border: none; font-size: 13px;")
            msg_lbl.setWordWrap(True)
            
            content_lay.addWidget(title_lbl)
            content_lay.addWidget(msg_lbl)
            main_lay.addLayout(content_lay)
            
            app.safety_layout.addWidget(box)