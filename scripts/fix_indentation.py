with open('rtai_core/military_airgap.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation of _create_verification_script and _create_offline_readme methods
# They should be at class level (4 spaces), not inside _create_install_script (8 spaces)

# Fix _create_verification_script method indentation
content = content.replace(
    '        def _create_verification_script(self, bundle_dir: Path):\n        """Create post-install verification script."""',
    '    def _create_verification_script(self, bundle_dir: Path):\n        """Create post-install verification script."""')

# Fix _create_offline_readme method
content = content.replace(
    '    def _create_offline_readme(self, bundle_dir: Path):\n        """Create offline deployment README."""',
    '    def _create_offline_readme(self, bundle_dir: Path):\n        """Create offline deployment README."""')

# Also need to fix the method bodies to be properly indented
# The methods' bodies should be at 8 spaces (method body), not 12

import re

# Fix the _create_verification_script body indentation
content = re.sub(
    r'^(\s{8})script = \(\n',
    r'        script = (\n',
    content
)

# Fix the method body indentation for _create_verification_script
# The body lines should be at 8 spaces (one level deeper than method def)
lines = content.split('\n')
new_lines = []
in_verification = False
in_offline_readme = False
base_indent = 8  # method body should be 8 spaces

for line in content.split('\n'):
    # Detect method boundaries
    if 'def _create_verification_script' in line:
        in_verification = True
        in_offline_readme = False
    elif 'def _create_offline_readme' in line:
        in_verification = False
        in_offline_readme = True
    elif line.strip().startswith('def ') and '_create_' not in line:
        in_verification = False
        in_offline_readme = False

    # Fix indentation for method bodies
    if (in_verification or in_offline_readme) and line.strip() and not line.strip().startswith('def '):
        # Remove leading whitespace and add proper indent
        stripped = line.lstrip()
        if stripped and not stripped.startswith('#'):
            line = ' ' * 8 + stripped
    
    new_lines.append(line)

content = '\n'.join(new_lines)

with open('rtai_core/military_airgap.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed indentation')