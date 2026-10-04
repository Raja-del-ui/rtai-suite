"""Killchain Orchestrator GUI — Full 7-phase run (lab-only)."""
import sys
from pathlib import Path
try:
    from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QCheckBox, QComboBox
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QCheckBox, QComboBox
    from PyQt6.QtGui import QFont
from rtai_core.gui.base import WorkerThread

class KillchainGUI(QWidget):  # Royal-Sec
    def __init__(self):
        super().__init__()
        self.worker=None
        self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(12,12,12,12); lay.setSpacing(10)
        hdr=QLabel("KILLCHAIN ORCHESTRATOR  —  01 Recon → 06 Forge → 03 Phish → 02 Fuzz → 04 C2 → 07 Persist → 08 APT → 05 Report")
        hdr.setFont(QFont("Share Tech Mono", 9, QFont.Weight.Bold)); hdr.setStyleSheet("color: #C2B280;")
        hdr.setWordWrap(True)
        lay.addWidget(hdr)
        g1=QGroupBox("Orchestration Target & Mission")
        f1 = QFormLayout(g1)
        f1.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f1.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.target=QLineEdit(placeholderText="127.0.0.1  or  lab.local"); self.target.setText("127.0.0.1")
        self.mission=QLineEdit(placeholderText="missions/OP-XXXX.json (leave empty for latest)")
        self.classification=QComboBox(); self.classification.addItems(["CUI","UNCLASS","CONFIDENTIAL","SECRET","TOP_SECRET"]); self.classification.setCurrentText("CUI")
        f1.addRow("Target (lab-only):", self.target)
        f1.addRow("Mission JSON:", self.mission)
        f1.addRow("Classification:", self.classification)
        lay.addWidget(g1)
        g2=QGroupBox("Options")
        f2 = QFormLayout(g2)
        f2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f2.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.dry=QCheckBox("Dry-run (no side effects, via --help)")
        self.dry.setChecked(True)
        f2.addRow("", self.dry)
        lay.addWidget(g2)
        # Phase legend
        legend=QLabel("Phases: 01-recon (passive) → 06-weaponize (EICAR) → 03-phish (validate) → 02-fuzz (list-payloads) → 04-c2 (stats) → 07-persist (sim) → 08-apt (sim) → 05-report (STIX) — all lab-only, audit-chained.")
        legend.setStyleSheet("color: #8A9A6A; font-size: 8px;")
        legend.setWordWrap(True)
        lay.addWidget(legend)
        btn=QHBoxLayout()
        self.run_btn=QPushButton("LAUNCH KILLCHAIN")
        self.run_btn.setStyleSheet("QPushButton { background: #C8102E; color: white; padding: 10px 18px; font-weight: bold; border-radius: 3px; } QPushButton:hover { background: #A00D24; }")
        self.run_btn.clicked.connect(self._run)
        self.list_btn=QPushButton("LIST PHASES")
        self.list_btn.clicked.connect(self._list)
        self.stop_btn=QPushButton("Stop"); self.stop_btn.setEnabled(False); self.stop_btn.clicked.connect(self._stop)
        self.clear_btn=QPushButton("Clear"); self.clear_btn.clicked.connect(lambda: self.log.clear())
        for b in (self.run_btn, self.list_btn, self.stop_btn, self.clear_btn):
            btn.addWidget(b)
        btn.addStretch()
        lay.addLayout(btn)
        self.prog=QProgressBar(); self.prog.setVisible(False); self.prog.setRange(0,0); lay.addWidget(self.prog)
        self.log=QTextEdit(readOnly=True)
        self.log.setStyleSheet("QTextEdit { background: #050A05; color: #33FF33; border: 1px solid #4B5320; font-family: 'JetBrains Mono', monospace; font-size: 11px; }")
        self.log.append("[KILLCHAIN] Ready — select target (lab-only) and launch. Requires KILLCHAIN_ATTESTED HMAC or interactive I AM AUTHORIZED.")
        self.log.append("[KILLCHAIN] Tip: Create mission first: rtai mission --create --name \"MANTICORE SHIELD\" --classification CUI --targets 127.0.0.1")
        lay.addWidget(self.log, 1)
    def _list(self):
        cmd=[sys.executable, "-m", "rtai_core.cli_app", "killchain", "--list-phases"]
        self.log.append("[KILLCHAIN] Listing phases ...\n")
        self.worker=WorkerThread(cmd, cwd=str(Path.cwd()))
        self.worker.output_signal.connect(lambda s: self.log.append(s))
        self.worker.finished_signal.connect(self._done)
        self.worker.start()
    def _run(self):
        t=self.target.text().strip() or "127.0.0.1"
        self.run_btn.setEnabled(False); self.stop_btn.setEnabled(True); self.prog.setVisible(True)
        cmd=[sys.executable, "-m", "rtai_core.cli_app", "killchain", "--target", t, "--yes"]
        if self.mission.text().strip():
            cmd+=["--mission", self.mission.text().strip()]
        if self.dry.isChecked():
            cmd.append("--dry-run")
        self.log.append(f"[KILLCHAIN] Launching full chain for {t} (dry_run={self.dry.isChecked()}) ...\n")
        self.worker=WorkerThread(cmd, cwd=str(Path.cwd()))
        self.worker.output_signal.connect(lambda s: (self.log.append(s), self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())))
        self.worker.finished_signal.connect(self._done)
        self.worker.error_signal.connect(lambda e: self.log.append(f"[ERROR] {e}"))
        self.worker.start()
    def _stop(self):
        if self.worker: self.worker.stop(); self.worker.wait(1500)
        self.run_btn.setEnabled(True); self.stop_btn.setEnabled(False); self.prog.setVisible(False); self.log.append("[STOPPED]\n")
    def _done(self, code):
        self.worker=None; self.run_btn.setEnabled(True); self.stop_btn.setEnabled(False); self.prog.setVisible(False)
        self.log.append(f"\n{'[DONE]' if code==0 else f'[EXIT {code}]'}\n")
