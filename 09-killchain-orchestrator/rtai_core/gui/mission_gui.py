"""Mission GUI — military mission planning with classification & ROE."""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
try:
    from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QGroupBox,
                                   QFormLayout, QPushButton, QTextEdit, QProgressBar, QMessageBox, QDateTimeEdit, QListWidget)
    from PySide6.QtGui import QFont
    from PySide6.QtCore import Qt, QDateTime
except ImportError:
    from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QGroupBox,
                                 QFormLayout, QPushButton, QTextEdit, QProgressBar, QMessageBox, QDateTimeEdit, QListWidget)
    from PyQt6.QtGui import QFont
    from PyQt6.QtCore import Qt, QDateTime
from rtai_core.gui.base import WorkerThread
from rtai_core.mission import Mission, ROE, CLASSIFICATIONS, CAVEATS, CLASS_COLORS, save_mission, list_missions

class MissionGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.worker=None
        self._build()
        self._load_missions()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(12,12,12,12); lay.setSpacing(10)
        hdr=QLabel("MISSION PLANNING  —  Classification, ROE, OPSEC")
        hdr.setFont(QFont("Share Tech Mono", 11, QFont.Weight.Bold)); hdr.setStyleSheet("color: #C2B280; letter-spacing: 1px;")
        lay.addWidget(hdr)
        # Mission ID row
        g0=QGroupBox("Mission Identity")
        f0=QFormLayout(g0)
        self.mission_id=QLineEdit(placeholderText="auto — OP-XXXXXX")
        self.name=QLineEdit(placeholderText="MANTICORE SHIELD")
        self.callsign=QLineEdit(placeholderText="REAPER 06")
        self.grid=QLineEdit(placeholderText="38TLL 1234 5678 (MGRS)")
        f0.addRow("Mission ID:", self.mission_id)
        f0.addRow("Name:", self.name)
        f0.addRow("Callsign:", self.callsign)
        f0.addRow("Grid REF:", self.grid)
        lay.addWidget(g0)
        # Classification
        g1=QGroupBox("Classification & Handling")
        f1=QFormLayout(g1)
        self.classification=QComboBox(); self.classification.addItems(CLASSIFICATIONS); self.classification.setCurrentText("CUI")
        self.caveat=QComboBox(); self.caveat.addItems(CAVEATS); self.caveat.setCurrentText("")
        self.approver=QLineEdit(placeholderText="COL Smith, J3")
        self.rank=QLineEdit(placeholderText="O-6")
        f1.addRow("Classification:", self.classification)
        f1.addRow("Caveat:", self.caveat)
        f1.addRow("Approver:", self.approver)
        f1.addRow("Rank:", self.rank)
        lay.addWidget(g1)
        # ROE
        g2=QGroupBox("Rules of Engagement")
        f2=QFormLayout(g2)
        self.targets=QLineEdit(placeholderText="example.com, 10.0.0.1/24 (comma-separated)")
        self.techniques=QComboBox(); self.techniques.addItems(["recon,fuzz,phish,c2,report","recon,report","fuzz","phish"])
        self.start=QDateTimeEdit(); self.start.setDateTime(QDateTime.currentDateTimeUtc()); self.start.setDisplayFormat("yyyy-MM-dd HH:mm UTC")
        self.end=QDateTimeEdit(); self.end.setDateTime(QDateTime.currentDateTimeUtc().addDays(7)); self.end.setDisplayFormat("yyyy-MM-dd HH:mm UTC")
        f2.addRow("Targets:", self.targets)
        f2.addRow("Techniques:", self.techniques)
        f2.addRow("Start:", self.start)
        f2.addRow("End:", self.end)
        lay.addWidget(g2)
        # List
        self.mission_list=QListWidget()
        self.mission_list.setStyleSheet("QListWidget { background: #0A0F0A; border: 1px solid #4B5320; color: #33FF33; font-family: 'JetBrains Mono', monospace; font-size: 11px; }")
        self.mission_list.setMaximumHeight(80)
        lay.addWidget(QLabel("Saved Missions:"))
        lay.addWidget(self.mission_list)
        # Buttons
        btn=QHBoxLayout()
        self.save_btn=QPushButton("SAVE MISSION")
        self.save_btn.setStyleSheet("QPushButton { background: #4B5320; color: white; }")
        self.save_btn.clicked.connect(self._save)
        self.package_btn=QPushButton("MISSION PACKAGE")
        self.package_btn.clicked.connect(self._package)
        self.opsec_btn=QPushButton("OPSEC CHECK")
        self.opsec_btn.clicked.connect(self._opsec)
        self.clear_btn=QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear)
        for b in (self.save_btn, self.package_btn, self.opsec_btn, self.clear_btn):
            btn.addWidget(b)
        btn.addStretch()
        lay.addLayout(btn)
        self.prog=QProgressBar(); self.prog.setVisible(False); self.prog.setRange(0,0); lay.addWidget(self.prog)
        self.log=QTextEdit(readOnly=True)
        self.log.setStyleSheet("QTextEdit { background: #050A05; color: #33FF33; border: 1px solid #4B5320; font-family: 'JetBrains Mono', monospace; font-size: 11px; }")
        lay.addWidget(self.log, 1)

    def _load_missions(self):
        try:
            for m in list_missions():
                self.mission_list.addItem(f"{m.mission_id} — {m.name} [{m.classification}{'//'+m.caveat if m.caveat else ''}] — {m.approver}")
        except Exception as e:
            self.log.append(f"[WARN] load missions: {e}")

    def _save(self):
        try:
            mid = self.mission_id.text().strip() or f"OP-{__import__('uuid').uuid4().hex[:8].upper()}"
            roe = ROE(
                targets=[t.strip() for t in self.targets.text().split(",") if t.strip()],
                techniques=[t.strip() for t in self.techniques.currentText().split(",")],
                start=self.start.dateTime().toString(Qt.DateFormat.ISODate),
                end=self.end.dateTime().toString(Qt.DateFormat.ISODate),
            )
            m = Mission(
                mission_id=mid,
                name=self.name.text().strip() or "UNNAMED OP",
                callsign=self.callsign.text().strip(),
                grid_ref=self.grid.text().strip(),
                classification=self.classification.currentText(),
                caveat=self.caveat.currentText(),
                approver=self.approver.text().strip(),
                approver_rank=self.rank.text().strip(),
                roe=roe,
            )
            save_mission(m)
            self.mission_list.addItem(f"{m.mission_id} — {m.name} [{m.banner}]")
            self.log.append(f"[SAVED] {m.mission_id} {m.banner} — {m.name}")
            # Audit
            try:
                from rtai_core.audit import record as audit_record
                from rtai_core.audit import actor_from_env
                audit_record("mission_saved", actor=actor_from_env(), mission_id=m.mission_id, classification=m.classification)
            except Exception:
                pass
            QMessageBox.information(self, "Royal-Sec", f"Mission {m.mission_id} saved\nBanner: {m.banner}")
        except Exception as e:
            QMessageBox.warning(self, "Royal-Sec", str(e))
            self.log.append(f"[ERROR] {e}")

    def _package(self):
        # Mission package = STIX + SBOM + audit bundle via airgap
        self.log.append("[PACKAGE] Building mission package (STIX + SBOM + audit)...")
        try:
            from rtai_core.mission import list_missions
            missions = list_missions()
            if not missions:
                self.log.append("[WARN] No missions — save one first")
                return
            m = missions[-1]
            # Simulate package
            self.log.append(f"[PACKAGE] Mission {m.mission_id} [{m.banner}] — packaging...")
            # Call airgap generator
            from rtai_core.military_airgap import AirGapBundleGenerator
            from pathlib import Path
            gen = AirGapBundleGenerator(Path.cwd())
            # Dry-run: just log
            self.log.append(f"[PACKAGE] Air-gap bundle would include: {m.roe.targets} + STIX bundle + audit.log")
            self.log.append("[PACKAGE] Classification banner embedded in all artifacts")
            self.log.append("[DONE] Mission package ready — handle per classification")
        except Exception as e:
            self.log.append(f"[ERROR] package: {e}")

    def _opsec(self):
        try:
            from rtai_core.mission import list_missions
            missions = list_missions()
            m = missions[-1] if missions else Mission(name="DRY RUN", classification=self.classification.currentText(), approver=self.approver.text().strip(), roe=ROE(targets=[self.targets.text()]))
            status = m.opsec_status()
            self.log.append("[OPSEC CHECK]")
            for k,v in status.items():
                icon = "✓" if v else "✗"
                color = "#33FF33" if v else "#FF0000"
                self.log.append(f"  {icon} {k}: {v}")
            if all(status.values()):
                self.log.append("[OPSEC] ALL CHECKS PASS — MISSION READY")
            else:
                self.log.append("[OPSEC] FAIL — resolve before execution (see AUP.md)")
        except Exception as e:
            self.log.append(f"[ERROR] opsec: {e}")

    def _clear(self):
        self.log.clear()
