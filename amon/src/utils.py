# utils.py
from pathlib import Path
import numpy as np
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
    np.random.seed(seed_value)

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
def getPoint(point_filepath, nb_turbines, opt_variables):
    if point_filepath is None:
        return None
    try:
        try:
            with open(point_filepath, 'r') as file:
                lines = file.read().splitlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"No point file at {point_filepath}")
        
        point = {}
        line = next((line for line in lines if line.split()), None) # Get the line where the point is specified

        if line is None:
            raise ValueError("Empty point file")
        
        values = [float(value.strip()) for value in line.split()] # Separate point into single elements

        nb_opt_variables = len(opt_variables) + 1 # We assume coords are always present. Since there is (x,y), we have to add 1 

        if nb_turbines is not None:
            if len(values) / nb_opt_variables != nb_turbines:
                raise ValueError(f"Point must be {nb_opt_variables} times as long as number of turbines, currently has {len(values)} values for {nb_turbines} turbines")
        else:
            if len(values) % nb_opt_variables != 0:
                raise ValueError(f"Point must be {nb_opt_variables} times as long as number of turbines, currently has {len(values)} values")
            nb_turbines = len(values) // nb_opt_variables

        # Set the point according to the opt variables specified in the param file
        i = 0
        for variable in opt_variables:
            variable = variable.lower()
            if variable == 'coords':
                point[variable] = [value for value in values[i*nb_turbines:(i+2)*nb_turbines]]
                i += 2
                continue
            elif variable == 'types':
                point[variable] = [int(value) for value in values[i*nb_turbines:(i+1)*nb_turbines]]
            else:
                point[variable] = [value for value in values[i*nb_turbines:(i+1)*nb_turbines]]
            i += 1
        # Set the default values for unspecified points
        if 'coords' not in point:
            raise ValueError("Must contain coordinates")
        if 'types' not in point:
            point['types'] = [0 for _ in range(nb_turbines)]
        if 'heights' not in point:
            point['heights'] = None # The default values are set by blackbox.py's runBB function
        if 'yaw' not in point:
            point['yaw'] = [0 for _ in range(nb_turbines)]
        return point
    except Exception as e:
        raise ValueError(f"\033[91mError\033[0m: Problem with point file: {e}")

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
    info = ''
    with open(INSTANCES_PARAM_FILEPATHS[instance - 1], 'r') as param_file:
        info += param_file.read()
    return info
    
# This function validates the output against hardcoded values
def check():
    import subprocess
    targets = { 1 : ['-42.2572597633', '0.0000000000', '0.0000000000', '0.0000000000'],
                2 : ['19623.9642234370', '0.0000000000', '0.0000000000', '0.0000000000'],
                3 : ['1.0450466129', '0.0000000000', '0.0000000000', '0.0000000000'],
                4 : ['1.7567544267', '0.0000000000', '0.0000000000', '0.0000000000', '-99979760.0000000000'],
                5 : ['35958.4901323267', '0.0000000000', '0.0000000000', '0.0000000000'] }
    results = {}
    for i in range(5):
        instance = i+1
        results[instance] = subprocess.run(['amon', 'run', f'{instance}', f'AMON_HOME/starting_pts/x{instance}.txt', '-s', '1'], capture_output=True, text=True).stdout.split()
    for instance, target_result in targets.items():
        if target_result != results[instance]:
            print(target_result)
            print(results[instance])
            return "\033[91mCHECK INVALID\033[0m: Unexpected results, please contact some_adress@provider.extension"
    return "\033[92mCHECK VALID\033[0m"