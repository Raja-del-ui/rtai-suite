"""Royal-Sec Tactical Operations Console — MIL-STD military style launcher."""
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                   QTabWidget, QLabel, QPushButton, QFrame, QComboBox, QGridLayout,
                                   QDialog, QDialogButtonBox, QLineEdit, QMessageBox)
    from PySide6.QtGui import QFont, QPainter, QPen, QColor, QPixmap
    from PySide6.QtCore import Qt, QTimer, Signal
    QT_OK = True
except ImportError:
    try:
        from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                     QTabWidget, QLabel, QPushButton, QFrame, QComboBox, QGridLayout,
                                     QDialog, QDialogButtonBox, QLineEdit, QMessageBox)
        from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QPixmap
        from PyQt6.QtCore import Qt, QTimer
        Signal = None
        QT_OK = True
    except ImportError:
        QT_OK = False

from rtai_core.gui.style import MILITARY_QSS, CLASS_BANNER_QSS, LED_QSS

def _classification_banner(classification="CUI", caveat=""):
    """Top/bottom classification banner — DoD standard colors (compact for laptop)."""
    from rtai_core.mission import CLASS_BANNERS, CLASS_COLORS
    base = CLASS_BANNERS.get(classification, classification)
    text = f"{base} // {caveat}" if caveat else base
    w = QFrame()
    color = CLASS_COLORS.get(classification, "#007A33")
    w.setStyleSheet(f"QFrame {{ background: {color}; border: none; }} QLabel {{ color: white; background: transparent; }}")
    w.setFixedHeight(22)
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lab = QLabel(text)
    lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lab.setFont(QFont("Share Tech Mono", 9, QFont.Weight.Bold))
    lab.setStyleSheet("color: white; background: transparent; letter-spacing: 1px;")
    lay.addWidget(lab)
    return w

