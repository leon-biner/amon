with open("x5.txt", 'r') as f:
    lines = f.readlines()
true_lines = []
for line in lines:
    true_lines.append(line.replace(',', ''))
with open("x5.txt", 'w') as f:
    f.write(true_lines[0])
