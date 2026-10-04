"""Persistence Privesc Lab GUI — simulated registry/cron/service/WMI (log-only)."""
import sys
from pathlib import Path
try:
    from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QCheckBox
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QCheckBox
    from PyQt6.QtGui import QFont
from rtai_core.gui.base import WorkerThread

class PersistGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.worker=None
        self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(12,12,12,12); lay.setSpacing(10)
        hdr=QLabel("PERSISTENCE / PRIVESC LAB  —  Simulated (lab_only:true, never host write)")
        hdr.setFont(QFont("Share Tech Mono", 10, QFont.Weight.Bold)); hdr.setStyleSheet("color: #C2B280;")
        lay.addWidget(hdr)
        g1=QGroupBox("Lab Target")
        f1 = QFormLayout(g1)
        f1.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f1.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.host=QLineEdit(placeholderText="127.0.0.1"); self.host.setText("127.0.0.1")
        self.technique=QComboBox(); self.technique.addItems(["all","registry_run","scheduled_task","service","wmi","startup_folder"])
        self.logpath=QLineEdit(placeholderText="07-persistence-privesc-lab/persistence.jsonl")
        f1.addRow("Host (lab-only):", self.host)
        f1.addRow("Technique:", self.technique)
        f1.addRow("Log:", self.logpath)
        lay.addWidget(g1)
        g2=QGroupBox("Options")
        f2 = QFormLayout(g2)
        f2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f2.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.dry=QCheckBox("Dry-run (preview, no file written)")
        self.skip_priv=QCheckBox("Skip privesc checks")
        self.skip_cred=QCheckBox("Skip credential checks")
        f2.addRow("", self.dry); f2.addRow("", self.skip_priv); f2.addRow("", self.skip_cred)
        lay.addWidget(g2)
        btn=QHBoxLayout()
        self.run_btn=QPushButton("SIMULATE")
        self.run_btn.setStyleSheet("QPushButton { background: #4B5320; color: white; padding: 8px 16px; font-weight: bold; border-radius: 3px; }")
        self.run_btn.clicked.connect(self._run)
        self.stop_btn=QPushButton("Stop"); self.stop_btn.setEnabled(False); self.stop_btn.clicked.connect(self._stop)
        self.clear_btn=QPushButton("Clear"); self.clear_btn.clicked.connect(lambda: self.log.clear())
        for b in (self.run_btn, self.stop_btn, self.clear_btn):
            btn.addWidget(b)
        btn.addStretch()
        lay.addLayout(btn)
        self.prog=QProgressBar(); self.prog.setVisible(False); self.prog.setRange(0,0); lay.addWidget(self.prog)
        self.log=QTextEdit(readOnly=True)
        self.log.setStyleSheet("QTextEdit { background: #050A05; color: #33FF33; border: 1px solid #4B5320; font-family: 'JetBrains Mono', monospace; font-size: 11px; }")
        self.log.append("[PERSIST] Ready — select technique (simulated log-only).")
        lay.addWidget(self.log, 1)
    def _run(self):
        if not self.host.text().strip():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Royal-Sec", "Host required")
            return
        self.run_btn.setEnabled(False); self.stop_btn.setEnabled(True); self.prog.setVisible(True)
        cmd=[sys.executable, "-m", "rtai_core.cli_app", "persist", "--host", self.host.text().strip(), "--technique", self.technique.currentText()]
        if self.logpath.text().strip():
            cmd+=["--log", self.logpath.text().strip()]
        if self.dry.isChecked():
            cmd.append("--dry-run")
        if self.skip_priv.isChecked():
            cmd.append("--skip-privesc")
        if self.skip_cred.isChecked():
            cmd.append("--skip-creds")
        cmd.append("--yes")
        self.log.append(f"[PERSIST] Simulating {self.technique.currentText()} on {self.host.text().strip()} ...\n")
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
