"""Royal-Sec branded main GUI launcher - unified tabbed interface."""
import sys
from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton, QFrame
    from PySide6.QtGui import QFont
    from PySide6.QtCore import Qt
    QT_OK = True
except ImportError:
    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton, QFrame
        from PyQt6.QtGui import QFont
        from PyQt6.QtCore import Qt
        QT_OK = True
    except ImportError:
        QT_OK = False

def _banner():
    w = QFrame()
    w.setStyleSheet("QFrame { background-color: #0A1931; border: none; } QLabel { color: white; }")
    w.setFixedHeight(64)
    lay = QHBoxLayout(w)
    lay.setContentsMargins(20, 8, 20, 8)
    left = QVBoxLayout()
    royal = QLabel("ROYAL-SEC")
    royal.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
    royal.setStyleSheet("color: #FFC107; letter-spacing: 2px;")
    sub = QLabel("Red Team Operations  •  AI-Integrated Toolkit")
    sub.setStyleSheet("color: #B0BEC5; font-size: 11px;")
    left.addWidget(royal)
    left.addWidget(sub)
    lay.addLayout(left)
    lay.addStretch()
    right = QVBoxLayout()
    ver = QLabel("v4.0.0  •  Military-Grade")
    ver.setAlignment(Qt.AlignmentFlag.AlignRight)
    ver.setStyleSheet("color: #FFC107; font-size: 11px; font-weight: bold;")
    plat = QLabel("Windows  •  Kali Linux  •  Standalone")
    plat.setAlignment(Qt.AlignmentFlag.AlignRight)
    plat.setStyleSheet("color: #78909C; font-size: 10px;")
    right.addWidget(ver)
    right.addWidget(plat)
    lay.addLayout(right)
    return w

def _dashboard_tab():
    try:
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, QFrame
        from PySide6.QtGui import QFont
        from PySide6.QtCore import Qt
    except ImportError:
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, QFrame
        from PyQt6.QtGui import QFont
        from PyQt6.QtCore import Qt
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(20, 20, 20, 20)
    lay.setSpacing(16)
    title = QLabel("Welcome to Royal-Sec Operations Console")
    title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
    title.setStyleSheet("color: #0A1931;")
    lay.addWidget(title)
    sub = QLabel("Select a tool below or use the tabs above. All tools are authorized-use only and run fully offline where noted.")
    sub.setWordWrap(True)
    sub.setStyleSheet("color: #546E7A;")
    lay.addWidget(sub)
    grid = QGridLayout()
    grid.setSpacing(12)
    cards = [
        ("Recon Agent", "Passive OSINT → exposure score", "#E3F2FD"),
        ("Injection Fuzzer", "LLM prompt-injection + judge", "#FFF3E0"),
        ("Phishing Sim", "Authorized awareness campaigns", "#E8F5E9"),
        ("C2 Lab", "Beacon simulator • offline", "#F3E5F5"),
        ("Report Copilot", "AI-assisted pentest reports", "#E0F7FA"),
    ]
    for i, (t, d, col) in enumerate(cards):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: {col}; border: 1px solid #CFD8DC; border-radius: 8px; }}")
        cl = QVBoxLayout(card)
        tl = QLabel(t)
        tl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        tl.setStyleSheet("color: #0A1931; border: none;")
        dl = QLabel(d)
        dl.setStyleSheet("color: #546E7A; font-size: 11px; border: none;")
        dl.setWordWrap(True)
        cl.addWidget(tl)
        cl.addWidget(dl)
        grid.addWidget(card, i // 3, i % 3)
    lay.addLayout(grid)
    foot = QLabel("Tip: Use rtai --list on CLI for the same tools. All operations are audit-logged to audit.log when RTAI_AUDIT_LOG is set.")
    foot.setStyleSheet("color: #78909C; font-size: 10px;")
    foot.setWordWrap(True)
    lay.addWidget(foot)
    lay.addStretch()
    return w

def main(*_args, **_kwargs):
    if not QT_OK:
        print("GUI requires PySide6: pip install PySide6")
        print("  Windows: py -m pip install PySide6")
        print("  Kali: pip install PySide6 --break-system-packages (or venv)")
        return 1
    app = QApplication(sys.argv)
    app.setApplicationName("Royal-Sec rtai-suite")
    app.setApplicationVersion("4.0.0")
    app.setOrganizationName("Royal-Sec")
    app.setStyleSheet("""
        QMainWindow { background: #F5F7FA; }
        QTabWidget::pane { border: 1px solid #CFD8DC; background: white; border-radius: 6px; }
        QTabBar::tab { background: #ECEFF1; border: 1px solid #CFD8DC; padding: 9px 18px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: 600; }
        QTabBar::tab:selected { background: white; border-bottom: 2px solid #FFC107; color: #0A1931; }
        QTabBar::tab:hover { background: #E3F2FD; }
        QGroupBox { font-weight: bold; border: 1px solid #CFD8DC; border-radius: 6px; margin-top: 10px; padding-top: 12px; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #0A1931; }
        QPushButton { border-radius: 6px; padding: 8px 18px; }
    """)
    win = QMainWindow()
    win.setWindowTitle("Royal-Sec — rtai-suite v4.0.0 Military-Grade")
    win.resize(1280, 800)
    central = QWidget()
    lay = QVBoxLayout(central)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)
    lay.addWidget(_banner())
    tabs = QTabWidget()
    tabs.setTabPosition(QTabWidget.TabPosition.North)
    tabs.setMovable(True)
    from rtai_core.gui.recon_gui import ReconGUI
    from rtai_core.gui.fuzzer_gui import FuzzerGUI
    from rtai_core.gui.phish_gui import PhishGUI
    from rtai_core.gui.c2_gui import C2LabGUI
    from rtai_core.gui.report_gui import ReportGUI
    tabs.addTab(_dashboard_tab(), "Dashboard")
    tabs.addTab(ReconGUI(), "Recon")
    tabs.addTab(FuzzerGUI(), "Fuzzer")
    tabs.addTab(PhishGUI(), "Phish")
    tabs.addTab(C2LabGUI(), "C2 Lab")
    tabs.addTab(ReportGUI(), "Report")
    lay.addWidget(tabs)
    # Footer status bar
    footer = QFrame()
    footer.setStyleSheet("QFrame { background: #0A1931; border: none; } QLabel { color: #B0BEC5; font-size: 10px; }")
    footer.setFixedHeight(22)
    fl = QHBoxLayout(footer)
    fl.setContentsMargins(12, 0, 12, 0)
    fl.addWidget(QLabel("ROYAL-SEC • Authorized Use Only • Audit-logged • v4.0.0 • Windows • Kali Linux"))
    fl.addStretch()
    fl.addWidget(QLabel("Industrial • Standalone • Military-Grade"))
    lay.addWidget(footer)
    win.setCentralWidget(central)
    win.show()
    return app.exec()

launch_gui = main

if __name__ == "__main__":
    sys.exit(main())
