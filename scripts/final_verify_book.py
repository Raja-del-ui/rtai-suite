import pathlib

content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

checks = [
    ('06-gui', '06-gui' in content),
    ('GUI Launch', 'rtai gui' in content),
    ('GUI Module', 'rtai_core.gui' in content),
    ('HTML report', 'html' in content.lower() and 'report' in content.lower()),
    ('Docker build', 'docker build' in content.lower()),
    ('docker compose', 'docker compose' in content.lower()),
    ('Container', 'container' in content.lower()),
]

print('Final BOOK.md verification:')
all_pass = True
for name, result in [
    ('06-gui', '06-gui' in content),
    ('GUI Launch', 'rtai gui' in content),
    ('GUI Module', 'rtai_core.gui' in content),
    ('HTML report', 'html' in content.lower() and 'report' in content.lower()),
    ('Docker build', 'docker build' in content.lower()),
    ('docker compose', 'docker compose' in content.lower()),
    ('Container', 'container' in content.lower()),
]:
    status = 'OK' if result else 'MISSING'
    if not result:
        print('  [MISSING]', check)
    else:
        print(f'  [OK] {name}')
    if not result:
        all_pass = False

if all_pass:
    print()
    print('All BOOK.md checks passed!')
else:
    print('Some checks failed')