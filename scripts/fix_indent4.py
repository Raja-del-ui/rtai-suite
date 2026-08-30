with open('rtai_core/military_airgap.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix method body indentation for _create_verification_script and _create_offline_readme
# The issue is that method bodies need 12 spaces (8 for class + 4 for method)

lines = content.split('\n')
new_lines = []
in_verification = False
in_offline_readme = False

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
    
    # Fix indentation for method bodies (should be 12 spaces)
    if (in_verification or in_offline_readme) and line.strip() and not line.strip().startswith('def ') and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
        stripped = line.lstrip()
        if stripped and not stripped.startswith('#'):
            # Check current indent
            current_indent = len(line) - len(line.lstrip())
            if current_indent < 12:
                line = ' ' * 12 + stripped
    
    new_lines.append(line)
    
    # Detect method boundaries
    if 'def _create_offline_readme' in line:
        in_offline_readme = True
    elif line.strip().startswith('def ') and '_create_' not in line:
        in_verification = False
        in_offline_readme = False

with open('rtai_core/military_airgap.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print('Fixed indentation')