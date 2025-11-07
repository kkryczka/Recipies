files = [
    'scripts/import_data.py',
    'src/crud.py',
    'src/db.py',
    'src/main.py',
    'src/models.py',
    'src/normalize.py',
    'src/translate.py',
]
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            for i, l in enumerate(fh, start=1):
                line = l.rstrip('\n')
                ln = len(line)
                if ln > 79:
                    print(f"{f}:{i}:{ln}: {line}")
    except Exception as e:
        print('ERR', f, e)
