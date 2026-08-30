"""Recon Agent GUI - Royal-Sec branded passive OSINT."""
import sys, re
from pathlib import Path
try:
    from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox, QComboBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QMessageBox
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox, QComboBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QMessageBox
    from PyQt6.QtGui import QFont
from rtai_core.gui.base import WorkerThread

class ReconGUI(QWidget):  # type: ignore
    def __init__(self):
        super().__init__()
        self.worker = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16,16,16,16)
        lay.setSpacing(12)
        hdr = QLabel("Recon Agent  —  Passive OSINT + LLM attack-surface analysis")
        hdr.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        hdr.setStyleSheet("color: #0A1931;")
        lay.addWidget(hdr)

        g1 = QGroupBox("Target")
        f1 = QFormLayout(g1)
        self.target = QLineEdit(placeholderText="example.com")
        self.http = QCheckBox("Include HTTP fingerprinting (light active check)")
        f1.addRow("Domain:", self.target)
        f1.addRow("", self.http)
        lay.addWidget(g1)

        g2 = QGroupBox("LLM Settings")
        f2 = QFormLayout(g2)
        self.provider = QComboBox()
        self.provider.addItems(["ollama","openai","anthropic"])
        self.model = QLineEdit(placeholderText="llama3.1 / gpt-4o-mini (leave empty for default)")
        self.api_key = QLineEdit(placeholderText="API key (uses env var if empty)")
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        f2.addRow("Provider:", self.provider)
        f2.addRow("Model:", self.model)
        f2.addRow("API Key:", self.api_key)
        lay.addWidget(g2)

        g3 = QGroupBox("Output")
        f3 = QFormLayout(g3)
        self.out = QLineEdit(placeholderText="recon_report.md")
        self.json_out = QLineEdit(placeholderText="recon_findings.json (machine-readable)")
        f3.addRow("Report:", self.out)
        f3.addRow("JSON:", self.json_out)
        lay.addWidget(g3)

        btn = QHBoxLayout()
        self.run_btn = QPushButton("Start Recon")
        self.run_btn.setStyleSheet("QPushButton { background:#0A1931; color:white; padding:10px 22px; border-radius:6px; font-weight:bold; } QPushButton:hover { background:#132A4C; }")
        self.run_btn.clicked.connect(self._run)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(lambda: self.log.clear())
        btn.addWidget(self.run_btn); btn.addWidget(self.stop_btn); btn.addWidget(self.clear_btn); btn.addStretch()
        lay.addLayout(btn)

        self.prog = QProgressBar(); self.prog.setVisible(False); self.prog.setRange(0,0)
        lay.addWidget(self.prog)
        self.log = QTextEdit(readOnly=True)
        self.log.setStyleSheet("QTextEdit { background:#0F172A; color:#E2E8F0; border:1px solid #1E293B; border-radius:6px; padding:8px; font-family: Consolas; }")
        lay.addWidget(self.log, 1)

    def _valid(self, d):
        return bool(re.fullmatch(r"(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}", d.strip().lower()))

    def _run(self):
        t = self.target.text().strip()
        if not t: QMessageBox.warning(self, "Royal-Sec", "Target domain is required"); return
        if not self._valid(t): QMessageBox.warning(self, "Royal-Sec", "Invalid domain format"); return
        self.run_btn.setEnabled(False); self.stop_btn.setEnabled(True); self.prog.setVisible(True); self.log.append(f"\n[ROYAL-SEC] Starting recon for {t} ...\n")
        cmd = [sys.executable, "-m", "rtai_core.cli_app", "recon", "--target", t]
        if self.http.isChecked(): cmd.append("--include-http")
        if self.provider.currentText(): cmd += ["--provider", self.provider.currentText()]
        if self.model.text().strip(): cmd += ["--model", self.model.text().strip()]
        if self.api_key.text().strip(): cmd += ["--api-key", self.api_key.text().strip()]
        if self.out.text().strip(): cmd += ["--out", self.out.text().strip()]
        if self.json_out.text().strip(): cmd += ["--json-out", self.json_out.text().strip()]
        self.worker = WorkerThread(cmd, cwd=str(Path.cwd()))
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
