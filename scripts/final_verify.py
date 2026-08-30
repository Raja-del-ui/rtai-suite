import pathlib

content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

checks = [
    ('HTML', 'HTML' in content or 'html' in content.lower()),
    ('Docker', 'Docker' in content or 'docker' in content.lower()),
    ('Container', 'container' in content.lower()),
]

print('HTML/Docker check:')
for check, result in [('HTML', 'HTML' in content or 'html' in content.lower()),
                      ('Docker', 'Docker' in content or 'docker' in content.lower()),
                      ('Container', 'container' in content.lower())]:
    status = 'OK' if result else 'MISSING'
    print('  [{}] {}'.format(status, check))

# Full verification
checks = [
    ('Version 4.0.0', '4.0.0' in content),
    ('Military-Grade', 'Military-Grade' in content),
    ('91 tests', '91' in content and 'test' in content.lower()),
    ('5 Tools', all(x in content for x in ['Recon Agent', 'Injection Fuzzer', 'Phishing', 'C2 Detection', 'Report Copilot'])),
    ('SBOM', 'SBOM' in content),
    ('SLSA', 'SLSA' in content),
    ('PQC', 'PQC' in content or 'Post-Quantum' in content),
    ('TLA+', 'TLA' in content),
    ('STIX', 'STIX' in content),
    ('TAXII', 'TAXII' in content),
    ('OPA', 'OPA' in content),
    ('mTLS', 'mTLS' in content),
    ('TPM', 'TPM' in content),
    ('SBOM', 'SBOM' in content),
    ('SLSA', 'SLSA' in content),
    ('STIG', 'STIG' in content),
    ('Audit', 'audit' in content.lower()),
    ('JUnit', 'JUnit' in content or 'junit' in content.lower()),
    ('HTML', 'HTML' in content or 'html' in content.lower()),
    ('Async', 'async' in content.lower()),
    ('Docker', 'Docker' in content or 'docker' in content.lower()),
    ('Kali', 'Kali' in content),
    ('Windows', 'Windows' in content),
    ('Air-gap', 'air-gap' in content.lower() or 'airgap' in content.lower()),
]

all_pass = True
for check, result in checks:
    status = 'OK' if result else 'MISSING'
    if not result:
        print('  [MISSING] {}'.format(check))
        all_pass = False
    else:
        print('  [OK] {}'.format(check))

if all_pass:
    print()
    print('All checks passed!')
else:
    print()
    print('Some checks failed')