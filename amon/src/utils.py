# utils.py
from pathlib import Path
import ast
import sys
import importlib.util


# Default port
DEFAULT_PORT = 8765

# Path to home directory
AMON_HOME = Path(__file__).parents[1]

# Random seed
SEED = None
def setSeed(seed_value):
    global SEED
    SEED = seed_value

# Path to param file for each instance (corresponding index)
INSTANCES_PARAM_FILEPATHS = [ AMON_HOME / 'instances' / '1' / 'params.txt',
                              AMON_HOME / 'instances' / '2' / 'params.txt',
                              AMON_HOME / 'instances' / '3' / 'params.txt',
                              AMON_HOME / 'instances' / '4' / 'params.txt',
                              AMON_HOME / 'instances' / '5' / 'params.txt' ]

# Names of available wind turbines in order
AVAILABLE_TURBINES_NAMES = ['V80', 'OpenWind', 'IEA_22MW', 'V82', 'Bespoke_6MW', 'IEA_3.4MW']

# Turbines max heights in order
MAX_TURBINE_HEIGHTS = [100, 100, 187.5, 100, 187.5, 150]

# Reads the point file
def getPoint(point_filepath):
    if point_filepath is None:
        return None
    try:
        with open(point_filepath, 'r') as file:
            content = file.read().splitlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"\033[91mError\033[0m: Invalid point file at {point_filepath}")
    point = {}
    keys = ['coords', 'types', 'heights', 'yaw_angles']
    point['types'] = None
    point['heights']  = None
    point['yaw_angles'] = None
    for line in content:
        for key in keys:
            if line.startswith(key):
                point[key] = ast.literal_eval(line[len(key):].strip())
    if not point['yaw_angles']:
        point['yaw_angles'] = [0 for _ in range(int(len(point['coords'])/2))]
    if not point['types']:
        point['types'] = [0 for _ in range(int(len(point['coords'])/2))]
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

# For simpler error messages when not in debug mode
def simple_excepthook(exctype, value, tb):
    print(value)
    sys.exit(1)


def getFunctionFromFile(filepath):
    with open(filepath, 'r') as file:
        file_content = file.read()
    tree_file_content = ast.parse(file_content, filename=filepath)
    function_definitions = []
    for node in tree_file_content.body:
        if isinstance(node, ast.FunctionDef): #if it's a function definition
            function_definitions.append(node)
    function_definitions = [node for node in tree_file_content.body if isinstance(node, ast.FunctionDef)]
    if len(function_definitions) != 1:
        raise ValueError(f"\033[91mError\033[0m: elevation_function_{id}.py file must have only one function definition alike f(numbers): return other_number")

    elevation_function_name = function_definitions[0].name
    spec = importlib.util.spec_from_file_location("elevation_function_module", filepath) # specifications of the file
    module = importlib.util.module_from_spec(spec) # make empty module
    spec.loader.exec_module(module) # execute the code and load it into the module object
    return getattr(module, elevation_function_name) # select the part with elevation_function_name


# This function is used to display te info of every instance
def getInstanceInfo(instance):
    if instance > len(INSTANCES_PARAM_FILEPATHS):
        raise ValueError(f"\033[91mError\033[0m: Instance {instance} does not exist, choose from 1 to {len(INSTANCES_PARAM_FILEPATHS)}")
    nb_turbines_instances = [30, 12, 6, 11, 21]
    info = f"NB_TURBINES        {nb_turbines_instances[instance-1]}\n"
    with open(INSTANCES_PARAM_FILEPATHS[instance - 1], 'r') as param_file:
        info += param_file.read()
    return info
    
