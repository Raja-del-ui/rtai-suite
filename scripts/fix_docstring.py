with open('rtai_core/military_airgap.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix docstring indentation for _create_verification_script and _create_offline_readme
content = content.replace(
    '        def _create_verification_script(self, bundle_dir: Path):\n        """Create post-install verification script."""',
    '        def _create_verification_script(self, bundle_dir: Path):\n            """Create post-install verification script."""'
)

content = content.replace(
    '        def _create_offline_readme(self, bundle_dir: Path):\n        """Create offline deployment README."""',
    '        def _create_offline_readme(self, bundle_dir: Path):\n            """Create offline deployment README."""'
)

with open('rtai_core/military_airgap.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed docstring indentation')