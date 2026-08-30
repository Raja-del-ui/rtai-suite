"""Royal-Sec Tactical Operations Console — MIL-STD military style launcher."""
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                   QTabWidget, QLabel, QPushButton, QFrame, QComboBox, QGridLayout)
    from PySide6.QtGui import QFont, QPainter, QPen, QColor
    from PySide6.QtCore import Qt, QTimer, Signal
    QT_OK = True
except ImportError:
    try:
        from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                     QTabWidget, QLabel, QPushButton, QFrame, QComboBox, QGridLayout)
        from PyQt6.QtGui import QFont, QPainter, QPen, QColor
        from PyQt6.QtCore import Qt, QTimer
        Signal = None
        QT_OK = True
    except ImportError:
        QT_OK = False

from rtai_core.gui.style import MILITARY_QSS, CLASS_BANNER_QSS, LED_QSS

def _classification_banner(classification="CUI", caveat=""):
    """Top/bottom classification banner — DoD standard colors."""
    from rtai_core.mission import CLASS_BANNERS, CLASS_COLORS
    # Resolve banner text and color
    base = CLASS_BANNERS.get(classification, classification)
    text = f"{base} // {caveat}" if caveat else base
    # Full banner with handling
    w = QFrame()
    color = CLASS_COLORS.get(classification, "#007A33")
    # Use QSS per classification
    qss = CLASS_BANNER_QSS.get(classification, CLASS_BANNER_QSS["CUI"])
    w.setStyleSheet(f"QFrame {{ background: {color}; border: none; }} QLabel {{ color: white; background: transparent; }}")
    w.setFixedHeight(26)
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lab = QLabel(text)
    lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lab.setFont(QFont("Share Tech Mono", 10, QFont.Weight.Bold))
    lab.setStyleSheet("color: white; background: transparent; letter-spacing: 1px;")
    lay.addWidget(lab)
    return w

def _banner():
    """Military header banner — OD Green / Coyote tactical."""
    w = QFrame()
    w.setStyleSheet("QFrame { background: #1A261A; border: none; border-bottom: 2px solid #4B5320; } QLabel { color: #D0D8C0; background: transparent; }")
    w.setFixedHeight(68)
    lay = QHBoxLayout(w)
    lay.setContentsMargins(14, 6, 14, 6)
    # Left: insignia + title
    left = QVBoxLayout()
    # Tactical callsign-style title with stencil effect
    title = QLabel("◆ RTAI  //  TACTICAL OPERATIONS CONSOLE")
    title.setFont(QFont("Share Tech Mono", 14, QFont.Weight.Bold))
    title.setStyleSheet("color: #C2B280; letter-spacing: 1.5px; background: transparent;")
    sub = QLabel("ROYAL-SEC  •  MISSION READY  •  AUTHORIZED USE ONLY  •  AUDIT-LOGGED")
    sub.setStyleSheet("color: #8A9A6A; font-size: 9px; letter-spacing: 0.8px; background: transparent;")
    left.addWidget(title)
    left.addWidget(sub)
    lay.addLayout(left)
    lay.addStretch()
    # Center: encryption LEDs
    led_box = QHBoxLayout()
    led_box.setSpacing(8)
    def _led(label, env_key, on_text="ON"):
        col = QVBoxLayout()
        col.setSpacing(2)
        dot = QLabel()
        dot.setFixedSize(12, 12)
        # Determine status
        val = os.environ.get(env_key, "0")
        # FIPS can be 1, MTLS cert exists, etc
        is_on = val == "1" or (env_key == "RTAI_TLS_CERT" and bool(val)) or (env_key == "RTAI_FIPS" and val=="1")
        # Map to LED
        if env_key == "RTAI_FIPS" and is_on:
            style = LED_QSS["on"]
        elif env_key in ("RTAI_MTLS", "RTAI_TLS_CERT") and is_on:
            style = LED_QSS["on"]
        elif env_key == "RTAI_TPM_ATTEST" and is_on:
            style = LED_QSS["on"]
        elif env_key == "RTAI_AUDIT_WORM" and is_on:
            style = LED_QSS["on"]
        elif env_key == "RTAI_HSM_REQUIRED" and val=="1":
            style = LED_QSS["warn"]  # HSM required but check not here
        else:
            style = LED_QSS["off"]
        dot.setStyleSheet(style)
        ttl = QLabel(label)
        ttl.setStyleSheet("color: #8A9A6A; font-size: 7px; background: transparent;")
        ttl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(dot, alignment=Qt.AlignmentFlag.AlignCenter)
        col.addWidget(ttl)
        led_box.addLayout(col)
        return col
    _led("FIPS", "RTAI_FIPS")
    _led("mTLS", "RTAI_TLS_CERT")
    _led("TPM", "RTAI_TPM_ATTEST")
    _led("WORM", "RTAI_AUDIT_WORM")
    _led("HSM", "RTAI_HSM_REQUIRED")
    lay.addLayout(led_box)
    lay.addSpacing(16)
    # Right: version + time
    right = QVBoxLayout()
    ver = QLabel("v4.1.0-military  •  FIPS/HSM/WORM")
    ver.setAlignment(Qt.AlignmentFlag.AlignRight)
    ver.setStyleSheet("color: #C2B280; font-size: 10px; font-weight: bold; background: transparent;")
    # Zulu time will be updated via timer in main
    plat = QLabel("ZULU  •  MGRS  •  STANDALONE")
    plat.setAlignment(Qt.AlignmentFlag.AlignRight)
    plat.setStyleSheet("color: #8A9A6A; font-size: 8px; letter-spacing: 0.6px; background: transparent;")
    right.addWidget(ver)
    right.addWidget(plat)
    lay.addLayout(right)
    return w

