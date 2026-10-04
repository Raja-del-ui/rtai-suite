"""STIX/TAXII GUI — military threat intel feed."""
import sys
from pathlib import Path
try:
    from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QGroupBox,
                                   QFormLayout, QPushButton, QTextEdit, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView)
    from PySide6.QtGui import QFont
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QGroupBox,
                                 QFormLayout, QPushButton, QTextEdit, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView)
    from PyQt6.QtGui import QFont
    from PyQt6.QtCore import Qt
from rtai_core.gui.base import WorkerThread

class StixGUI(QWidget):  # Royal-Sec
    def __init__(self):
        super().__init__()
        self.worker=None
        self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(12,12,12,12); lay.setSpacing(10)
        hdr=QLabel("STIX 2.1 / TAXII 2.1  —  Threat Intel & ATT&CK Navigator")
        hdr.setFont(QFont("Share Tech Mono", 11, QFont.Weight.Bold)); hdr.setStyleSheet("color: #C2B280;")
        lay.addWidget(hdr)
        g1=QGroupBox("TAXII Collection")
        f1 = QFormLayout(g1)
        f1.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f1.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.server=QLineEdit(placeholderText="https://taxii.example/api/v2")
        self.collection=QLineEdit(placeholderText="collection-id (leave empty for local)")
        self.api_key=QLineEdit(placeholderText="API key (uses env if empty)"); self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        f1.addRow("Server:", self.server)
        f1.addRow("Collection:", self.collection)
        f1.addRow("API Key:", self.api_key)
        lay.addWidget(g1)
        g2=QGroupBox("Local STIX Generation")
        f2 = QFormLayout(g2)
        f2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        f2.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.classification=QComboBox(); self.classification.addItems(["CUI","SECRET","TOP_SECRET","UNCLASS"])
        self.pattern=QLineEdit(placeholderText="[file:name = 'malware.exe']")
        f2.addRow("Classification:", self.classification)
        f2.addRow("Indicator Pattern:", self.pattern)
        lay.addWidget(g2)
        # Table for indicators
        self.table=QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Indicator", "Pattern", "ATT&CK"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("QTableWidget { background: #0A0F0A; gridline-color: #4B5320; }")
        self.table.setMaximumHeight(120)
        lay.addWidget(self.table)
        # Populate with sample mapping
        try:
            from rtai_core.military_stix import MITREATTACKMapper
            for tid, info in list(MITREATTACKMapper.TECHNIQUES.items())[:5]:
                row=self.table.rowCount(); self.table.insertRow(row)
                self.table.setItem(row,0,QTableWidgetItem(tid))
                self.table.setItem(row,1,QTableWidgetItem(info['name']))
                self.table.setItem(row,2,QTableWidgetItem(info['tactic']))
        except Exception:
            pass
        btn=QHBoxLayout()
        self.fetch_btn=QPushButton("FETCH TAXII")
        self.fetch_btn.clicked.connect(self._fetch)
        self.gen_btn=QPushButton("GENERATE STIX")
        self.gen_btn.setStyleSheet("QPushButton { background: #4B5320; }")
        self.gen_btn.clicked.connect(self._generate)
        self.nav_btn=QPushButton("NAVIGATOR LAYER")
        self.nav_btn.clicked.connect(self._navigator)
        self.clear_btn=QPushButton("Clear"); self.clear_btn.clicked.connect(lambda: self.log.clear())
        for b in (self.fetch_btn, self.gen_btn, self.nav_btn, self.clear_btn):
            btn.addWidget(b)
        btn.addStretch()
        lay.addLayout(btn)
        self.prog=QProgressBar(); self.prog.setVisible(False); self.prog.setRange(0,0); lay.addWidget(self.prog)
        self.log=QTextEdit(readOnly=True)
        self.log.setStyleSheet("QTextEdit { background: #050A05; color: #33FF33; border: 1px solid #4B5320; font-family: 'JetBrains Mono', monospace; font-size: 11px; }")
        self.log.append("[STIX] Ready — classification handling per data_protection policy (military_opa.py)")
        lay.addWidget(self.log, 1)

    def _fetch(self):
        self.log.append(f"[TAXII] Fetching {self.server.text() or 'local'} / {self.collection.text() or 'default'} ...")
        try:
            from rtai_core.military_stix import TAXIIClient
            if not self.server.text().strip():
                self.log.append("[TAXII] No server — showing local STIX builder (military_stix.py:STIXBuilder)")
                self.log.append("[TAXII] Use TAXIIClient(server_url, api_key) for remote (see docs/military/stix.md)")
                return
            client=TAXIIClient(self.server.text().strip(), api_key=self.api_key.text().strip() or None)
            cols=client.get_collections()
            self.log.append(f"[TAXII] Collections: {cols}")
        except Exception as e:
            self.log.append(f"[ERROR] {e}")

    def _generate(self):
        pat=self.pattern.text().strip() or "[file:name = 'suspicious.exe']"
        cls=self.classification.currentText()
        self.log.append(f"[STIX] Generating indicator {pat} [{cls}] ...")
        try:
            from rtai_core.military_stix import STIXBuilder, MITREATTACKMapper
            from rtai_core.military_opa import OPAPolicyEngine
            opa=OPAPolicyEngine()
            dec=opa.evaluate("data_protection", {"data":{"classification":cls},"auth":{"valid":True},"encryption":"AES-256-GCM","mtls":True,"audit":True})
            if not dec.allowed and "not found" not in dec.reason:
                self.log.append(f"[OPA DENIED] {dec.reason}")
                return
            b=STIXBuilder()
            b.indicator(pattern=pat, labels=["malicious-activity"])
            bundle=b.bundle()
            self.log.append(f"[STIX] Bundle {bundle.id} with {len(bundle.objects)} objects")
            # Add to table
            row=self.table.rowCount(); self.table.insertRow(row)
            self.table.setItem(row,0,QTableWidgetItem(bundle.objects[-1].id[:16] if hasattr(bundle.objects[-1],'id') else "indicator"))
            self.table.setItem(row,1,QTableWidgetItem(pat))
            self.table.setItem(row,2,QTableWidgetItem("T1059"))
            self.log.append(f"[STIX] ATT&CK mapping: {MITREATTACKMapper.map_observation_to_techniques({'title': pat})}")
        except Exception as e:
            self.log.append(f"[ERROR] {e}")

    def _navigator(self):
        self.log.append("[NAVIGATOR] Generating ATT&CK Navigator layer...")
        try:
            from rtai_core.military_stix import ATTACKNavigatorLayer
            layer=ATTACKNavigatorLayer(name="RTAI-STIX", description="Generated via rtai_core/military_stix.py")
            layer.add_technique("T1059.001", score=0.9, comment="PowerShell")
            layer.add_technique("T1071.001", score=0.8, comment="Web Protocols")
            out=Path("attack_layer.json")
            layer.save(out)
            self.log.append(f"[NAVIGATOR] Layer saved -> {out} ({len(layer.techniques)} techniques)")
        except Exception as e:
            self.log.append(f"[ERROR] {e}")
