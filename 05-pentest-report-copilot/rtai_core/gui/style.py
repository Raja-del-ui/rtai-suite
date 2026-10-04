"""Military-grade tactical style — MIL-STD-2525 / STANAG 2019 / JADC2 compliant.

Palette — per MIL-STD-2525D & STANAG:
OD Green #4B5320 (primary), NATO Green #454B1B, Coyote Brown #81613C, Desert Tan #C2B280, Gold #D4AF37
Black-Green #0F1A0F (background), Gunmetal #1A261A (panel), Sage #D0D8C0 (text), Phosphor #33FF33 (HUD), Amber #FFB000 (alert)
Typography — Share Tech Mono (HUD), JetBrains Mono (terminal), Times New Roman (royal serif) — all monospaced for tactical readability
"""

# MIL-STD-2525D tactical symbology colors
MIL_STD_COLORS = {
    "friendly": "#00A0FF",  # Blue
    "hostile": "#FF0000",   # Red
    "neutral": "#00FF00",   # Green
    "unknown": "#FFFF00",   # Yellow
}

MILITARY_QSS = """
/* === ROOT === */
QMainWindow { background-color: #0F1A0F; }
QWidget { background-color: #0F1A0F; color: #D0D8C0; font-family: 'Share Tech Mono', 'JetBrains Mono', 'Consolas', monospace; font-size: 13px; }
QToolTip { background-color: #1A261A; color: #C2B280; border: 1px solid #4B5320; padding: 4px 8px; font-size: 10px; }

/* === LABELS === */
QLabel { color: #D0D8C0; font-size: 13px; }
QLabel[class="hud"] { color: #33FF33; font-family: 'Share Tech Mono', monospace; letter-spacing: 1px; font-weight: bold; }
QLabel[class="stencil"] { color: #C2B280; font-family: 'Share Tech Mono', monospace; letter-spacing: 2px; text-transform: uppercase; }
QLabel[class="classification"] { font-family: 'Share Tech Mono', monospace; letter-spacing: 1px; font-weight: bold; }

/* === GROUPBOX — TACTICAL PANEL — responsive for laptop 768p === */
QGroupBox { background-color: #1A261A; border: 1px solid #4B5320; border-radius: 4px; margin-top: 8px; padding: 10px 8px 8px 8px; font-weight: bold; color: #C2B280; font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 1px 6px; color: #C2B280; background-color: #1A261A; border: 1px solid #4B5320; border-radius: 2px; margin-top: 0px; }

/* === INPUTS — DARK TACTICAL — responsive === */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit { background-color: #0A0F0A; border: 1px solid #4B5320; border-radius: 3px; padding: 5px 8px; color: #E8EDE0; min-height: 30px; min-width: 110px; font-family: 'JetBrains Mono', monospace; font-size: 11px; selection-background-color: #4B5320; selection-color: white; }
QFormLayout { spacing: 6px; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus { border: 1px solid #D4AF37; background-color: #121F12; }
QLineEdit:disabled, QComboBox:disabled { background-color: #0F1A0F; color: #5A5A3A; border-color: #2A2E1A; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow { image: none; border-left: 1px solid #4B5320; width: 0px; }
QComboBox QAbstractItemView { background-color: #0A0F0A; border: 1px solid #4B5320; color: #D0D8C0; selection-background-color: #4B5320; }

/* === TEXTEDIT — PHOSPHOR TERMINAL === */
QTextEdit, QPlainTextEdit { background-color: #050A05; color: #33FF33; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; border: 1px solid #4B5320; border-radius: 3px; padding: 8px; line-height: 1.3; }
QTextEdit:focus { border: 1px solid #5A6428; }

/* === BUTTONS — TACTICAL === */
QPushButton { background-color: #4B5320; color: #FFFFFF; border: 1px solid #6B7A3B; border-radius: 3px; padding: 7px 16px; font-weight: bold; min-height: 32px; min-width: 90px; font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; }
QPushButton:hover { background-color: #5A6428; border-color: #D4AF37; color: #FFFFFF; }
QPushButton:pressed { background-color: #2F3515; border-color: #81613C; padding-top: 8px; }
QPushButton:disabled { background-color: #1A1F12; color: #5A5A3A; border-color: #2A2E1A; }
QPushButton[class="danger"] { background-color: #C8102E; border-color: #8B0000; }
QPushButton[class="danger"]:hover { background-color: #A00D24; border-color: #FF4444; }
QPushButton[class="success"] { background-color: #007A33; border-color: #00441A; }
QPushButton[class="success"]:hover { background-color: #009940; }
QPushButton[class="ghost"] { background-color: transparent; border: 1px solid #4B5320; color: #8A9A6A; }
QPushButton[class="ghost"]:hover { background-color: #1A261A; color: #C2B280; border-color: #C2B280; }

/* === PROGRESS — TACTICAL === */
QProgressBar { border: 1px solid #4B5320; border-radius: 3px; text-align: center; background-color: #0A0F0A; min-height: 16px; color: #33FF33; font-family: 'Share Tech Mono', monospace; font-size: 9px; }
QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4B5320, stop:1 #5A6428); }

/* === CHECKBOX / RADIO — TACTICAL === */
QCheckBox, QRadioButton { color: #D0D8C0; spacing: 8px; font-size: 12px; }
QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; border: 1px solid #4B5320; border-radius: 2px; background-color: #0A0F0A; }
QCheckBox::indicator:checked, QRadioButton::indicator:checked { background-color: #4B5320; border-color: #D4AF37; }
QCheckBox::indicator:checked { image: url(none); }

/* === TABS — TACTICAL RIBBON === */
QTabWidget::pane { border: 1px solid #4B5320; background: #0F1A0F; border-radius: 0px; top: -1px; }
QTabBar::tab { background: #1A261A; border: 1px solid #4B5320; border-bottom: none; padding: 8px 14px; margin-right: 1px; color: #8A9A6A; font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; min-width: 70px; }
QTabBar::tab:selected { background: #0F1A0F; color: #D4AF37; border-top: 2px solid #D4AF37; border-bottom: 1px solid #0F1A0F; }
QTabBar::tab:hover:!selected { background: #2A341A; color: #E8EDE0; border-top: 2px solid #5A6428; }
QTabBar::tab:disabled { color: #3A3A2A; }

/* === TABLES — TACTICAL GRID === */
QHeaderView::section { background-color: #1A261A; color: #D4AF37; padding: 7px 10px; border: 1px solid #4B5320; border-left: none; font-weight: bold; font-size: 9px; text-transform: uppercase; letter-spacing: 0.8px; }
QHeaderView::section:first { border-left: 1px solid #4B5320; }
QTableWidget { background-color: #0A0F0A; gridline-color: #1A2E1A; color: #D0D8C0; selection-background-color: #2A341A; selection-color: #33FF33; border: 1px solid #4B5320; border-radius: 3px; font-size: 11px; }
QTableWidget::item { padding: 4px 8px; border-bottom: 1px solid #0F1A0F; }
QTableWidget::item:selected { background-color: #1A2E1A; color: #33FF33; }

/* === LISTS === */
QListWidget { background-color: #0A0F0A; border: 1px solid #4B5320; border-radius: 3px; color: #33FF33; font-family: 'JetBrains Mono', monospace; font-size: 10px; padding: 4px; }
QListWidget::item { padding: 4px 6px; border-bottom: 1px solid #0F1A0F; }
QListWidget::item:selected { background-color: #1A2E1A; color: #D4AF37; border-left: 2px solid #D4AF37; }
QListWidget::item:hover { background-color: #121F12; }

/* === SCROLLBARS — TACTICAL === */
QScrollBar:vertical { background: #0A0F0A; width: 10px; margin: 0px; border-left: 1px solid #1A261A; }
QScrollBar::handle:vertical { background: #2A341A; min-height: 24px; border-radius: 3px; margin: 2px; border: 1px solid #4B5320; }
QScrollBar::handle:vertical:hover { background: #4B5320; border-color: #D4AF37; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollArea { border: none; background: #0F1A0F; }
QScrollArea > QWidget > QWidget { background: #0F1A0F; }
QScrollBar:horizontal { background: #0A0F0A; height: 10px; margin: 0px; border-top: 1px solid #1A261A; }
QScrollBar::handle:horizontal { background: #2A341A; min-width: 24px; border-radius: 3px; margin: 2px; border: 1px solid #4B5320; }
QScrollBar::handle:horizontal:hover { background: #4B5320; }

/* === SPLITTER / FRAME === */
QFrame { border: none; }
QSplitter::handle { background-color: #1A261A; border: 1px solid #4B5320; }

/* === STATUS BAR === */
QStatusBar { background-color: #0A0F0A; color: #8A9A6A; border-top: 1px solid #4B5320; font-family: 'Share Tech Mono', monospace; font-size: 9px; }

/* === TOOLTIP === */
QToolTip { background-color: #1A261A; color: #D4AF37; border: 1px solid #4B5320; padding: 5px 8px; font-size: 10px; border-radius: 3px; }

/* === SPINBOX ARROWS === */
QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button { background-color: #1A261A; border: 1px solid #4B5320; width: 18px; }
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #2A341A; border-color: #D4AF37; }
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
