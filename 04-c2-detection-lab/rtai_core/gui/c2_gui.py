"""C2 Lab GUI - Royal-Sec branded."""
import sys
from pathlib import Path
try:
    from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QSpinBox, QComboBox, QCheckBox
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QSpinBox, QComboBox, QCheckBox
    from PyQt6.QtGui import QFont
from rtai_core.gui.base import WorkerThread

class C2LabGUI(QWidget):  # type: ignore  # Royal-Sec Tactical
    """C2LabGUI — Royal-Sec branded (military HUD)."""
    def __init__(self):
        super().__init__()
        self.worker=None
        self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(12)
        hdr=QLabel("C2 Detection Lab  —  Beacon simulator (fully offline)")
        hdr.setFont(QFont("Share Tech Mono",11,QFont.Weight.Bold)); hdr.setStyleSheet("color: #C2B280; letter-spacing: 0.8px;")
        lay.addWidget(hdr)
        g1=QGroupBox("Listener"); f1 = QFormLayout(g1)
        f1.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f1.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.l_host=QLineEdit(placeholderText="127.0.0.1"); self.l_port=QSpinBox(); self.l_port.setRange(1024,65535); self.l_port.setValue(8080)
        self.l_log=QLineEdit(placeholderText="beacons.jsonl")
        f1.addRow("Host:", self.l_host); f1.addRow("Port:", self.l_port); f1.addRow("Log:", self.l_log)
        lay.addWidget(g1)
        g2=QGroupBox("Beacon"); f2 = QFormLayout(g2)
        f2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f2.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.b_host=QLineEdit(placeholderText="127.0.0.1"); self.b_port=QSpinBox(); self.b_port.setRange(1024,65535); self.b_port.setValue(8080)
        self.b_preset=QComboBox(); self.b_preset.addItems(["regular","low_slow","bursty","office_hours"])
        self.b_count=QSpinBox(); self.b_count.setRange(1,100); self.b_count.setValue(8)
        f2.addRow("Host:", self.b_host); f2.addRow("Port:", self.b_port); f2.addRow("Preset:", self.b_preset); f2.addRow("Count:", self.b_count)
        lay.addWidget(g2)
        g3=QGroupBox("Analysis"); f3 = QFormLayout(g3)
        f3.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f3.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.a_log=QLineEdit(placeholderText="beacons.jsonl")
        self.a_only=QCheckBox("Stats only (no LLM)"); self.a_provider=QComboBox(); self.a_provider.addItems(["ollama","openai","anthropic","xai","grok","gemini","google"]); self.a_provider.setEnabled(not self.a_only.isChecked()); self.a_only.toggled.connect(lambda v: self.a_provider.setEnabled(not v))
        f3.addRow("Log:", self.a_log); f3.addRow("LLM Provider:", self.a_provider); f3.addRow("", self.a_only)
        lay.addWidget(g3)
        btn=QHBoxLayout()
        self.btn_listen=QPushButton("Start Listener"); self.btn_beacon=QPushButton("Start Beacon"); self.btn_analyze=QPushButton("Analyze")
        for b in (self.btn_listen, self.btn_beacon, self.btn_analyze):
            b.setStyleSheet("QPushButton { background:#4B5320; color:white; padding:8px 14px; border-radius:6px; font-weight:600; }")
        self.btn_listen.clicked.connect(self._listen); self.btn_beacon.clicked.connect(self._beacon); self.btn_analyze.clicked.connect(self._analyze)
        self.stop_btn=QPushButton("Stop"); self.stop_btn.setEnabled(False); self.stop_btn.clicked.connect(self._stop)
        self.clear_btn=QPushButton("Clear"); self.clear_btn.clicked.connect(lambda: self.log.clear())
        for b in (self.btn_listen, self.btn_beacon, self.btn_analyze, self.stop_btn, self.clear_btn): btn.addWidget(b)
        btn.addStretch(); lay.addLayout(btn)
        self.prog=QProgressBar(); self.prog.setVisible(False); self.prog.setRange(0,0); lay.addWidget(self.prog)
        self.log=QTextEdit(readOnly=True); self.log.setStyleSheet("QTextEdit { background:#050A05; color:#33FF33; border:1px solid #4B5320; font-family: 'JetBrains Mono', monospace; font-size: 11px; }")
        lay.addWidget(self.log,1)
    def _run(self, cmd):
        self.btn_listen.setEnabled(False); self.btn_beacon.setEnabled(False); self.btn_analyze.setEnabled(False); self.stop_btn.setEnabled(True); self.prog.setVisible(True)
        self.worker=WorkerThread(cmd, cwd=str(Path.cwd()))
        self.worker.output_signal.connect(lambda s: (self.log.append(s), self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())))
        self.worker.finished_signal.connect(self._done); self.worker.error_signal.connect(lambda e: self.log.append(f"[ERROR] {e}")); self.worker.start()
    def _listen(self):
        self.log.append("[TACTICAL] Starting listener ...\n")
        cmd=[sys.executable,"-m","rtai_core.cli_app","c2-listen","--host",self.l_host.text().strip() or "127.0.0.1","--port",str(self.l_port.value())]
        if self.l_log.text().strip(): cmd+=["--log", self.l_log.text().strip()]
        self._run(cmd)
    def _beacon(self):
        self.log.append("[TACTICAL] Starting beacon ...\n")
        cmd=[sys.executable,"-m","rtai_core.cli_app","c2-beacon","--host",self.b_host.text().strip() or "127.0.0.1","--port",str(self.b_port.value()),"--preset",self.b_preset.currentText(),"--count",str(self.b_count.value())]
        self._run(cmd)
    def _analyze(self):
        self.log.append("[TACTICAL] Analyzing ...\n")
        cmd=[sys.executable,"-m","rtai_core.cli_app","c2-analyze","--log",self.a_log.text().strip() or "beacons.jsonl"]
        if self.a_only.isChecked(): cmd.append("--stats-only")
        self._run(cmd)
    def _stop(self):
        if self.worker: self.worker.stop(); self.worker.wait(1500)
        for b in (self.btn_listen,self.btn_beacon,self.btn_analyze): b.setEnabled(True)
        self.stop_btn.setEnabled(False); self.prog.setVisible(False); self.log.append("[STOPPED]\n")
    def _done(self, code):
        self.worker=None
        for b in (self.btn_listen,self.btn_beacon,self.btn_analyze): b.setEnabled(True)
        self.stop_btn.setEnabled(False); self.prog.setVisible(False); self.log.append(f"\n{'[DONE]' if code==0 else f'[EXIT {code}]'}\n")
