import glob

for fpath in glob.glob('C:/PROJECTS/CHASE/frontend/src/*.jsx'):
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            code = f.read()
        # Fix escaped single quotes written by the Python regex substitution
        if "\\'" in code:
            fixed = code.replace("\\'", "'")
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print(f'Fixed: {fpath}')
        else:
            print(f'OK: {fpath}')
    except Exception as e:
        print(f'Skip {fpath}: {e}')
