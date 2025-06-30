import subprocess
import numpy as np

from amon.src.utils import AMON_HOME

for i in range(20000):
    print("Iteration ", i+1, ' of ', 20000)
    with open(f'x{i}.txt', 'w') as file:
        file.write('coords [')
        for j in range(20):
            file.write(f"{np.random.uniform(-1150, 2500)}, {np.random.uniform(-1300, 813)}, ")
        file.write(f"{np.random.uniform(-1150, 2500)}, {np.random.uniform(-1300, 813)}]")
    result = subprocess.run([str(AMON_HOME), 'amon', 'run', '5', f'x{i}.txt', '-s'], capture_output=True, text=True)
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