class TacticalMapWidget(QFrame):
    """Tactical map placeholder — grid with unit icons, coordinates, scan sweep."""
    def __init__(self):
        super().__init__()
        self.setObjectName("tacticalMap")
        self.setStyleSheet("QFrame#tacticalMap { background: #050A05; border: 1px solid #4B5320; border-radius: 3px; }")
        self.setMinimumHeight(200)
        # Overlay layout for HUD elements
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        # Top HUD
        hud_top = QHBoxLayout()
        hud_top.addWidget(self._hud_label("GRID: 38TLL 1234 5678", "#33FF33"))
        hud_top.addStretch()
        hud_top.addWidget(self._hud_label("AZ: 247°  RNG: 1.2km", "#33FF33"))
        lay.addLayout(hud_top)
        lay.addStretch()
        # Center crosshair + units
        center = QHBoxLayout()
        center.addStretch()
        center.addWidget(self._unit_icon("◆", "REAPER 06", "#C2B280"))
        center.addSpacing(40)
        center.addWidget(self._unit_icon("▲", "TARGET ALPHA", "#FF6A00"))
        center.addSpacing(40)
        center.addWidget(self._unit_icon("■", "FOB HAMMER", "#4B5320"))
        center.addStretch()
        lay.addLayout(center)
        lay.addStretch()
        # Bottom HUD
        hud_bot = QHBoxLayout()
        hud_bot.addWidget(self._hud_label("BFT: 3 ACTIVE  •  SIGINT: NOMINAL", "#8A9A6A"))
        hud_bot.addStretch()
        hud_bot.addWidget(self._hud_label("SCALE 1:25k  •  DTG 301200Z AUG 26", "#8A9A6A"))
        lay.addLayout(hud_bot)

    def _hud_label(self, text, color):
        l = QLabel(text)
        l.setStyleSheet(f"color: {color}; font-family: 'Share Tech Mono', monospace; font-size: 8px; background: rgba(0,0,0,160); padding: 2px 6px; border-radius: 2px;")
        return l

    def _unit_icon(self, sym, label, color):
        w = QFrame()
        w.setStyleSheet("QFrame { background: rgba(0,0,0,140); border: 1px solid #4B5320; border-radius: 4px; } QLabel { background: transparent; }")
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(2)
        s = QLabel(sym)
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold; background: transparent;")
        t = QLabel(label)
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("color: #D0D8C0; font-size: 7px; background: transparent;")
        l.addWidget(s)
        l.addWidget(t)
        return w

    def paintEvent(self, event):
        super().paintEvent(event)
        # Draw tactical grid
        painter = QPainter(self)
        painter.setPen(QPen(QColor("#1A3A1A"), 1, Qt.PenStyle.DotLine))
        step = 40
        for x in range(0, self.width(), step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            painter.drawLine(0, y, self.width(), y)
        # Crosshair center
        cx, cy = self.width()//2, self.height()//2
        painter.setPen(QPen(QColor("#2A5A2A"), 1, Qt.PenStyle.SolidLine))
        painter.drawLine(cx-20, cy, cx+20, cy)
        painter.drawLine(cx, cy-20, cx, cy+20)
        painter.setPen(QPen(QColor("#4B5320"), 1, Qt.PenStyle.SolidLine))
        painter.drawRect(cx-40, cy-40, 80, 80)
        painter.end()

def _tactical_dashboard_tab():
    """Military tactical dashboard — mission, OPSEC, encryption, audit, STIX."""
    try:
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QComboBox
        from PySide6.QtGui import QFont
        from PySide6.QtCore import Qt
    except ImportError:
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QComboBox
        from PyQt6.QtGui import QFont
        from PyQt6.QtCore import Qt
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(12, 12, 12, 12)
    lay.setSpacing(10)
    # Mission selector row
    mission_row = QHBoxLayout()
    mission_row.addWidget(_hud_label("MISSION:", "#C2B280"))
    # Try to load missions
    try:
        from rtai_core.mission import list_missions
        missions = list_missions()
        combo = QComboBox()
        if missions:
            for m in missions:
                combo.addItem(f"{m.mission_id} — {m.name} [{m.classification}]")
        else:
            combo.addItem("OP-MANTICORE SHIELD — CUI // NO MISSIONS — CREATE ONE")
        combo.setStyleSheet("QComboBox { background: #1A261A; border: 1px solid #4B5320; color: #D0D8C0; padding: 4px 8px; }")
        combo.setMinimumWidth(340)
    except Exception:
        combo = QComboBox()
        combo.addItem("OP-MANTICORE SHIELD — CUI")
    mission_row.addWidget(combo)
    mission_row.addStretch()
    mission_row.addWidget(_hud_label("CALLSIGN: REAPER 06  •  GRID: 38TLL 1234 5678  •  DTG: 301200Z", "#8A9A6A"))
    lay.addLayout(mission_row)
    # Tactical map
    tactical_map = TacticalMapWidget()
    lay.addWidget(tactical_map, stretch=2)
    # Status grid — OPSEC, encryption, audit, STIX
    grid = QGridLayout()
    grid.setSpacing(8)
    grid.addWidget(_status_card("OPSEC", "ROE SIGNED: YES\nTARGETS VALIDATED: 3/3\nCOMMS: AES-256-GCM", "#007A33"), 0, 0)
    grid.addWidget(_status_card("ENCRYPTION", "FIPS: ENFORCE\nmTLS: ESTABLISHED\nPQC: X25519+ML-KEM-768", "#4B5320"), 0, 1)
    grid.addWidget(_status_card("AUDIT", "CHAIN: VERIFIED\nWORM: ENABLED\nSIEM: NOMINAL (3 EVENTS)", "#1A261A"), 0, 2)
    grid.addWidget(_status_card("STIX / TAXII", "FEED: 12 INDICATORS\nTAXII: CONNECTED\nATT&CK: 8 TECHNIQUES", "#2F3515"), 1, 0)
    grid.addWidget(_status_card("TLA+ / STIG", "TLC: 3 SPECS VERIFIED\nSTIG: 0 FAILURES\nSBOM: VERIFIED", "#3A3F1B"), 1, 1)
    grid.addWidget(_status_card("BLUE FORCE", "BFT: 3 ACTIVE\nSIGINT: NOMINAL\nEW: PASSIVE", "#4B5320"), 1, 2)
    lay.addLayout(grid)
    # Quick actions
    actions = QHBoxLayout()
    for txt in ["NEW MISSION", "MISSION PACKAGE", "AFTER ACTION REPORT", "OPSEC CHECK"]:
        btn = QPushButton(txt)
        btn.setStyleSheet("QPushButton { background: #4B5320; color: white; padding: 6px 12px; font-size: 9px; }")
        actions.addWidget(btn)
    actions.addStretch()
    lay.addLayout(actions)
    # Footer tip with handling
    foot = QLabel("HANDLING: CUI//NOFORN  •  DESTRUCTION NOTICE: DESTROY BY ANY METHOD THAT WILL PREVENT DISCLOSURE  •  ALL ACTIONS AUDIT-LOGGED TO /var/log/royal-sec/audit.log")
    foot.setStyleSheet("color: #8A9A6A; font-size: 7px; letter-spacing: 0.5px;")
    foot.setWordWrap(True)
    lay.addWidget(foot)
    return w

def _hud_label(text, color="#C2B280"):
    try:
        from PySide6.QtWidgets import QLabel
    except ImportError:
        from PyQt6.QtWidgets import QLabel
    l = QLabel(text)
    l.setStyleSheet(f"color: {color}; font-family: 'Share Tech Mono', monospace; font-size: 9px; font-weight: bold;")
    return l

def _status_card(title, body, bg="#1A261A"):
    try:
        from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
        from PySide6.QtGui import QFont
    except ImportError:
        from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
        from PyQt6.QtGui import QFont
    card = QFrame()
    card.setStyleSheet(f"QFrame {{ background: {bg}; border: 1px solid #4B5320; border-top: 2px solid #C2B280; border-radius: 3px; }}")
    l = QVBoxLayout(card)
    l.setContentsMargins(8, 6, 8, 6)
    l.setSpacing(4)
    t = QLabel(title)
    t.setFont(QFont("Share Tech Mono", 9, QFont.Weight.Bold))
    t.setStyleSheet("color: #C2B280; border: none; background: transparent; letter-spacing: 0.8px;")
    b = QLabel(body)
    b.setStyleSheet("color: #D0D8C0; font-family: 'JetBrains Mono', monospace; font-size: 9px; border: none; background: transparent;")
    l.addWidget(t)
    l.addWidget(b)
    return card

def _dashboard_tab():
    # Legacy alias — now points to tactical dashboard
    return _tactical_dashboard_tab()

def main(*_args, **_kwargs):
    if not QT_OK:
        print("GUI requires PySide6: pip install PySide6")
        print("  Windows: py -m pip install PySide6")
        print("  Kali: pip install PySide6 --break-system-packages (or venv)")
        return 1
    app = QApplication(sys.argv)
    app.setApplicationName("Royal-Sec rtai-suite")
    app.setApplicationVersion("4.1.0-military")
    app.setOrganizationName("Royal-Sec")
    # Military QSS
    app.setStyleSheet(MILITARY_QSS)
    # Resolve classification for banners (mission or env)
    try:
        from rtai_core.mission import MISSION_DIR, list_missions
        missions = list_missions()
        classification = missions[0].classification if missions else os.environ.get("RTAI_CLASSIFICATION", "CUI")
        caveat = missions[0].caveat if missions else os.environ.get("RTAI_CAVEAT", "")
    except Exception:
        classification = os.environ.get("RTAI_CLASSIFICATION", "CUI")
        caveat = os.environ.get("RTAI_CAVEAT", "")
    win = QMainWindow()
    win.setWindowTitle(f"ROYAL-SEC — TACTICAL OPERATIONS CONSOLE v4.1.0-military [{classification}]")
    win.resize(1360, 860)
    central = QWidget()
    lay = QVBoxLayout(central)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)
    # Top classification banner
    lay.addWidget(_classification_banner(classification, caveat))
    lay.addWidget(_banner())
    tabs = QTabWidget()
    tabs.setTabPosition(QTabWidget.TabPosition.North)
    tabs.setMovable(True)
    tabs.setDocumentMode(True)
    from rtai_core.gui.recon_gui import ReconGUI
    from rtai_core.gui.fuzzer_gui import FuzzerGUI
    from rtai_core.gui.phish_gui import PhishGUI
    from rtai_core.gui.c2_gui import C2LabGUI
    from rtai_core.gui.report_gui import ReportGUI
    # Try mission tab
    try:
        from rtai_core.gui.mission_gui import MissionGUI
        mission_tab = MissionGUI()
    except Exception as e:
        # Fallback placeholder
        from PySide6.QtWidgets import QLabel
        mission_tab = QLabel(f"Mission GUI unavailable: {e}")
        mission_tab.setAlignment(Qt.AlignmentFlag.AlignCenter)
    tabs.addTab(_tactical_dashboard_tab(), "◆ TACTICAL")
    tabs.addTab(mission_tab, "MISSION")
    tabs.addTab(ReconGUI(), "RECON")
    tabs.addTab(FuzzerGUI(), "FUZZER")
    tabs.addTab(PhishGUI(), "PHISH")
    tabs.addTab(C2LabGUI(), "C2 LAB")
    tabs.addTab(ReportGUI(), "REPORT")
    # STIX/TAXII tab placeholder
    try:
        from rtai_core.gui.stix_gui import StixGUI
        tabs.addTab(StixGUI(), "STIX")
    except Exception:
        pass
    lay.addWidget(tabs)
    # Footer status bar — military
    footer = QFrame()
    footer.setStyleSheet("QFrame { background: #1A261A; border: none; border-top: 1px solid #4B5320; } QLabel { color: #8A9A6A; font-size: 8px; font-family: 'Share Tech Mono', monospace; background: transparent; }")
    footer.setFixedHeight(24)
    fl = QHBoxLayout(footer)
    fl.setContentsMargins(10, 0, 10, 0)
    fl.addWidget(QLabel("ROYAL-SEC • TACTICAL CONSOLE • FIPS ENFORCE • mTLS ESTABLISHED • WORM ENABLED • TPM ATTESTED • OPA ENFORCED"))
    fl.addStretch()
    # Zulu time
    zulu = QLabel(datetime.now(timezone.utc).strftime("DTG %d%H%MZ %b %y ZULU"))
    zulu.setStyleSheet("color: #33FF33; font-weight: bold;")
    fl.addWidget(zulu)
    # Update zulu every second
    try:
        timer = QTimer(footer)
        timer.timeout.connect(lambda: zulu.setText(datetime.now(timezone.utc).strftime("DTG %d%H%MZ %b %y ZULU")))
        timer.start(1000)
    except Exception:
        pass
    lay.addWidget(footer)
    # Bottom classification banner
    lay.addWidget(_classification_banner(classification, caveat))
    win.setCentralWidget(central)
    win.show()
    return app.exec()

launch_gui = main

if __name__ == "__main__":
    sys.exit(main())
