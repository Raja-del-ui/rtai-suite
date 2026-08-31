"""Military-grade tactical style — OD Green / Coyote / Black-Green HUD."""

# Primary military palette
# OD Green #4B5320, NATO Green #454B1B, Coyote #81613C, Tan #C2B280
# Black-Green #0F1A0F, Sage #D0D8C0, Phosphor #33FF33 (for HUD)

MILITARY_QSS = """
QMainWindow { background-color: #0F1A0F; }
QWidget { background-color: #0F1A0F; color: #D0D8C0; font-family: 'Share Tech Mono', 'JetBrains Mono', 'Consolas', monospace; font-size: 13px; }
QLabel { color: #D0D8C0; font-size: 13px; }
QLabel[class="hud"] { color: #33FF33; font-family: 'Share Tech Mono', monospace; letter-spacing: 1px; }
QGroupBox { background-color: #1A261A; border: 1px solid #4B5320; border-radius: 4px; margin-top: 10px; padding: 10px 8px 8px 8px; font-weight: bold; color: #C2B280; font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; color: #C2B280; background-color: #1A261A; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background-color: #0A0F0A; border: 1px solid #4B5320; border-radius: 3px; padding: 6px 10px; color: #E8EDE0; min-height: 32px; min-width: 180px; font-family: 'JetBrains Mono', monospace; selection-background-color: #4B5320; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #C2B280; background-color: #121F12; }
QTextEdit { background-color: #050A05; color: #33FF33; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 12px; border: 1px solid #4B5320; border-radius: 3px; padding: 8px; }
QPushButton { background-color: #4B5320; color: #FFFFFF; border: 1px solid #6B7A3B; border-radius: 3px; padding: 7px 16px; font-weight: bold; min-height: 32px; min-width: 90px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; }
QPushButton:hover { background-color: #5A6428; border-color: #C2B280; color: #FFFFFF; }
QPushButton:pressed { background-color: #2F3515; border-color: #81613C; }
QPushButton:disabled { background-color: #1A1F12; color: #5A5A3A; border-color: #2A2E1A; }
QPushButton[class="danger"] { background-color: #C8102E; border-color: #8B0000; }
QPushButton[class="danger"]:hover { background-color: #A00D24; }
QPushButton[class="success"] { background-color: #007A33; border-color: #00441A; }
QProgressBar { border: 1px solid #4B5320; border-radius: 3px; text-align: center; background-color: #0A0F0A; min-height: 16px; color: #33FF33; font-family: 'Share Tech Mono', monospace; font-size: 10px; }
QProgressBar::chunk { background-color: #4B5320; }
QCheckBox { color: #D0D8C0; spacing: 6px; font-size: 12px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #4B5320; border-radius: 2px; background-color: #0A0F0A; }
QCheckBox::indicator:checked { background-color: #4B5320; border-color: #C2B280; image: url(none); }
QTabWidget::pane { border: 1px solid #4B5320; background: #0F1A0F; border-radius: 0px; top: -1px; }
QTabBar::tab { background: #1A261A; border: 1px solid #4B5320; border-bottom: none; padding: 8px 16px; margin-right: 1px; color: #8A9A6A; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; }
QTabBar::tab:selected { background: #0F1A0F; color: #C2B280; border-top: 2px solid #C2B280; border-bottom: 1px solid #0F1A0F; }
QTabBar::tab:hover { background: #2A341A; color: #E8EDE0; }
QHeaderView::section { background-color: #1A261A; color: #C2B280; padding: 6px; border: 1px solid #4B5320; font-weight: bold; font-size: 10px; text-transform: uppercase; }
QTableWidget { background-color: #0A0F0A; gridline-color: #2A341A; color: #D0D8C0; selection-background-color: #4B5320; }
QScrollBar:vertical { background: #0F1A0F; width: 10px; margin: 0px; }
QScrollBar::handle:vertical { background: #4B5320; min-height: 20px; border-radius: 3px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
"""

# Legacy alias for compatibility — now points to military theme
GLOBAL_QSS = MILITARY_QSS

# Classification banner QSS per level (used in launcher)
CLASS_BANNER_QSS = {
    "UNCLASS": "background: #007A33; color: white; font-weight: bold; font-family: 'Share Tech Mono', monospace; font-size: 11px; letter-spacing: 1px; padding: 4px 0px; border: none;",
    "CUI": "background: #502B85; color: white; font-weight: bold; font-family: 'Share Tech Mono', monospace; font-size: 11px; letter-spacing: 1px; padding: 4px 0px; border: none;",
    "CONFIDENTIAL": "background: #0033A0; color: white; font-weight: bold; font-family: 'Share Tech Mono', monospace; font-size: 11px; letter-spacing: 1px; padding: 4px 0px; border: none;",
    "SECRET": "background: #C8102E; color: white; font-weight: bold; font-family: 'Share Tech Mono', monospace; font-size: 11px; letter-spacing: 1px; padding: 4px 0px; border: none;",
    "TOP_SECRET": "background: #FF6A00; color: white; font-weight: bold; font-family: 'Share Tech Mono', monospace; font-size: 11px; letter-spacing: 1px; padding: 4px 0px; border: none;",
}

# HUD grid overlay for tactical map
TACTICAL_MAP_QSS = """
QFrame#tacticalMap { background-color: #050A05; border: 1px solid #4B5320; border-radius: 3px; }
QLabel#gridLabel { color: #2A4A2A; font-family: 'Share Tech Mono', monospace; font-size: 8px; }
QLabel#coordLabel { color: #33FF33; font-family: 'JetBrains Mono', monospace; font-size: 10px; background: rgba(0,0,0,180); padding: 2px 6px; border-radius: 2px; }
"""

# LED indicators for encryption status
LED_QSS = {
    "on": "background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #33FF33, stop:1 #0A4A0A); border: 1px solid #1A6A1A; border-radius: 6px;",
    "off": "background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #3A3A2A, stop:1 #1A1A0F); border: 1px solid #4B5320; border-radius: 6px;",
    "warn": "background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #FFC107, stop:1 #8B4513); border: 1px solid #FF8C00; border-radius: 6px;",
    "alert": "background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #FF0000, stop:1 #8B0000); border: 1px solid #FF0000; border-radius: 6px;",
}
