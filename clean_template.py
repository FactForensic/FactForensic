"""
This script removes the leftover old breaking-news content from the Django template.
It keeps:
  - Lines 1-612: The new carousel section
  - Lines starting from '<!-- ══ SECTION DIVIDER': The rest of the page
"""
path = r'f:\AI-ML\FactForensic\FactForensic\pages\templates\pages\home.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# The marker for the start of the good second half
DIVIDER_MARKER = '<!-- \u2550\u2550 SECTION DIVIDER'

# The marker for the end of the new carousel script
CAROUSEL_END = '})();\n</script>\n'

# Split at the section divider
if DIVIDER_MARKER not in content:
    # Try with \r\n
    DIVIDER_MARKER_CRLF = DIVIDER_MARKER.replace('\n', '\r\n')
    if DIVIDER_MARKER_CRLF not in content:
        print("ERROR: Could not find section divider marker!")
        exit(1)
    parts = content.split(DIVIDER_MARKER_CRLF, 1)
    divider = DIVIDER_MARKER_CRLF + parts[1]
else:
    parts = content.split(DIVIDER_MARKER, 1)
    divider = DIVIDER_MARKER + parts[1]

first_half = parts[0]

# Find the end of the carousel script in the first half
# Everything up to and including })();\n</script>\n is good
if '})();\r\n</script>\r\n' in first_half:
    end_marker = '})();\r\n</script>\r\n'
elif '})();\n</script>\n' in first_half:
    end_marker = '})();\n</script>\n'
else:
    print("ERROR: Could not find carousel end marker!")
    exit(1)

# Split first half at the carousel end marker (keep everything up to and including the marker)
carousel_parts = first_half.split(end_marker, 1)
good_first = carousel_parts[0] + end_marker

# Combine: good first half + section divider onwards
new_content = good_first + '\n' + divider

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

# Count lines in new content
line_count = new_content.count('\n')
print(f"Done! Approximate line count: {line_count}")
print(f"Old length: {len(content)} chars, New length: {len(new_content)} chars")
print(f"Removed: {len(content) - len(new_content)} chars")
