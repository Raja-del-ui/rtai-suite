"""Report GUI - Royal-Sec branded."""
import sys
from pathlib import Path
try:
    from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QComboBox, QCheckBox
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QComboBox, QCheckBox
    from PyQt6.QtGui import QFont
from rtai_core.gui.base import WorkerThread

class ReportGUI(QWidget):  # type: ignore
    def __init__(self):
        super().__init__()
        self.worker=None
        self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(12)
        hdr=QLabel("Report Copilot  —  AI-assisted pentest reports")
        hdr.setFont(QFont("Share Tech Mono",11,QFont.Weight.Bold)); hdr.setStyleSheet("color: #C2B280; letter-spacing: 0.8px;")
        lay.addWidget(hdr)
        g1=QGroupBox("Inputs"); f1 = QFormLayout(g1)
        f1.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f1.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.nmap=QLineEdit(placeholderText="samples/sample-nmap.xml")
        self.nuclei=QLineEdit(placeholderText="samples/sample-nuclei.jsonl")
        self.nessus=QLineEdit(placeholderText="samples/sample-scan.nessus (optional)")
        self.company=QLineEdit(placeholderText="Acme Corp")
        f1.addRow("Nmap XML:", self.nmap); f1.addRow("Nuclei JSONL:", self.nuclei); f1.addRow("Nessus:", self.nessus); f1.addRow("Company:", self.company)
        lay.addWidget(g1)
        g2=QGroupBox("Options"); f2 = QFormLayout(g2)
        f2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f2.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.fmt=QComboBox(); self.fmt.addItems(["markdown","html","json"])
        self.no_llm=QCheckBox("Skip LLM (--no-llm)")
        self.out=QLineEdit(placeholderText="report.md / report.html")
        f2.addRow("Format:", self.fmt); f2.addRow("", self.no_llm); f2.addRow("Output:", self.out)
        lay.addWidget(g2)
        btn=QHBoxLayout()
        self.run_btn=QPushButton("Generate Report"); self.run_btn.setStyleSheet("QPushButton { background:#4B5320; color:white; padding:10px 22px; border-radius:6px; font-weight:bold; }")
        self.run_btn.clicked.connect(self._run)
        self.stop_btn=QPushButton("Stop"); self.stop_btn.setEnabled(False); self.stop_btn.clicked.connect(self._stop)
        self.clear_btn=QPushButton("Clear"); self.clear_btn.clicked.connect(lambda: self.log.clear())
        btn.addWidget(self.run_btn); btn.addWidget(self.stop_btn); btn.addWidget(self.clear_btn); btn.addStretch()
        lay.addLayout(btn)
        self.prog=QProgressBar(); self.prog.setVisible(False); self.prog.setRange(0,0); lay.addWidget(self.prog)
        self.log=QTextEdit(readOnly=True); self.log.setStyleSheet("QTextEdit { background:#050A05; color:#33FF33; border:1px solid #4B5320; color:#E2E8F0; border-radius:6px; padding:8px; font-family: Consolas; }")
        lay.addWidget(self.log,1)
    def _run(self):
        if not any([self.nmap.text().strip(), self.nuclei.text().strip(), self.nessus.text().strip()]):
            from PySide6.QtWidgets import QMessageBox
            try: QMessageBox.warning(self,"Royal-Sec","At least one input required")
            except: pass
            return
        self.run_btn.setEnabled(False); self.stop_btn.setEnabled(True); self.prog.setVisible(True)
        cmd=[sys.executable,"-m","rtai_core.cli_app","report","--company", self.company.text().strip() or "Acme Corp","--format", self.fmt.currentText()]
        if self.nmap.text().strip(): cmd+=["--nmap", self.nmap.text().strip()]
        if self.nuclei.text().strip(): cmd+=["--nuclei", self.nuclei.text().strip()]
        if self.nessus.text().strip(): cmd+=["--nessus", self.nessus.text().strip()]
        if self.no_llm.isChecked(): cmd.append("--no-llm")
        if self.out.text().strip(): cmd+=["--out", self.out.text().strip()]
        self.log.append(f"[TACTICAL] Generating {self.fmt.currentText()} report ...\n")
        self.worker=WorkerThread(cmd, cwd=str(Path.cwd()))
        self.worker.output_signal.connect(lambda s: (self.log.append(s), self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())))
        self.worker.finished_signal.connect(self._done); self.worker.error_signal.connect(lambda e: self.log.append(f"[ERROR] {e}")); self.worker.start()
    def _stop(self):
        if self.worker: self.worker.stop(); self.worker.wait(1500)
        self.run_btn.setEnabled(True); self.stop_btn.setEnabled(False); self.prog.setVisible(False); self.log.append("[STOPPED]\n")
    def _done(self, code):
        self.worker=None; self.run_btn.setEnabled(True); self.stop_btn.setEnabled(False); self.prog.setVisible(False); self.log.append(f"\n{'[DONE]' if code==0 else f'[EXIT {code}]'}\n")
