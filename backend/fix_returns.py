import os

main_py_path = 'C:/PROJECTS/CHASE/backend/main.py'
with open(main_py_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(len(lines)):
    # get_recommendations result starts around line 361.
    # Actually, let's just check if the line contains `result = {` and it's not inside get_recommendations.
    # An easier way: replace all `result = {` with `return {`, then fix line 361 specifically.
    pass

# Better approach:
# We know the line indices from the previous search (1-indexed):
# 54, 57, 143, 149, 154, 162, 191, 198, 222, 267, 279, 289, 293, 304, 312, 336, 428, 514, 533, 567, 606
lines_to_fix = [54, 57, 143, 149, 154, 162, 191, 198, 222, 267, 279, 289, 293, 304, 312, 336, 428, 514, 533, 567, 606]

for idx in lines_to_fix:
    lines[idx-1] = lines[idx-1].replace('result = {', 'return {')

with open(main_py_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed result = { to return {")
