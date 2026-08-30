import pathlib

content = pathlib.Path('rtai_core/gui/phish_gui.py').read_bytes()

old = b'(["--host", self.landing_host.text().strip()] if self.landing_host.text().strip() else []),\n        cwd=str(Path.cwd())\n        )\n'
new = b'(["--host", self.landing_host.text().strip()] if self.landing_host.text().strip() else []),\r\n        ],\r\n        cwd=str(Path.cwd())\r\n        )\r\n'

if old in content:
    content = content.replace(old, new)
    pathlib.Path('rtai_core/gui/phish_gui.py').write_bytes(content)
    print('Fixed')
else:
    print('Pattern not found')
    idx = content.find(b'landing_host.text().strip() else []),')
    if idx >= 0:
        print(repr(content[idx-10:idx+80]))