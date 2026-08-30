import pathlib

content = pathlib.Path('rtai_core/gui/c2_gui.py').read_text(encoding='utf-8')

old = '''def on_error(self, error: str):
        self.worker = None
        self.set_running(False)
        self.output.append(f"\\n[ERROR] {error}\\n")'''

new = '''def on_error(self, error: str):
        self.worker = None
        self.set_running(False)
        self.output.append(f"\\n[ERROR] {error}\\n")

    def create_header(self):
        """Create the header layout with title and description."""
        header = QHBoxLayout()
        title = QLabel("C2 Detection Lab")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        
        desc = QLabel("C2 beacon simulator + AI detection engineering - fully offline lab")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 11px;")
        header.addWidget(desc)
        
        return header'''

content = pathlib.Path('rtai_core/gui/c2_gui.py').read_text(encoding='utf-8')

old = '''def on_error(self, error: str):
        self.worker = None
        self.set_running(False)
        self.output.append(f"\\n[ERROR] {error}\\n")'''

new = '''def on_error(self, error: str):
        self.worker = None
        self.set_running(False)
        self.output.append(f"\\n[ERROR] {error}\\n")

    def create_header(self):
        """Create the header layout with title and description."""
        header = QHBoxLayout()
        title = QLabel("C2 Detection Lab")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        
        desc = QLabel("C2 beacon simulator + AI detection engineering - fully offline lab")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 11px;")
        header.addWidget(desc)
        
        return header'''

content = pathlib.Path('rtai_core/gui/c2_gui.py').read_text(encoding='utf-8')

old = '''def on_error(self, error: str):
        self.worker = None
        self.set_running(False)
        self.output.append(f"\\n[ERROR] {error}\\n")'''

new = '''def on_error(self, error: str):
        self.worker = None
        self.set_running(False)
        self.output.append(f"\\n[ERROR] {error}\\n")

    def create_header(self):
        """Create the header layout with title and description."""
        header = QHBoxLayout()
        title = QLabel("C2 Detection Lab")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        
        desc = QLabel("C2 beacon simulator + AI detection engineering - fully offline lab")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 11px;")
        header.addWidget(desc)
        
        return header'''

content = content.replace(old, new)

pathlib.Path('rtai_core/gui/c2_gui.py').write_text(content, encoding='utf-8')
print('Done')