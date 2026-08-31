"""Weaponization Forge GUI — benign payload placeholders (EICAR)."""
import sys
from pathlib import Path
try:
    from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QMessageBox, QCheckBox
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QGroupBox, QFormLayout, QPushButton, QTextEdit, QProgressBar, QMessageBox, QCheckBox
    from PyQt6.QtGui import QFont
from rtai_core.gui.base import WorkerThread

class WeaponizeGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.worker=None
        self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(12,12,12,12); lay.setSpacing(10)
        hdr=QLabel("WEAPONIZATION FORGE  —  Benign EICAR placeholders only (lab-audited)")
        hdr.setFont(QFont("Share Tech Mono", 10, QFont.Weight.Bold)); hdr.setStyleSheet("color: #C2B280; letter-spacing: 0.8px;")
        lay.addWidget(hdr)
        info=QLabel("Generates watermarked macro/LNK/HTA/ISO/shellcode_stub (EICAR) — FORBIDDEN_SNIPPETS blocked, lab-only, audit-chained.")
        info.setStyleSheet("color: #8A9A6A; font-size: 9px;"); info.setWordWrap(True)
        lay.addWidget(info)
        g1=QGroupBox("Target & Payload")
        f1=QFormLayout(g1)
        self.target=QLineEdit(placeholderText="127.0.0.1  or  lab.local")
        self.payload=QComboBox(); self.payload.addItems(["document_macro","lnk_dropper","hta_artifact","iso_container","shellcode_stub"])
        self.out=QLineEdit(placeholderText="06-weaponization-forge/out (leave empty for default)")
        f1.addRow("Target (lab-only):", self.target)
        f1.addRow("Payload type:", self.payload)
        f1.addRow("Out dir:", self.out)
        lay.addWidget(g1)
        g2=QGroupBox("Options")
        f2=QFormLayout(g2)
        self.force=QCheckBox("Overwrite existing out/ files (--force)")
        f2.addRow("", self.force)
        lay.addWidget(g2)
        btn=QHBoxLayout()
        self.run_btn=QPushButton("FORGE")
        self.run_btn.setStyleSheet("QPushButton { background: #4B5320; color: white; padding: 8px 16px; font-weight: bold; border-radius: 3px; } QPushButton:hover { background: #5A6428; }")
        self.run_btn.clicked.connect(self._run)
        self.list_btn=QPushButton("LIST TEMPLATES")
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
        self.log.append("[FORGE] Ready — select payload type and target (lab-only).")
        lay.addWidget(self.log, 1)
    def _list(self):
        self.log.append("[FORGE] Listing templates ...")
        cmd=[sys.executable, "-m", "rtai_core.cli_app", "weaponize", "--list-templates"]
        self._spawn(cmd)
    def _run(self):
        t=self.target.text().strip()
        if not t:
            QMessageBox.warning(self, "Royal-Sec", "Target required (lab-only: 127.0.0.1 or lab.local)")
            return
        self.run_btn.setEnabled(False); self.stop_btn.setEnabled(True); self.prog.setVisible(True)
        cmd=[sys.executable, "-m", "rtai_core.cli_app", "weaponize", "--target", t, "--payload-type", self.payload.currentText()]
        if self.out.text().strip():
            cmd+=["--out", self.out.text().strip()]
        if self.force.isChecked():
            cmd.append("--force")
        cmd.append("--yes")
        self.log.append(f"[FORGE] Forging {self.payload.currentText()} for {t} ...\n")
        self._spawn(cmd)
    def _spawn(self, cmd):
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
