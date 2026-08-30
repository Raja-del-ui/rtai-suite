import pathlib

content = pathlib.Path('rtai_core/gui/c2_gui.py').read_text(encoding='utf-8')

old = """                ['--encode-tasks'] if self.encode_tasks.isChecked() else []),\n            cwd=str(Path.cwd())"""

new = """                (['--encode-tasks'] if self.encode_tasks.isChecked() else []),\n            cwd=str(Path.cwd())"""

content = pathlib.Path('rtai_core/gui/c2_gui.py').read_text(encoding='utf-8')
old = """                (['--encode-tasks'] if self.encode_tasks.isChecked() else []),\n            cwd=str(Path.cwd())"""

new = """                (['--encode-tasks'] if self.encode_tasks.isChecked() else []),\n            cwd=str(Path.cwd())"""

if old in content:
    content = content.replace(old, new)
    pathlib.Path('rtai_core/gui/c2_gui.py').write_text(content, encoding='utf-8')
    print('Fixed')
else:
    print('Pattern not found')
    idx = content.find('if self.encode_tasks.isChecked() else []),\n            cwd=str(Path.cwd())')
    if idx >= 0:
        print(repr(content[idx-50:idx+80]))

pathlib.Path('rtai_core/gui/c2_gui.py').write_text(content, encoding='utf-8')
print('Done')