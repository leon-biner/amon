# utils.py
from pathlib import Path
import ast
import sys
import numpy as np


# Default port
DEFAULT_PORT = 8765

# Path to home directory
AMON_HOME = Path(__file__).parents[1]

# Path to param file for each instance (corresponding index)
INSTANCES_PARAM_FILEPATHS = [ AMON_HOME / 'instances' / '1' / 'params.txt' ]

# Reads the point file
def getPoint(point_filepath):
    if point_filepath is None:
        return None, None
    with open(point_filepath, 'r') as file:
        content = file.read().splitlines()
        point = {}
        keys = ['coords', 'turbines', 'heights', 'yaw']
        point['turbines'] = None
        point['heights']  = None
        point['yaw']      = None
        for line in content:
            for key in keys:
                if line.startswith(key):
                    point[key] = ast.literal_eval(line[len(key):].strip())
        if not point['yaw']:
            point['yaw'] = [0 for _ in range(int(len(point['coords'])/2))]
        if not point['turbines']:
            point['turbines'] = [0 for _ in range(int(len(point['coords'])/2))]
        return point

# Reads a string and returns the corresponding path
def getPath(path, includes_file=True):
    if path is None:
        return None
    if 'AMON_HOME' in path:
        path = path.replace('AMON_HOME', str(AMON_HOME))
    path = Path(path).expanduser()
    if includes_file:
        dir_path = path.parent
        filename = path.name
        try:
            dir_path = dir_path.resolve(strict=False)
        except Exception:
            raise FileNotFoundError(f"\033[91mINPUT ERROR\033[0m: Invalid save path provided {dir_path}")
        return dir_path / filename
    else:
        try:
            path = path.resolve(strict=False)
        except Exception:
            raise FileNotFoundError(f"\033[91mINPUT ERROR\033[0m: Invalid save path provided {path}")
        return path

def simple_excepthook(exctype, value, tb):
    print(value)
    sys.exit(1)

def plot3D(f, lx, ly, ux, uy):
    import matplotlib.pyplot as plt
    x = np.arange(lx, ux, step=(ux-lx)/500)
    y = np.arange(ly, uy, step=(uy-ly)/500)
    X, Y = np.meshgrid(x, y)
    Z = np.array([[f(x, y) for x, y in zip(row_x, row_y)] for row_x, row_y in zip(X, Y)])
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(X, Y, Z)
    plt.show()
