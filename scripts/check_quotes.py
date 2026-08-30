with open('rtai_core/military_airgap.py', 'r', encoding='utf-8') as f:
    content = f.read()
    count = content.count('"""')
    print(f'Triple quotes count: {count}')
    if count % 2 != 0:
        print('UNEVEN - unclosed triple quote!')
    else:
        print('Even number of triple quotes')