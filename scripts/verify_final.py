import pathlib

c = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

checks = [
    ('06-gui', '06-gui' in c),
    ('GUI Launch', 'rtai gui' in c),
    ('GUI Module', 'rtai_core.gui' in c),
    ('HTML report', 'html' in c.lower() and 'report' in c.lower()),
    ('Docker build', 'docker build' in c.lower()),
    ('docker compose', 'docker compose' in c.lower()),
    ('Container', 'container' in c.lower()),
]

all_pass = True
for name, result in [
    ('06-gui', '06-gui' in c),
    ('GUI Launch', 'rtai gui' in c),
    ('GUI Module', 'rtai_core.gui' in c),
    ('HTML report', 'html' in c.lower() and 'report' in c.lower()),
    ('Docker build', 'docker build' in c.lower()),
    ('docker compose', 'docker compose' in c.lower()),
    ('Container', 'container' in c.lower()),
]:
    status = 'OK' if result else 'MISSING'
    if not result:
        print('  [MISSING]', name)
    else:
        print(f'  [OK] {name}')

all_pass = all([
    '06-gui' in c,
    'rtai gui' in c,
    'rtai_core.gui' in c,
    'html' in c.lower() and 'report' in c.lower(),
    'docker build' in c.lower(),
    'docker compose' in c.lower(),
    'container' in c.lower(),
])

print()
if all([
    '06-gui' in c,
    'rtai gui' in c,
    'rtai_core.gui' in c,
    'html' in c.lower() and 'report' in c.lower(),
    'docker build' in c.lower(),
    'docker compose' in c.lower(),
    'container' in c.lower(),
]):
    print()
    print('All BOOK.md checks passed!')
else:
    print('Some checks failed')