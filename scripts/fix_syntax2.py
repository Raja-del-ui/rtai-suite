import re

with open('rtai_core/military_airgap.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the problematic lines in _create_verification_script
# The issue is with escaped quotes in the script string

# Fix 1: Line 310-316 - fix the exception handler strings
content = content.replace(
    '        "        except Exception as e:\\n"',
    '        "        except Exception as e:\\\\n"'
)

content = content.replace(
    '        "            print(f\\"[WARN] Could not test CLI: {e}\\\\")\\n\\n"',
    '            "            print(f\\\"[WARN] Could not test CLI: {e}\\\")\\\\n\\\\n"'
)

content = content.replace(
    '        "    print()\\n"',
    '            "    print()\\\\n"'
)

content = content.replace(
    '        "    print(\\"=== Verification Complete ===:\\")\\n\\n"',
    '            "    print(\\\"=== Verification Complete ===:\\\")\\\\n\\\\n"'
)

content = content.replace(
    '        "if __name__ == \\"__main__\\":\\n"',
    '            "if __name__ == \\\"__main__\\\":\\\\n"'
)

content = content.replace(
    '        "    main()\\n"',
    '            "    main()\\\\n"'
)

content = content.replace(
    '        )',
    '        )'
)

# Fix the duplicate method definition
content = content.replace(
    '    def _create_offline_readme    def _create_offline_readme(self, bundle_dir: Path):',
    '    def _create_offline_readme(self, bundle_dir: Path):'
)

with open('rtai_core/military_airgap.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed syntax errors')