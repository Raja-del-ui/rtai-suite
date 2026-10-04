"""Fuzzer GUI - Royal-Sec branded."""
import sys
from pathlib import Path
try:
    from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox, QComboBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QSpinBox, QMessageBox
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox, QComboBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QSpinBox, QMessageBox
    from PyQt6.QtGui import QFont
from rtai_core.gui.base import WorkerThread

class FuzzerGUI(QWidget):  # type: ignore
    def __init__(self):
        super().__init__()
        self.worker=None
        self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(12)
        hdr=QLabel("Injection Fuzzer  —  Adaptive prompt-injection with judge & mutation")
        hdr.setFont(QFont("Share Tech Mono",11,QFont.Weight.Bold)); hdr.setStyleSheet("color: #C2B280; letter-spacing: 0.8px;")
        lay.addWidget(hdr)
        g1=QGroupBox("Target"); f1 = QFormLayout(g1)
        f1.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f1.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.url=QLineEdit(placeholderText="http://127.0.0.1:11434/v1")
        self.model=QLineEdit(placeholderText="llama3.1")
        self.system=QLineEdit(placeholderText="System prompt (defense) - optional")
        f1.addRow("Base URL:", self.url); f1.addRow("Model:", self.model); f1.addRow("Defense prompt:", self.system)
        lay.addWidget(g1)
        g2=QGroupBox("Options"); f2 = QFormLayout(g2)
        f2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f2.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.judge=QCheckBox("Enable LLM-as-judge"); self.judge_provider=QComboBox(); self.judge_provider.addItems(["ollama","openai","anthropic","xai","grok","gemini","google"]); self.judge_provider.setEnabled(False); self.judge.toggled.connect(lambda v: self.judge_provider.setEnabled(v)); self.adaptive=QSpinBox(); self.adaptive.setRange(0,5)
        self.concurrency=QSpinBox(); self.concurrency.setRange(1,16); self.concurrency.setValue(6)
        f2.addRow("", self.judge); f2.addRow("Judge provider:", self.judge_provider); f2.addRow("Adaptive rounds:", self.adaptive); f2.addRow("Concurrency:", self.concurrency)
        lay.addWidget(g2)
        g3=QGroupBox("Output"); f3 = QFormLayout(g3)
        f3.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f3.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.out=QLineEdit(placeholderText="injection_report.md")
        f3.addRow("Report:", self.out)
        lay.addWidget(g3)
        btn=QHBoxLayout()
        self.run_btn=QPushButton("Start Fuzzing"); self.run_btn.setStyleSheet("QPushButton { background:#4B5320; color:white; padding:10px 22px; border-radius:6px; font-weight:bold; }")
        self.run_btn.clicked.connect(self._run)
        self.stop_btn=QPushButton("Stop"); self.stop_btn.setEnabled(False); self.stop_btn.clicked.connect(self._stop)
        self.clear_btn=QPushButton("Clear"); self.clear_btn.clicked.connect(lambda: self.log.clear())
        btn.addWidget(self.run_btn); btn.addWidget(self.stop_btn); btn.addWidget(self.clear_btn); btn.addStretch()
        lay.addLayout(btn)
        self.prog=QProgressBar(); self.prog.setVisible(False); self.prog.setRange(0,0); lay.addWidget(self.prog)
        self.log=QTextEdit(readOnly=True); self.log.setStyleSheet("QTextEdit { background:#050A05; color:#33FF33; border:1px solid #4B5320; color:#E2E8F0; border-radius:6px; padding:8px; font-family: Consolas; }")
        lay.addWidget(self.log,1)
    def _run(self):
        if not self.url.text().strip(): QMessageBox.warning(self,"Royal-Sec","Base URL required"); return
        self.run_btn.setEnabled(False); self.stop_btn.setEnabled(True); self.prog.setVisible(True)
        cmd=[sys.executable,"-m","rtai_core.cli_app","fuzz","--url",self.url.text().strip(),"--model",self.model.text().strip() or "llama3.1"]
        if self.system.text().strip(): cmd+=["--system", self.system.text().strip()]
        if self.judge.isChecked():
            cmd.append("--judge")
            if self.judge_provider.currentText(): cmd+=["--judge-provider", self.judge_provider.currentText()]
        if self.adaptive.value()>0: cmd+=["--adaptive", str(self.adaptive.value())]
        cmd+=["--concurrency", str(self.concurrency.value())]
        if self.out.text().strip(): cmd+=["--out", self.out.text().strip()]
        self.log.append(f"[TACTICAL] Fuzzing {self.url.text().strip()} ...\n")
        self.worker=WorkerThread(cmd, cwd=str(Path.cwd()))
        self.worker.output_signal.connect(lambda s: (self.log.append(s), self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())))
        self.worker.finished_signal.connect(self._done); self.worker.error_signal.connect(lambda e: self.log.append(f"[ERROR] {e}")); self.worker.start()
    def _stop(self):
        if self.worker: self.worker.stop(); self.worker.wait(1500)
        self.run_btn.setEnabled(True); self.stop_btn.setEnabled(False); self.prog.setVisible(False); self.log.append("[STOPPED]\n")
    def _done(self, code):
        self.worker=None; self.run_btn.setEnabled(True); self.stop_btn.setEnabled(False); self.prog.setVisible(False); self.log.append(f"\n{'[DONE]' if code==0 else f'[EXIT {code}]'}\n")
