import pathlib

content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

checks = [
    ('06-gui', '06-gui' in content),
    ('GUI Module', 'rtai_core.gui' in content),
    ('GUI Launch', 'rtai gui' in content),
    ('GUI Module', 'rtai_core.gui' in content),
    ('GUI Launch', 'rtai gui' in content),
    ('HTML report', 'html' in content.lower() and 'report' in content.lower()),
    ('Docker build', 'docker build' in content.lower()),
    ('docker compose', 'docker compose' in content.lower()),
    ('Container', 'container' in content.lower()),
]

all_pass = True
for check, result in [
    ('06-gui', '06-gui' in content),
    ('GUI Module', 'rtai_core.gui' in content),
    ('GUI Launch', 'rtai gui' in content),
    ('GUI Module', 'rtai_core.gui' in content),
    ('GUI Launch', 'rtai gui' in content),
    ('HTML report', 'html' in content.lower() and 'report' in content.lower()),
    ('Docker build', 'docker build' in content.lower()),
    ('docker compose', 'docker compose' in content.lower()),
    ('Container', 'container' in content.lower()),
]:
    status = 'OK' if result else 'MISSING'
    if not result:
        print(f'  [MISSING] {check}')
    else:
        print(f'  [OK] {check}')

all_pass = all([
    '06-gui' in content,
    'rtai_core.gui' in content,
    'rtai gui' in content,
    'rtai_core.gui' in content,
    'rtai gui' in content,
    'html' in content.lower() and 'report' in content.lower(),
    'docker build' in content.lower(),
    'docker compose' in content.lower(),
    'container' in content.lower(),
])

if all_pass:
    print('All checks passed!')
else:
    print('Some checks failed')