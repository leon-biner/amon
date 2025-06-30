import subprocess
import numpy as np

for i in range(20000):
    print("Iteration ", i+1, ' of ', 20000)
    with open(f'x{i}.txt', 'w') as file:
        file.write('coords [')
        for j in range(15):
            file.write(f"{np.random.uniform(-425000, -423500)}, {np.random.uniform(237750, 239250)}, ")
        file.write(f"{np.random.uniform(-425000, -423500)}, {np.random.uniform(237750, 239250)}]")
    result = subprocess.run(['amon', 'run', '4', f'x{i}.txt', '-s'], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    output = lines[1]
    print("Output : ", output)
    constraints = output.split()[1:]
    print("Constraints : ", constraints)
    for const in constraints:
        if float(const) > 0:
            break
    else:
        break
