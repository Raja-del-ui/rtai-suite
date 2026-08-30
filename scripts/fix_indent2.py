with open('rtai_core/military_airgap.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix indentation of _create_verification_script method body
# The method body should be indented by 8 spaces (4 for class + 4 for method)
lines = content.split('\n')
new_lines = []
in_verification = False
in_offline_readme = False

for line in content.split('\n'):
    # Detect method boundaries
    if 'def _create_verification_script' in line:
        in_verification = True
    elif 'def _create_offline_readme' in line:
        in_verification = False
        in_offline_readme = True
    elif line.strip().startswith('def ') and '_create_' not in line:
        in_verification = False
        in_offline_readme = False
    
    # Fix indentation for method bodies
    if (in_verification or in_offline_readme) and line.strip() and not line.strip().startswith('def ') and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
        # Ensure method body lines have 8 spaces indent
        stripped = line.lstrip()
        if stripped and not stripped.startswith('#'):
            # Check if line already has proper indent
            if not line.startswith(' ' * 8):
                line = ' ' * 8 + stripped
    
    new_lines.append(line)

content = '\n'.join(new_lines)

with open('rtai_core/military_airgap.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed indentation')