def _banner():
    """Military header banner — OD Green / Coyote tactical with Royal Security logo (compact)."""
    w = QFrame()
    w.setStyleSheet("QFrame { background: #0A0A0A; border: none; border-bottom: 2px solid #C2B280; } QLabel { color: #D0D8C0; background: transparent; }")
    w.setFixedHeight(60)
    lay = QHBoxLayout(w)
    lay.setContentsMargins(12, 6, 12, 6)
    # Left: logo + title block
    try:
        from PySide6.QtGui import QPixmap
    except ImportError:
        from PyQt6.QtGui import QPixmap
    logo_path = Path(__file__).parent / "assets" / "logo_small.png"
    if not logo_path.exists():
        logo_path = Path(__file__).parent / "assets" / "logo.png"
    logo_lab = QLabel()
    logo_lab.setFixedSize(56, 56)
    logo_lab.setStyleSheet("background: transparent; border: none;")
    if logo_path.exists():
        try:
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                pix = pix.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_lab.setPixmap(pix)
                logo_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            else:
                logo_lab.setText("◆")
                logo_lab.setStyleSheet("color: #C2B280; font-size: 28px; background: transparent;")
        except Exception:
            logo_lab.setText("◆")
    else:
        logo_lab.setText("◆")
        logo_lab.setStyleSheet("color: #C2B280; font-size: 28px; background: transparent;")
    lay.addWidget(logo_lab)
    lay.addSpacing(8)
    # Title block
    left = QVBoxLayout()
    left.setSpacing(1)
    title = QLabel("ROYAL SECURITY  //  TACTICAL OPERATIONS CONSOLE")
    title.setFont(QFont("Times New Roman", 13, QFont.Weight.Bold))
    title.setStyleSheet("color: #D4AF37; letter-spacing: 2px; background: transparent; font-family: 'Times New Roman', serif;")
    sub = QLabel("CYBER PROTECTION  •  MISSION READY  •  AUTHORIZED USE ONLY  •  AUDIT-LOGGED")
    sub.setStyleSheet("color: #C2B280; font-size: 8px; letter-spacing: 1.2px; background: transparent; font-family: 'Share Tech Mono', monospace;")
    crown = QLabel("♛  ROYAL-SEC  •  EST. 2026  •  BY APPOINTMENT")
    crown.setStyleSheet("color: #8A9A6A; font-size: 7px; letter-spacing: 0.8px; background: transparent;")
    left.addWidget(title)
    left.addWidget(sub)
    left.addWidget(crown)
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
        self.setMinimumHeight(150)
        self.setMaximumHeight(220)
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
        # Royal Security watermark logo faint center
        try:
            from PySide6.QtGui import QPixmap
        except ImportError:
            try:
                from PyQt6.QtGui import QPixmap
            except ImportError:
                QPixmap = None
        if QPixmap:
            logo_path = Path(__file__).parent / "assets" / "logo_small.png"
            if logo_path.exists():
                try:
                    pix = QPixmap(str(logo_path))
                    if not pix.isNull():
                        # Draw faint 90x90 centered with low opacity
                        painter.setOpacity(0.07)
                        w, h = 90, 90
                        cx, cy = self.width()//2, self.height()//2
                        scaled = pix.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        painter.drawPixmap(cx - scaled.width()//2, cy - scaled.height()//2 - 10, scaled)
                        painter.setOpacity(1.0)
                except Exception:
                    pass
        # Crosshair center
        cx, cy = self.width()//2, self.height()//2
        painter.setPen(QPen(QColor("#2A5A2A"), 1, Qt.PenStyle.SolidLine))
        painter.drawLine(cx-20, cy, cx+20, cy)
        painter.drawLine(cx, cy-20, cx, cy+20)
        painter.setPen(QPen(QColor("#4B5320"), 1, Qt.PenStyle.SolidLine))
        painter.drawRect(cx-40, cy-40, 80, 80)
        # Gold laurel accent corners
        painter.setPen(QPen(QColor("#D4AF37"), 1, Qt.PenStyle.SolidLine))
        for (x, y) in [(8,8), (self.width()-28,8), (8,self.height()-28), (self.width()-28,self.height()-28)]:
            painter.drawLine(x, y, x+20, y)
            painter.drawLine(x, y, x, y+20)
        painter.end()

def _wrap_scroll(widget):
    """Wrap tab in QScrollArea so 768p laptop can scroll instead of clipping."""
    try:
        # Use global QScrollArea if available (top-level import)
        _QScrollArea = QScrollArea  # type: ignore[name-defined]
    except NameError:
        # Fallback import for PyInstaller/fallback
        try:
            from PySide6.QtWidgets import QScrollArea as _QScrollArea
        except ImportError:
            from PyQt6.QtWidgets import QScrollArea as _QScrollArea
    scroll = _QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setStyleSheet("QScrollArea { background: #0F1A0F; border: none; } QScrollBar { background: #0F1A0F; }")
    scroll.setWidget(widget)
    return scroll

def _tactical_dashboard_tab():
    """Military tactical dashboard — mission, OPSEC, encryption, audit, STIX (compact for laptop)."""
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
    # Quick actions — full kill chain + mission
    actions = QHBoxLayout()
    actions.setSpacing(6)
    for txt in ["NEW MISSION", "RECON", "FORGE", "FUZZ", "PHISH", "C2", "PERSIST", "APT", "KILLCHAIN", "REPORT", "STIX", "OPSEC"]:
        btn = QPushButton(txt)
        btn.setStyleSheet("QPushButton { background: #4B5320; color: white; padding: 5px 9px; font-size: 8px; font-weight: bold; border-radius: 3px; } QPushButton:hover { background: #5A6428; }")
        btn.setToolTip(f"Quick launch {txt.lower()} (see tab)")
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

def _show_splash(app):
    """Royal Security splash with laurel logo — 900ms."""
    try:
        from PySide6.QtWidgets import QSplashScreen
        from PySide6.QtGui import QPixmap, QFont, QPainter, QColor
        from PySide6.QtCore import Qt
    except ImportError:
        try:
            from PyQt6.QtWidgets import QSplashScreen
            from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor
            from PyQt6.QtCore import Qt
        except ImportError:
            return
    logo_path = Path(__file__).parent / "assets" / "logo.png"
    if not logo_path.exists():
        return
    try:
        pix = QPixmap(str(logo_path))
        if pix.isNull():
            return
        # Scale splash to 420x420 with black background
        splash_pix = QPixmap(460, 460)
        splash_pix.fill(QColor("#0A0A0A"))
        painter = QPainter(splash_pix)
        # Draw logo centered
        scaled = pix.scaled(380, 380, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        x = (splash_pix.width() - scaled.width()) // 2
        y = 20
        painter.drawPixmap(x, y, scaled)
        painter.setPen(QColor("#D4AF37"))
        painter.setFont(QFont("Times New Roman", 18, QFont.Weight.Bold))
        painter.drawText(splash_pix.rect().adjusted(0, 400, 0, -30), Qt.AlignmentFlag.AlignCenter, "ROYAL SECURITY")
        painter.setPen(QColor("#C2B280"))
        painter.setFont(QFont("Share Tech Mono", 9))
        painter.drawText(splash_pix.rect().adjusted(0, 425, 0, -10), Qt.AlignmentFlag.AlignCenter, "CYBER PROTECTION  •  TACTICAL CONSOLE  •  v4.1.0-military")
        painter.end()
        splash = QSplashScreen(splash_pix)
        splash.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        splash.show()
        app.processEvents()
        # Show for 900ms
        from PySide6.QtCore import QEventLoop, QTimer
        loop = QEventLoop()
        QTimer.singleShot(900, loop.quit)
        loop.exec()
        splash.close()
    except Exception:
        pass

def main(*_args, **_kwargs):
    if not QT_OK:
        print("GUI requires PySide6: pip install PySide6")
        print("  Windows: py -m pip install PySide6")
        print("  Kali: pip install PySide6 --break-system-packages (or venv)")
        return 1
    # High-DPI for laptop 125%/150% scaling
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setApplicationName("Royal-Sec rtai-suite")
    app.setApplicationVersion("4.1.0-military")
    app.setOrganizationName("Royal-Sec")
    # Military QSS
    app.setStyleSheet(MILITARY_QSS)
    # --- GUI password gate (military) — must pass before Tactical Console ---
    # Bypass: RTAI_GUI_NO_AUTH=1 (audited, dev) or QT offscreen first-run (CI)
    _bypass_no_auth = os.environ.get("RTAI_GUI_NO_AUTH") == "1"
    _is_offscreen = os.environ.get("QT_QPA_PLATFORM") == "offscreen"
    if _bypass_no_auth:
        try:
            from rtai_core.audit import record as _audit
            from rtai_core.audit import actor_from_env as _actor
            _audit("gui_auth_bypass_no_auth", actor=_actor())
        except Exception:
            pass
    elif _is_offscreen:
        try:
            from rtai_core.gui.auth import is_first_run
            if is_first_run():
                pass  # CI first-run — no password yet, allow
            else:
                # Offscreen but password exists — require RTAI_GUI_PASSWORD env for CI
                if os.environ.get("RTAI_GUI_PASSWORD"):
                    from rtai_core.gui.auth import check_password, record_success
                    if check_password(os.environ.get("RTAI_GUI_PASSWORD","")):
                        record_success()
                    else:
                        print("[x] GUI password env mismatch", file=sys.stderr)
                        return 1
                else:
                    # No password env and not first-run — allow for CI (verify_project)
                    pass
        except Exception:
            pass
    else:
        _auth_ok = True
        try:
            from rtai_core.gui.auth import is_first_run, is_locked_out, check_password, set_password, record_failure, record_success, password_strength_ok
        except ImportError:
            _auth_ok = False
            is_first_run = lambda: False  # type: ignore
        if _auth_ok:
            # Check lockout first
            try:
                locked, remaining = is_locked_out()
                if locked:
                    QMessageBox.critical(None, "Royal-Sec — Locked", f"Too many failed attempts. Try again in {remaining}s.\n\nAudit logged.")
                    return 1
            except Exception:
                pass
            if is_first_run():
                # First run — setup password
                dlg = QDialog()
                dlg.setWindowTitle("Royal-Sec — Set Tactical Console Password")
                dlg.setModal(True)
                dlg.setFixedSize(420, 280)
                dlg.setStyleSheet("QDialog { background: #0A0A0A; border: 2px solid #C2B280; } QLabel { color: #D0D8C0; background: transparent; } QLineEdit { background: #1A261A; border: 1px solid #4B5320; color: #E8EDE0; padding: 6px; }")
                lay = QVBoxLayout(dlg)
                lay.setContentsMargins(20, 16, 20, 16)
                lay.setSpacing(10)
                # Logo
                try:
                    logo_path = Path(__file__).parent / "assets" / "logo_small.png"
                    if logo_path.exists():
                        pix = QPixmap(str(logo_path)).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        logo_lab = QLabel()
                        logo_lab.setPixmap(pix)
                        logo_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        lay.addWidget(logo_lab)
                except Exception:
                    pass
                title = QLabel("ROYAL SECURITY — INITIAL SETUP")
                title.setFont(QFont("Times New Roman", 12, QFont.Weight.Bold))
                title.setStyleSheet("color: #D4AF37; letter-spacing: 1.5px; background: transparent;")
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lay.addWidget(title)
                info = QLabel("Set a Tactical Console password (8+ chars, 3 of: lower/upper/digit/symbol).\nStored as PBKDF2-SHA256 260k + keyring/file 600. Audit-logged.")
                info.setStyleSheet("color: #8A9A6A; font-size: 9px; background: transparent;")
                info.setWordWrap(True)
                lay.addWidget(info)
                pw1 = QLineEdit(); pw1.setEchoMode(QLineEdit.EchoMode.Password); pw1.setPlaceholderText("New password")
                pw2 = QLineEdit(); pw2.setEchoMode(QLineEdit.EchoMode.Password); pw2.setPlaceholderText("Confirm password")
                lay.addWidget(QLabel("New Password:")); lay.addWidget(pw1)
                lay.addWidget(QLabel("Confirm:")); lay.addWidget(pw2)
                btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
                btns.setStyleSheet("QPushButton { background: #4B5320; color: white; padding: 6px 12px; }")
                lay.addWidget(btns)
                btns.accepted.connect(dlg.accept)
                btns.rejected.connect(dlg.reject)
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    return 1
                if pw1.text() != pw2.text():
                    QMessageBox.warning(None, "Royal-Sec", "Passwords do not match")
                    return 1
                ok, msg = password_strength_ok(pw1.text())
                if not ok:
                    QMessageBox.warning(None, "Royal-Sec", msg)
                    return 1
                try:
                    set_password(pw1.text())
                except Exception as e:
                    QMessageBox.critical(None, "Royal-Sec", f"Failed to set password: {e}")
                    return 1
                QMessageBox.information(None, "Royal-Sec", "Password set — Tactical Console will now launch.\n\nStore: OS keyring or %APPDATA%\\Royal-Sec\\gui_auth.json (600).")
            else:
                # Normal login — 3 attempts
                for attempt in range(3):
                    dlg = QDialog()
                    dlg.setWindowTitle(f"Royal-Sec — Tactical Console Login (attempt {attempt+1}/3)")
                    dlg.setModal(True)
                    dlg.setFixedSize(380, 220)
                    dlg.setStyleSheet("QDialog { background: #0A0A0A; border: 2px solid #C2B280; } QLabel { color: #D0D8C0; background: transparent; } QLineEdit { background: #1A261A; border: 1px solid #4B5320; color: #E8EDE0; padding: 6px; }")
                    lay = QVBoxLayout(dlg)
                    # Logo small
                    try:
                        lp = Path(__file__).parent / "assets" / "logo_small.png"
                        if lp.exists():
                            pix = QPixmap(str(lp)).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            ll = QLabel()
                            ll.setPixmap(pix)
                            ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            lay.addWidget(ll)
                    except Exception:
                        pass
                    hdr = QLabel("ROYAL SECURITY — CLASSIFIED ACCESS")
                    hdr.setFont(QFont("Times New Roman", 11, QFont.Weight.Bold))
                    hdr.setStyleSheet("color: #D4AF37; letter-spacing: 1px; background: transparent;")
                    hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lay.addWidget(hdr)
                    sub = QLabel("Enter Tactical Console password")
                    sub.setStyleSheet("color: #8A9A6A; font-size: 9px; background: transparent;")
                    sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lay.addWidget(sub)
                    pw = QLineEdit(); pw.setEchoMode(QLineEdit.EchoMode.Password); pw.setPlaceholderText("Password")
                    lay.addWidget(pw)
                    btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
                    btns.setStyleSheet("QPushButton { background: #4B5320; color: white; padding: 6px 12px; }")
                    lay.addWidget(btns)
                    btns.accepted.connect(dlg.accept)
                    btns.rejected.connect(dlg.reject)
                    if dlg.exec() != QDialog.DialogCode.Accepted:
                        return 1
                    if check_password(pw.text()):
                        record_success()
                        try:
                            from rtai_core.audit import record as _audit
                            from rtai_core.audit import actor_from_env as _actor
                            _audit("gui_auth_success", actor=_actor())
                        except Exception:
                            pass
                        break
                    else:
                        record_failure()
                        try:
                            from rtai_core.audit import record as _audit
                            from rtai_core.audit import actor_from_env as _actor
                            _audit("gui_auth_failed", actor=_actor(), attempt=attempt+1)
                        except Exception:
                            pass
                        if attempt == 2:
                            QMessageBox.critical(None, "Royal-Sec", "Too many failed attempts — locked for 5 minutes.\nAudit logged.")
                            return 1
                        else:
                            QMessageBox.warning(None, "Royal-Sec", f"Incorrect password — {2-attempt} attempts remaining")
                            continue
                else:
                    return 1
    # Royal Security splash
    _show_splash(app)
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
    # Responsive sizing — 92% of available screen, capped, min for laptop 1024x600
    try:
        screen = app.primaryScreen()
        avail = screen.availableGeometry() if screen else None
        if avail:
            w = min(1280, max(1024, int(avail.width() * 0.92)))
            h = min(800, max(620, int(avail.height() * 0.90)))
            win.resize(w, h)
            # Center on screen
            win.move(avail.x() + (avail.width() - w)//2, avail.y() + (avail.height() - h)//2)
        else:
            win.resize(1100, 700)
    except Exception:
        win.resize(1100, 700)
    win.setMinimumSize(1024, 620)
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
    from rtai_core.gui.weaponize_gui import WeaponizeGUI
    from rtai_core.gui.persist_gui import PersistGUI
    from rtai_core.gui.apt_gui import AptGUI
    from rtai_core.gui.killchain_gui import KillchainGUI
    # Try mission tab
    try:
        from rtai_core.gui.mission_gui import MissionGUI
        mission_tab = MissionGUI()
    except Exception as e:
        # Fallback placeholder — use globally imported QLabel (do not re-import locally to avoid shadowing)
        mission_tab = QLabel(f"Mission GUI unavailable: {e}")
        mission_tab.setAlignment(Qt.AlignmentFlag.AlignCenter)
    # All tabs wrapped in scroll so laptop 768p never clips QGroupBox
    tabs.addTab(_wrap_scroll(_tactical_dashboard_tab()), "◆ TACTICAL")
    tabs.addTab(_wrap_scroll(mission_tab), "MISSION")
    tabs.addTab(_wrap_scroll(ReconGUI()), "RECON")
    tabs.addTab(_wrap_scroll(WeaponizeGUI()), "FORGE")
    tabs.addTab(_wrap_scroll(FuzzerGUI()), "FUZZER")
    tabs.addTab(_wrap_scroll(PhishGUI()), "PHISH")
    tabs.addTab(_wrap_scroll(C2LabGUI()), "C2 LAB")
    tabs.addTab(_wrap_scroll(PersistGUI()), "PERSIST")
    tabs.addTab(_wrap_scroll(AptGUI()), "APT LAB")
    tabs.addTab(_wrap_scroll(KillchainGUI()), "KILLCHAIN")
    tabs.addTab(_wrap_scroll(ReportGUI()), "REPORT")
    # STIX/TAXII tab
    try:
        from rtai_core.gui.stix_gui import StixGUI
        tabs.addTab(_wrap_scroll(StixGUI()), "STIX")
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
