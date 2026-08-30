"""Phish GUI - Royal-Sec branded."""
import sys
from pathlib import Path
try:
    from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox, QComboBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox, QComboBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar
    from PyQt6.QtGui import QFont
from rtai_core.gui.base import WorkerThread

class PhishGUI(QWidget):  # type: ignore
    def __init__(self):
        super().__init__()
        self.worker=None
        self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(12)
        hdr=QLabel("Phishing Simulator  —  Authorized awareness training")
        hdr.setFont(QFont("Segoe UI",11,QFont.Weight.Bold)); hdr.setStyleSheet("color:#0A1931;")
        lay.addWidget(hdr)
        g1=QGroupBox("Campaign"); f1=QFormLayout(g1)
        self.config=QLineEdit(placeholderText="samples/campaign.example.json")
        self.template=QComboBox(); self.template.addItems(["password_expiry","hr_bonus_letter","invoice_attachment","package_delivery","all"])
        self.validate=QCheckBox("Validate config only")
        f1.addRow("Config:", self.config); f1.addRow("Template:", self.template); f1.addRow("", self.validate)
        lay.addWidget(g1)
        btn=QHBoxLayout()
        self.run_btn=QPushButton("Generate Campaign"); self.run_btn.setStyleSheet("QPushButton { background:#0A1931; color:white; padding:10px 22px; border-radius:6px; font-weight:bold; }")
        self.run_btn.clicked.connect(self._run)
        self.stop_btn=QPushButton("Stop"); self.stop_btn.setEnabled(False); self.stop_btn.clicked.connect(self._stop)
        self.clear_btn=QPushButton("Clear"); self.clear_btn.clicked.connect(lambda: self.log.clear())
        btn.addWidget(self.run_btn); btn.addWidget(self.stop_btn); btn.addWidget(self.clear_btn); btn.addStretch()
        lay.addLayout(btn)
        self.prog=QProgressBar(); self.prog.setVisible(False); self.prog.setRange(0,0); lay.addWidget(self.prog)
        self.log=QTextEdit(readOnly=True); self.log.setStyleSheet("QTextEdit { background:#0F172A; color:#E2E8F0; border-radius:6px; padding:8px; font-family: Consolas; }")
        lay.addWidget(self.log,1)
    def _run(self):
        self.run_btn.setEnabled(False); self.stop_btn.setEnabled(True); self.prog.setVisible(True)
        cmd=[sys.executable,"-m","rtai_core.cli_app","phish","--config", self.config.text().strip() or "samples/campaign.example.json","--template", self.template.currentText()]
        if self.validate.isChecked(): cmd.append("--validate-config-only")
        self.log.append(f"[ROYAL-SEC] Generating {self.template.currentText()} campaign ...\n")
        self.worker=WorkerThread(cmd, cwd=str(Path.cwd()))
        self.worker.output_signal.connect(lambda s: (self.log.append(s), self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())))
        self.worker.finished_signal.connect(self._done); self.worker.error_signal.connect(lambda e: self.log.append(f"[ERROR] {e}")); self.worker.start()
    def _stop(self):
        if self.worker: self.worker.stop(); self.worker.wait(1500)
        self.run_btn.setEnabled(True); self.stop_btn.setEnabled(False); self.prog.setVisible(False); self.log.append("[STOPPED]\n")
    def _done(self, code):
        self.worker=None; self.run_btn.setEnabled(True); self.stop_btn.setEnabled(False); self.prog.setVisible(False); self.log.append(f"\n{'[DONE]' if code==0 else f'[EXIT {code}]'}\n")
