import pathlib

content = pathlib.Path('rtai_core/gui/c2_gui.py').read_text(encoding='utf-8')

# Fix the create_header method indentation
old = '''    def create_header(self):
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

new = '''    def create_header(self):
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
content = content.replace(
    '''    def create_header(self):
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
        
        return header''',
    '''    def create_header(self):
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
        
        return header''')

pathlib.Path('rtai_core/gui/c2_gui.py').write_text(content, encoding='utf-8')
print('Done')