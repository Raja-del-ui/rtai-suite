"""APT Lab GUI — Discovery / Lateral / Collection / Exfil / Impact (lab-only)."""
import sys
from pathlib import Path
try:
    from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QCheckBox
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QCheckBox
    from PyQt6.QtGui import QFont
from rtai_core.gui.base import WorkerThread

class AptGUI(QWidget):  # Royal-Sec
    def __init__(self):
        super().__init__()
        self.worker=None
        self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(12,12,12,12); lay.setSpacing(10)
        hdr=QLabel("APT LAB  —  Discovery • Lateral • Collection • Exfil • Impact (lab-only, report-only)")
        hdr.setFont(QFont("Share Tech Mono", 10, QFont.Weight.Bold)); hdr.setStyleSheet("color: #C2B280;")
        lay.addWidget(hdr)
        g1=QGroupBox("Lab C2 Target")
        f1=QFormLayout(g1)
        self.host=QLineEdit(placeholderText="127.0.0.1"); self.host.setText("127.0.0.1")
        self.port=QSpinBox(); self.port.setRange(1,65535); self.port.setValue(8080)
        self.jitter=QDoubleSpinBox(); self.jitter.setRange(0.0,1.0); self.jitter.setValue(0.35); self.jitter.setSingleStep(0.05)
        f1.addRow("Host:", self.host); f1.addRow("Port:", self.port); f1.addRow("Jitter:", self.jitter)
        lay.addWidget(g1)
        g2=QGroupBox("Telemetry")
        f2=QFormLayout(g2)
        self.logpath=QLineEdit(placeholderText="08-discovery-lateral-exfil-lab/apt_telemetry.jsonl")
        self.findings=QLineEdit(placeholderText="08-discovery-lateral-exfil-lab/apt_findings.json")
        self.dummy=QSpinBox(); self.dummy.setRange(1,10); self.dummy.setValue(3)
        self.exfil=QSpinBox(); self.exfil.setRange(1,5); self.exfil.setValue(2)
        f2.addRow("Log:", self.logpath); f2.addRow("Findings:", self.findings)
        f2.addRow("Dummy files:", self.dummy); f2.addRow("Exfil POSTs:", self.exfil)
        lay.addWidget(g2)
        g3=QGroupBox("Integration")
        f3=QFormLayout(g3)
        self.db=QLineEdit(placeholderText="08-discovery-lateral-exfil-lab/apt_events.db (optional SQLite)")
        f3.addRow("DB:", self.db)
        lay.addWidget(g3)
        btn=QHBoxLayout()
        self.run_btn=QPushButton("RUN APT LAB")
        self.run_btn.setStyleSheet("QPushButton { background: #4B5320; color: white; padding: 8px 16px; font-weight: bold; border-radius: 3px; }")
        self.run_btn.clicked.connect(self._run)
        self.dry_btn=QPushButton("DRY-RUN")
        self.dry_btn.clicked.connect(self._dry)
        self.stop_btn=QPushButton("Stop"); self.stop_btn.setEnabled(False); self.stop_btn.clicked.connect(self._stop)
        self.clear_btn=QPushButton("Clear"); self.clear_btn.clicked.connect(lambda: self.log.clear())
        for b in (self.run_btn, self.dry_btn, self.stop_btn, self.clear_btn):
            btn.addWidget(b)
        btn.addStretch()
        lay.addLayout(btn)
        self.prog=QProgressBar(); self.prog.setVisible(False); self.prog.setRange(0,0); lay.addWidget(self.prog)
        self.log=QTextEdit(readOnly=True)
        self.log.setStyleSheet("QTextEdit { background: #050A05; color: #33FF33; border: 1px solid #4B5320; font-family: 'JetBrains Mono', monospace; font-size: 11px; }")
        self.log.append("[APT] Ready — discovery (redacted) → lateral simulated → exfil to 127.0.0.1 + DNS/Cloud covert sim.")
        lay.addWidget(self.log, 1)
    def _base_cmd(self):
        cmd=[sys.executable, "-m", "rtai_core.cli_app", "apt", "--host", self.host.text().strip() or "127.0.0.1", "--port", str(self.port.value()), "--jitter", str(self.jitter.value())]
        if self.logpath.text().strip():
            cmd+=["--log", self.logpath.text().strip()]
        if self.findings.text().strip():
            cmd+=["--findings", self.findings.text().strip()]
        if self.dummy.value()!=3:
            cmd+=["--dummy-files", str(self.dummy.value())]
        if self.exfil.value()!=2:
            cmd+=["--exfil-count", str(self.exfil.value())]
        if self.db.text().strip():
            cmd+=["--db", self.db.text().strip()]
        cmd.append("--yes")
        return cmd
    def _run(self):
        self.run_btn.setEnabled(False); self.dry_btn.setEnabled(False); self.stop_btn.setEnabled(True); self.prog.setVisible(True)
        cmd=self._base_cmd()
        self.log.append(f"[APT] Running lab simulation on {self.host.text().strip()}:{self.port.value()} ...\n")
        self.worker=WorkerThread(cmd, cwd=str(Path.cwd()))
        self.worker.output_signal.connect(lambda s: (self.log.append(s), self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())))
        self.worker.finished_signal.connect(self._done)
        self.worker.error_signal.connect(lambda e: self.log.append(f"[ERROR] {e}"))
        self.worker.start()
    def _dry(self):
        cmd=self._base_cmd() + ["--dry-run"]
        self.log.append("[APT] Dry-run ...\n")
        self.worker=WorkerThread(cmd, cwd=str(Path.cwd()))
        self.worker.output_signal.connect(lambda s: self.log.append(s))
        self.worker.finished_signal.connect(self._done)
        self.worker.start()
    def _stop(self):
        if self.worker: self.worker.stop(); self.worker.wait(1500)
        self.run_btn.setEnabled(True); self.dry_btn.setEnabled(True); self.stop_btn.setEnabled(False); self.prog.setVisible(False); self.log.append("[STOPPED]\n")
    def _done(self, code):
        self.worker=None; self.run_btn.setEnabled(True); self.dry_btn.setEnabled(True); self.stop_btn.setEnabled(False); self.prog.setVisible(False)
        self.log.append(f"\n{'[DONE]' if code==0 else f'[EXIT {code}]'}\n")
