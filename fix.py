import sys

file_path = r'f:\AI-ML\FactForensic\FactForensic\pages\templates\pages\home.html'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if '<!-- Card inner -->' in line and start_idx is None:
            start_idx = i
        if '<!-- \u2550\u2550 SECTION DIVIDER' in line and end_idx is None:
            end_idx = i

    print(f'Start: {start_idx}, End: {end_idx}')

    if start_idx is not None and end_idx is not None:
        new_lines = lines[:start_idx] + lines[end_idx:]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print('Template successfully cleaned!')
    else:
        print('Failed to find start or end index')
except Exception as e:
    print(f'Error: {e}')
