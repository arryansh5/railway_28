import re

with open('src/pages/MapPage/Map.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# The start is still the same:
start_marker = r"<div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>"
start_idx = content.find(start_marker)

# For the end marker, we want the `          ) : (` that comes AFTER the end of the `selectedTrain` block.
# We can find the `Station Explorer` which is right after it!
station_explorer_marker = r'<h2 style={{ margin: 0, fontSize: \'20px\', fontWeight: 700 }}>Station Explorer</h2>'
station_explorer_idx = content.find(station_explorer_marker, start_idx)

# Find the `) : (` just before `Station Explorer`
end_idx = content.rfind(') : (', start_idx, station_explorer_idx)

# Find the end of `) : (`
end_idx = end_idx + len(') : (')

# Re-read new_sidebar from patch_sidebar.py
with open('patch_sidebar.py', 'r', encoding='utf-8') as f:
    patch_content = f.read()

new_sidebar_start = patch_content.find("new_sidebar = '''") + len("new_sidebar = '''")
new_sidebar_end = patch_content.find("'''\n\ncontent = content[:start_idx]")
new_sidebar = patch_content[new_sidebar_start:new_sidebar_end]

# Add the closing tag for selectedTrain ternary
new_sidebar = new_sidebar + '\n          ) : ('

# Replace the broken content
fixed_content = content[:start_idx] + new_sidebar + content[end_idx:]

with open('src/pages/MapPage/Map.tsx', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print('Success')
