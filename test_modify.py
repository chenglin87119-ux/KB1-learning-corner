#!/usr/bin/env python3
"""Test on unit2 only."""
import sys, os, shutil

os.chdir('/home/wlsclaw/ket_learning_corner/html')
fp = 'unit2_my_school.html'
shutil.copy2(fp, fp + '.bak')
print(f'Backup: {fp}.bak')

# Read file
with open(fp, 'r', encoding='utf-8') as f:
    c = f.read()
orig = c

# Import the actual processing logic
from batch_modify import process_file
process_file(fp)

with open(fp, 'r', encoding='utf-8') as f:
    modified = f.read()

print('\n--- DIFF (first 200 lines) ---')
import difflib
diff = difflib.unified_diff(orig.splitlines(), modified.splitlines(), lineterm='')
for line in list(diff)[:200]:
    print(line)
