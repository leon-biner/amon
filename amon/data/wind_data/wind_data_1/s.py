with open("wind_speed.csv", 'r') as file:
    lines = file.readlines()

with open("wind_speed.csv", 'w') as file:
    for line in lines:
        if line.startswith('2018'):
            file.write(line)

with open("wind_direction.csv", 'r') as file:
    lines = file.readlines()

with open("wind_direction.csv", 'w') as file:
    for line in lines:
        if line.startswith('2018'):
            file.write(line)