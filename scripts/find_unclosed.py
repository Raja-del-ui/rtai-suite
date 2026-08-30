with open('rtai_core/military_airgap.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all triple quote positions
positions = []
start = 0
while True:
    pos = content.find('"""', start)
    if pos == -1:
        break
    positions.append(pos)
    start = pos + 3

print(f'Found {len(positions)} triple quotes')
for i, pos in enumerate(positions):
    # Show context
    start_ctx = max(0, pos - 30)
    end_ctx = min(len(content), pos + 50)
    context = content[start_ctx:end_ctx].replace('\n', '\\n')
    print(f'  {i}: pos={pos}, context=...{context}...')

if len(positions) % 2 != 0:
    print(f'\nUNEVEN - last triple quote at pos {positions[-1]} is unclosed')
    # Show context around the last one
    last = positions[-1]
    start_ctx = max(0, last - 100)
    context = content[start_ctx:last+10].replace('\n', '\\n')
    print(f'Context: ...{context}...')