import pathlib

content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

checks = [
    ('Docker build', 'docker build' in content.lower()),
    ('docker compose', 'docker compose' in content.lower()),
    ('Container', 'container' in content.lower()),
    ('HTML report', 'html' in content.lower() and 'report' in content.lower()),
    ('HTML format', '--format html' in content.lower() or 'format html' in content.lower()),
    ('Docker build', 'docker build' in content.lower()),
    ('docker compose', 'docker compose' in content.lower()),
    ('Container', 'container' in content.lower()),
]

print('Verification:')
for check, result in [
    ('Docker build', 'docker build' in content.lower()),
    ('docker compose', 'docker compose' in content.lower()),
    ('Container', 'container' in content.lower()),
    ('HTML report', 'html' in content.lower() and 'report' in content.lower()),
    ('HTML format', '--format html' in content.lower() or 'format html' in content.lower()),
    ('Docker build', 'docker build' in content.lower()),
    ('docker compose', 'docker compose' in content.lower()),
    ('Container', 'container' in content.lower()),
]:
    status = 'OK' if result else 'MISSING'
    print('  [{}] {}'.format(status, check))