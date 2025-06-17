with open('powerct_curve_2.csv', 'r') as file:
    lines = file.readlines()

with open('powerct_curve_2.csv', 'w') as file:
    for line in lines:
        file.write(line.replace(' ', ''))