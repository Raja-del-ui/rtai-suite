import pathlib

content = pathlib.Path('rtai_core/gui/c2_gui.py').read_text(encoding='utf-8')

old = """cwd=str(Path.cwd())"""

new = """cwd=str(Path.cwd())"""

if old in content:
    content = content.replace(old, new)
    pathlib.Path('rtai_core/gui/c2_gui.py').write_text(content, encoding='utf-8')
    print('Fixed')
else:
    print('Pattern not found')
    idx = content.find('cwd=str(Path.cwd())')
    if idx >= 0:
        print(repr(content[idx-50:idx+50]))

pathlib.Path('rtai_core/gui/c2_gui.py').write_text(content, encoding='utf-8')
print('Done')