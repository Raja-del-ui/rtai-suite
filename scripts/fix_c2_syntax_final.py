import pathlib

content = pathlib.Path('rtai_core/gui/c2_gui.py').read_text(encoding='utf-8')

old = """                ('--tasks', self.listener_tasks.text().strip()] if self.listener_tasks.text().strip() else [] +
                (['--encode-tasks'] if self.encode_tasks.isChecked() else []),"""

new = """                ('--tasks', self.listener_tasks.text().strip()) if self.listener_tasks.text().strip() else [] +
                (['--encode-tasks'] if self.encode_tasks.isChecked() else []),"""

if old in content:
    content = content.replace(old, new)
    with open('rtai_core/gui/c2_gui.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed')
else:
    print('Pattern not found')
    idx = content.find("if self.listener_tasks.text().strip() else [] +")
    if idx >= 0:
        print(repr(content[idx-50:idx+80]))