# utils.py
from pathlib import Path
import ast
import sys
import numpy as np


from py_wake.superposition_models import SquaredSum

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
        point['turbines'] = 0 # Default values
        point['heights']  = None
        point['yaw']      = None
        for line in content:
            for key in keys:
                if line.startswith(key):
                    point[key] = ast.literal_eval(line[len(key):].strip())
        if not point['yaw']:
            point['yaw'] = [0 for _ in range(int(len(point['coords'])/2))]
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

class SafeSquaredSum(SquaredSum):
    def __call__(self, deficit_jxxx, **kwargs):
        deficit_jxxx = np.maximum(deficit_jxxx, 0)
        return super().__call__(deficit_jxxx, **kwargs)