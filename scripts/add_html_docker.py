import pathlib
import re

content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

# Add HTML and Docker references in the Platform section
idx = content.find('## Platform Capabilities')
if idx >= 0:
    table_end = content.find('\n## ', idx + 1)
    if table_end == -1:
        table_end = len(content)
    
    table_section = content[idx:table_end]
    
    if 'HTML reporting' not in table_section and 'Docker' not in table_section:
        # Find the end of the table
        table_lines = content[idx:table_end].split('\n')
        for i in range(len(table_lines) - 1, -1, -1):
            if table_lines[i].strip().startswith('|'):
                # Insert before this line
                table_lines.insert(i, '| HTML reporting | `copilot.py --format html` styled client report · `metrics.py --html` click dashboard |')
                table_lines.insert(i + 1, '| Docker/Containers | `docker build -t rtai-suite .` (non-root + healthcheck) · `docker compose up api` |')
                break
        
        new_table = '\n'.join(table_lines)
        content = content[:idx] + new_table + content[idx + len('\n'.join(content[idx:table_end].split('\n'))):]
        print('Added HTML/Docker rows to Platform Capabilities table')
    else:
        print('HTML/Docker already in table')

    # Also add Docker reference in Architecture section
    if 'Docker' not in content and 'docker' not in content.lower():
        arch_idx = content.find('## Architecture')
        if arch_idx >= 0:
            arch_end = content.find('\n## ', arch_idx + 1)
            if arch_end == -1:
                arch_end = len(content)
            insert_pos = arch_end
            insertion = '\n\n**Containers:** Docker multi-stage build with non-root user, health checks, and docker-compose for multi-service deployment.\n'
            content = content[:arch_end] + '\n\n**Containers:** Docker multi-stage build with non-root user, health checks, and docker-compose for multi-service deployment.\n' + content[arch_end:]
            print('Added Docker reference to Architecture section')

    with open('BOOK.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated BOOK.md with HTML/Docker references')