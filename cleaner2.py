import os

file_path = r'f:\AI-ML\FactForensic\FactForensic\pages\templates\pages\home.html'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Original lines: {len(lines)}")

# We know the good section ends at 
# 611: })();
# 612: </script>
# Let's find '</script>' just after 'fetchBreakingNews();'
start_idx = None
for i, line in enumerate(lines):
    if line.strip() == '</script>':
        # Check if previous lines contain fetchBreakingNews()
        if 'fetchBreakingNews();' in ''.join(lines[max(0, i-5):i]):
            start_idx = i + 1
            break

# The good section starts again at '<!-- ══ SECTION DIVIDER'
end_idx = None
for i, line in enumerate(lines):
    if '<!-- ══ SECTION DIVIDER' in line:
        end_idx = i
        break

if start_idx is not None and end_idx is not None:
    print(f"Cutting lines from {start_idx} to {end_idx}")
    new_lines = lines[:start_idx] + lines[end_idx:]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"File updated. New lines: {len(new_lines)}")
else:
    print(f"Could not find indices: start={start_idx}, end={end_idx}")
