import numpy  as np
import xarray as xr
import pandas as pd
import shapefile
import ast
import importlib.util
import csv
from py_wake.site import XRSite
from py_wake.site.distance import StraightDistance, TerrainFollowingDistance
from py_wake.wind_turbines.power_ct_functions import PowerCtTabular
from py_wake.wind_turbines import WindTurbines
from py_wake.deficit_models import BastankhahGaussianDeficit # wake deficit
from py_wake.deficit_models import HybridInduction, RankineHalfBody, VortexCylinder # blockage deficit
from py_wake.rotor_avg_models import GaussianOverlapAvgModel
from py_wake.superposition_models import SquaredSum, LinearSum, MaxSum
from py_wake.deflection_models import FugaDeflection, GCLHillDeflection, JimenezWakeDeflection 
from py_wake.turbulence_models import CrespoHernandez, GCLTurbulence, FrandsenWeight
from py_wake.site.shear import PowerShear
import shapely

from amon.src.utils import AMON_HOME, SafeSquaredSum

OBJECTIVE_FUNCTIONS = ['AEP']
NB_WIND_DATA = 4
NB_TERRAIN = 5

ACCEPTED_INTERPOLATION_METHODS   = ['linear', 'nearest', 'cubic']
ACCEPTED_WAKE_DISTANCE_MODELS    = { 'StraightDistance' : StraightDistance, 'TerrainDollowingDistance' : TerrainFollowingDistance }
ACCEPTED_WIND_TURBINE_PROPERTIES = [ 'name', 'diameter(m)', 'hub_height(m)']
ACCEPTED_WAKE_DEFICIT_MODELS     = { 'BastankhahGaussianDeficit' : BastankhahGaussianDeficit }
ACCEPTED_ROTOR_AVG_MODELS        = { 'GaussianOverlapAvgModel' : GaussianOverlapAvgModel }
ACCEPTED_SUPERPOSITION_MODELS    = { 'SquaredSum' : SafeSquaredSum, 'LinearSum' : LinearSum, 'MaxSum' : MaxSum }
ACCEPTED_BLOCKAGE_DEFICIT_MODELS = { 'HybridInduction' : HybridInduction, 'RankineHalfBody' : RankineHalfBody, 'VortexCylinder' : VortexCylinder}
ACCEPTED_DEFLECTION_MODELS       = { 'FugaDeflection' : FugaDeflection, 'GCLHillDeflection' : GCLHillDeflection, 'JimenezWakeDeflection' : JimenezWakeDeflection }
ACCEPTED_TURBULENCE_MODELS       = { 'CrespoHernandez' : CrespoHernandez, 'GCLTurbulence' : GCLTurbulence, 'FrandsenWeight' : FrandsenWeight }
REQUIRED_POWERCT_CURVE_HEADERS   = { 'WindSpeed[m/s]', 'Power[MW]', 'Ct'}
ACCEPTED_BLOCKAGE_SUPERP_MODELS  = { 'LinearSum' : LinearSum, 'MaxSum' : MaxSum}


class WindFarmData:
    def __init__(self, param_file_path):
        '''
            @brief   : sets the data used to construct the All2AllIterative object
            @params  : param file path from AMON_HOME
            @returns : nothing
        '''
        '''
            STEPS
            -----
                1 : Read through the param file and get the raw data (dict). Some objects need other objects
                    to be constructed, so we extract the data then build the objects in order
                2 : Build the objects necessary to construct the All2AllIterative object and to handle the buildable zone
                3 : Set the buildable zone
            
            ATTRIBUTES
            ----------
                - Site
                - WindTurbines
                - Buildable zone
                - Physical models
                - Convergence tolerance
                - Wind speed and direction data
                - Minimal distance between turbines
        '''

        #---------------------------------#
        #- Step 1 : Getting the raw data -#
        #---------------------------------#

        # All parameters and their respective handler function
        # Each handler function returns the parameter's corresponding object, or the data for building it
        parameters = { "WIND_DATA"              : self.__getWindData,           # returns dict of pandas dataFrames
                       "NB_WIND_SPEED_BINS"     : int,
                       "NB_WIND_DIRECTION_BINS" : int,
                       "TI"                     : float,
                       "ZONE"                   : self.__getZone,                 # returns shapefile.Reader
                       "OBJECTIVE_FUNCTION"     : self.__getObjectiveFunction,    # returns string 
                       "INTERPOLATION_METHOD"   : self.__getInterpolationMethod,  # returns string
                       "SHEAR_FUNCTION"         : self.__getShearFunction,        # returns python function object
                       "WAKE_DISTANCE"          : self.__getWakeDistance,         # returns class
                       "WIND_TURBINES"          : self.__getWindTurbines,         # returns dict with data
                       "NB_WIND_TURBINES"       : int,
                       "WAKE_DEFICIT_MODEL"     : self.__getWakeDeficitModel,     # returns class
                       "ROTOR_AVG_MODEL"        : self.__getRotorAvgModel,        # returns class  
                       "SUPERPOSITION_MODEL"    : self.__getSuperpositionModel,   # returns class  
                       "BLOCKAGE_DEFICIT_MODEL" : self.__getBlockageDeficitModel, # returns class  
                       "BLOCKAGE_SUPERP_MODEL"  : self.__getBlockageSuperpModel,  # returns class
                       "DEFLECTION_MODEL"       : self.__getDeflectionModel,      # returns class  
                       "TURBULENCE_MODEL"       : self.__getTurbulenceModel,      # returns class  
                       "CONVERGENCE_TOLERANCE"  : float,
                       "MIN_DISTANCE_BETWEEN_WT": float,
                       "SCALE_FACTOR"           : float
                     }
        
        # Initialising optional parameters with default values
        raw_data = {
            "NB_WIND_SPEED_BINS"     : 41,
            "NB_WIND_DIRECTION_BINS" : 36,
            "TI"                     : 0.1,
            "INTERPOLATION_METHOD"   : 'linear',
            "SHEAR_FUNCTION"         : None,
            "WAKE_DISTANCE"          : None,
            "WAKE_DEFICIT_MODEL"     : BastankhahGaussianDeficit,
            "ROTOR_AVG_MODEL"        : None,
            "SUPERPOSITION_MODEL"    : LinearSum,
            "BLOCKAGE_DEFICIT_MODEL" : None,
            "BLOCKAGE_SUPERP_MODEL"  : LinearSum,
            "DEFLECTION_MODEL"       : None,
            "TURBULENCE_MODEL"       : None,
            "CONVERGENCE_TOLERANCE"  : 1e-6,
            "SCALE_FACTOR"           : 1
        }

        # Read every line of the param file and set the data from it
        with open(AMON_HOME / param_file_path, 'r') as param_file:
            for line in param_file:
                line = line.strip()
                for param_name, handler in parameters.items():
                    if line.startswith(param_name):
                        value = line[len(param_name):].strip()
                        # Any exception raised in handler functions will be caught here
                        try:
                            raw_data[param_name] = handler(value)
                        except Exception as e:
                            raise ValueError(f"Failed to parse parameter {param_name} : {e}")
        
        # Ensuring every parameter is in data
        missing_params = []
        for param_name in parameters:
            if param_name not in raw_data:
                missing_params.append(param_name)
        if missing_params:
            raise ValueError(f"Missing required parameters : {missing_params}")


        #-----------------------------------------------------------------#
        #- Step 2 : Construct the necessary objects for All2AllIterative -#
        #-----------------------------------------------------------------#

        #---------------#
        #- Site object -#
        #---------------#

        wind_data = raw_data['WIND_DATA']
        # Initialising an empty dataset
        degrees_per_bin     = 360 / raw_data['NB_WIND_DIRECTION_BINS']
        max_wind_speed      = wind_data['WIND_SPEED'].max().values[0]
        speed_units_per_bin = max_wind_speed / raw_data['NB_WIND_SPEED_BINS'] 
        wind_direction_bins = np.array([i*degrees_per_bin for i in range(raw_data['NB_WIND_DIRECTION_BINS'])])
        # wind_speed_bins     = np.array([0] + [0.5+i for i in range(41)]) #np.array([0] + [0.5+speed_units_per_bin*i for i in range(raw_data['NB_WIND_SPEED_BINS'])])
        wind_speed_bins     = np.array([0] + [0.5+speed_units_per_bin*i for i in range(raw_data['NB_WIND_SPEED_BINS'])])
        wind_rose_data      = pd.DataFrame(data=None, columns=wind_direction_bins, index=wind_speed_bins[1:])
    
        # Going through csv data
        WS = wind_data['WIND_SPEED']
        WD = wind_data['WIND_DIRECTION']
        self.WS_BB = WS[list(WS.columns)[0]]
        self.WD_BB = WD[list(WD.columns)[0]]
        N  = len(WS)
        width = 360 / len(wind_direction_bins)
        for i in range(len(wind_direction_bins)):
            wd = wind_direction_bins[i]
            for j in range(len(wind_speed_bins)-1):
                lower, upper = wind_speed_bins[j], wind_speed_bins[j+1]
                if wd == 0:
                    sector = (360 - 0.5*width <= WD.values) | (WD.values < 0.5*width)
                else:
                    sector = (wd - 0.5*width <= WD.values) & (WD.values < wd + 0.5*width)
                TS_sector = WS.values[sector]
                wind_rose_data.iloc[j,i] = sum((lower <= TS_sector) & (TS_sector < upper)) / N

        wind_rose_dataset = xr.Dataset( data_vars={"P":(("wd", "ws"), wind_rose_data.values.T), "TI":raw_data['TI']},
                                           coords={"wd":wind_direction_bins, "ws":wind_speed_bins[1:]} )

        self.site = XRSite( ds            = wind_rose_dataset,
                            interp_method = raw_data['INTERPOLATION_METHOD'],
                            shear         = PowerShear(alpha=0.2), # power_law_shear,# raw_data['SHEAR_FUNCTION'],
                            distance      = raw_data['WAKE_DISTANCE']() if raw_data['WAKE_DISTANCE'] is not None else None ) 

        #-----------------------#
        #- WindTurbines object -#
        #-----------------------#

        names          = raw_data['WIND_TURBINES']['names']
        diameters      = raw_data['WIND_TURBINES']['diameters']
        hub_heights    = raw_data['WIND_TURBINES']['hub_heights']
        powerct_curves = raw_data['WIND_TURBINES']['powerct_curves']

        self.wind_turbines = WindTurbines(names, diameters, hub_heights, powerct_curves)

        #-------------------#
        #- Physical models -#
        #-------------------#

        # We first get all classes, then look which one they are, as some take different arguments
        rotor_avg_model_class         = raw_data['ROTOR_AVG_MODEL']
        superposition_model_class     = raw_data['SUPERPOSITION_MODEL']
        wake_deficit_model_class      = raw_data['WAKE_DEFICIT_MODEL']
        blockage_deficit_model_class  = raw_data['BLOCKAGE_DEFICIT_MODEL']
        deflection_model_class        = raw_data['DEFLECTION_MODEL']
        turbulence_model_class        = raw_data['TURBULENCE_MODEL']

        # Setting objects
        self.rotor_avg_model          = rotor_avg_model_class() if rotor_avg_model_class is not None else None
        self.superposition_model      = superposition_model_class()
        if wake_deficit_model_class.__name__ == 'FugaDeficit':
            self.wake_deficit_model       = wake_deficit_model_class(rotorAvgModel=self.rotor_avg_model )
        else:
            self.wake_deficit_model       = wake_deficit_model_class( use_effective_ws=True,
                                                                  rotorAvgModel=self.rotor_avg_model )
        self.blockage_deficit_model   = blockage_deficit_model_class( superpositionModel= LinearSum(),
                                                                      rotorAvgModel=self.rotor_avg_model,
                                                                      use_effective_ws=True ) if blockage_deficit_model_class is not None else None
        if not deflection_model_class:
            self.deflection_model = None
        else:
            if deflection_model_class.__name__ == 'GCLHillDeflection':
                self.deflection_model = deflection_model_class(wake_deficitModel=self.wake_deficit_model)
            else:
                self.deflection_model = deflection_model_class()

        if not turbulence_model_class:
            self.turbulence_model = None
        else:
            if turbulence_model_class.__name__ == 'FrandsenWeight':
                self.turbulence_model = turbulence_model_class()
            else:
                self.turbulence_model = turbulence_model_class(rotorAvgModel=self.rotor_avg_model)
        
        
        # Convergence tolerance
        self.convergence_tolerance = raw_data['CONVERGENCE_TOLERANCE']

        #--------------------------------------#
        #- Step 3 : Define the buildable zone -#
        #--------------------------------------#

        boundary_zone_content  = raw_data['ZONE']['boundary_zone']
        exclusion_zone_content = raw_data['ZONE']['exclusion_zone']
        boundary_zone          = []
        exclusion_zone         = []
        for shape in boundary_zone_content.shapes():
            coords = np.array(shape.points).T*raw_data['SCALE_FACTOR']
            boundary_zone.append(shapely.Polygon(coords.T))
        boundary_zone = [shapely.MultiPolygon(boundary_zone)]

        if exclusion_zone_content:
            for shape in exclusion_zone_content.shapes():
                coords = np.array(shape.points).T*raw_data['SCALE_FACTOR']
                exclusion_zone.append(shapely.Polygon(coords.T))
        
        buildable_zone = boundary_zone
        for polygon in exclusion_zone:
            buildable_zone = shapely.difference(buildable_zone, polygon)

        self.buildable_zone = buildable_zone
        
        self.min_dist_between_wt = raw_data['MIN_DISTANCE_BETWEEN_WT']

        '''This will all dissapear'''
        # for plotting the terrain, we need the boundary and buildable zones separately
        self.boundary_zone = boundary_zone
        self.exclusion_zone = exclusion_zone


    #-------------------#
    #- Handler methods -#
    #-------------------#

# Note to self : should verify column headers like in __getWindTurbines for the next method
    def __getWindData(self, id):
        id = self.__cast(id, int, "WIND_DATA")
        wind_speed_data_filepath     = AMON_HOME / 'data' / 'wind_data' / f'wind_data_{id}' / 'wind_speed.csv'
        wind_direction_data_filepath = AMON_HOME / 'data' / 'wind_data' / f'wind_data_{id}' / f'wind_direction.csv'
        return { 'WIND_SPEED'     : pd.read_csv(wind_speed_data_filepath, index_col=0),
                 'WIND_DIRECTION' : pd.read_csv(wind_direction_data_filepath, index_col=0) }

    def __getZone(self, id):
        id = self.__cast(id, int, "ZONE")
        boundary_zone_data_filepath = AMON_HOME / 'data' / 'zones' / f'zone_{id}' / 'boundary_zone.shp'
        exclusion_zone_data_filepath = AMON_HOME / 'data' / 'zones' / f'zone_{id}' / 'exclusion_zone.shp'
        if not exclusion_zone_data_filepath.is_file(): # if there are no exclusions, so no exclusion_zone file
            return { 'boundary_zone'  : shapefile.Reader(boundary_zone_data_filepath),
                     'exclusion_zone' : None }
        return { 'boundary_zone'  : shapefile.Reader(boundary_zone_data_filepath),
                 'exclusion_zone' : shapefile.Reader(exclusion_zone_data_filepath) }

    def __getObjectiveFunction(self, function_name):
        if function_name not in OBJECTIVE_FUNCTIONS:
            raise ValueError(f"\033[91mError\033[0m: OBJECTIVE_FUNCTION must be one of {OBJECTIVE_FUNCTIONS}, got {function_name}")
        return function_name

    def __getInterpolationMethod(self, name):
        if name not in ACCEPTED_INTERPOLATION_METHODS:
            raise ValueError(f"\033[91mError\033[0m: INTERPOLATION_METHOD must be one of {ACCEPTED_INTERPOLATION_METHODS}, got {name}")
        return name

    def __getShearFunction(self, id):
        id = self.__cast(id, int, "SHEAR_FUNCTION")
        data_filepath = AMON_HOME / 'data' / 'shear_functions' / f'shear_function_{id}.py'
        with open(data_filepath, 'r') as file:
            file_content = file.read()
        tree_file_content = ast.parse(file_content, filename=data_filepath)
        function_definitions = []
        other_code = []
        for node in tree_file_content.body:
            if isinstance(node, ast.FunctionDef): #if it's a function definition
                function_definitions.append(node)
            elif not isinstance(node, (ast.FunctionDef, ast.Expr)): #if it's not a function def or comment / docstring
                other_code.append(node)
        function_definitions = [node for node in tree_file_content.body if isinstance(node, ast.FunctionDef)]
        if len(function_definitions) != 1 or other_code:
            raise ValueError(f"\033[91mError\033[0m: shear_function_{id}.py file must have only one function definition alike f(number): return other_number")

        shear_function_name = function_definitions[0].name
        spec = importlib.util.spec_from_file_location("shear_function_module", data_filepath) # specifications of the file
        module = importlib.util.module_from_spec(spec) # make empty module
        spec.loader.exec_module(module) # execute the code and load it into the module object
        return getattr(module, shear_function_name) # select the part with shear_function_name


    def __getWakeDistance(self, distance_class_name):
        if distance_class_name not in ACCEPTED_WAKE_DISTANCE_MODELS:
            raise ValueError(f"\033[91mError\033[0m: WAKE_DISTANCE must be one of {list(ACCEPTED_WAKE_DISTANCE_MODELS.keys())}, got {distance_class_name}")
        return ACCEPTED_WAKE_DISTANCE_MODELS[distance_class_name]

    def __getWindTurbines(self, wind_turbines_indices):
        wt_data = { 'names' : [], 'diameters' : [], 'hub_heights' : [], 'powerct_curves' : []}
        wind_turbines_indices = [self.__cast(index.strip(), int, "WIND_TURBINES") for index in wind_turbines_indices.split(',')]
        for index in wind_turbines_indices:
            data_folder_path = AMON_HOME / 'data' / 'wind_turbines' / f'wind_turbine_{index}'
            if not data_folder_path.is_dir():
                raise FileNotFoundError(f"\033[91mError\033[0m: No wind turbine for index = {index}, no directory at {data_folder_path}")
            
            # dealing with the properties
            with open(data_folder_path / 'properties.csv') as properties_file:
                properties = next(csv.DictReader(properties_file))
                if set(properties.keys()) != set(ACCEPTED_WIND_TURBINE_PROPERTIES):
                    raise ValueError(f"csv header must be {ACCEPTED_WIND_TURBINE_PROPERTIES} or another permutation")
            wt_data['names'].append(properties['name'])
            wt_data['diameters'].append(int(properties['diameter(m)']))
            wt_data['hub_heights'].append(int(properties['hub_height(m)']))

            # dealing with the powerct curve
            powerct_curve_file_data = pd.read_csv(data_folder_path / 'powerct_curve.csv')
            headers = powerct_curve_file_data.columns
            if not REQUIRED_POWERCT_CURVE_HEADERS.issubset(headers):
                raise ValueError(f"\033[91mError\033[0m: PowerCt curve headers must include {REQUIRED_POWERCT_CURVE_HEADERS}")
            wind_speed_values = powerct_curve_file_data['WindSpeed[m/s]'].values
            power_values = powerct_curve_file_data['Power[MW]'].values*1000
            raw_ct_values = powerct_curve_file_data['Ct'].values
            ct_values = []
            for val in raw_ct_values:
                if val >= 1:
                    ct_values.append(0.99)
                elif val <= 0:
                    ct_values.append(0.01)
                else:
                    ct_values.append(val)
            wt_data['powerct_curves'].append(PowerCtTabular(wind_speed_values, power_values, 'kW', ct_values))
        
        return wt_data

    def __getWakeDeficitModel(self, wake_deficit_model_class_name):
        if wake_deficit_model_class_name not in ACCEPTED_WAKE_DEFICIT_MODELS:
            raise ValueError(f"\033[91mError\033[0m: WAKE_DEFICIT_MODEL must be one of {list(ACCEPTED_WAKE_DEFICIT_MODELS.keys())}, got {wake_deficit_model_class_name}")
        return ACCEPTED_WAKE_DEFICIT_MODELS[wake_deficit_model_class_name]

    def __getRotorAvgModel(self, rotor_avg_model_class_name):
        if rotor_avg_model_class_name not in ACCEPTED_ROTOR_AVG_MODELS:
            raise ValueError(f"\033[91mError\033[0m: ROTOR_AVG_MODEL must be one of {list(ACCEPTED_ROTOR_AVG_MODELS.keys())}, got {rotor_avg_model_class_name}")
        return ACCEPTED_ROTOR_AVG_MODELS[rotor_avg_model_class_name]
    
    def __getSuperpositionModel(self, superposition_model_class_name):
        if superposition_model_class_name not in ACCEPTED_SUPERPOSITION_MODELS:
            raise ValueError(f"\033[91mError\033[0m: SUPERPOSITION_MODEL must be one of {list(ACCEPTED_SUPERPOSITION_MODELS.keys())}, got {superposition_model_class_name}")
        return ACCEPTED_SUPERPOSITION_MODELS[superposition_model_class_name]
    
    def __getBlockageDeficitModel(self, blockage_deficit_model_class_name):
        if blockage_deficit_model_class_name not in ACCEPTED_BLOCKAGE_DEFICIT_MODELS:
            raise ValueError(f"\033[91mError\033[0m: BLOCKAGE_DEFICIT_MODEL must be one of {list(ACCEPTED_BLOCKAGE_DEFICIT_MODELS.keys())}, got {blockage_deficit_model_class_name}")
        return ACCEPTED_BLOCKAGE_DEFICIT_MODELS[blockage_deficit_model_class_name]

    def __getBlockageSuperpModel(self, superposition_model_class_name):
        if superposition_model_class_name not in ACCEPTED_BLOCKAGE_SUPERP_MODELS:
            raise ValueError(f"\033[91mError\033[0m: SUPERPOSITION_MODEL must be one of {list(ACCEPTED_BLOCKAGE_SUPERP_MODELS.keys())}, got {superposition_model_class_name}")
        return ACCEPTED_BLOCKAGE_SUPERP_MODELS[superposition_model_class_name]

    def __getDeflectionModel(self, deflection_model_class_name):
        if deflection_model_class_name not in ACCEPTED_DEFLECTION_MODELS:
            raise ValueError(f"\033[91mError\033[0m: DEFLECTION_MODEL must be one of {list(ACCEPTED_DEFLECTION_MODELS.keys())}, got {deflection_model_class_name}")
        return ACCEPTED_DEFLECTION_MODELS[deflection_model_class_name]
    
    def __getTurbulenceModel(self, turbulence_model_class_name):
        if turbulence_model_class_name not in ACCEPTED_TURBULENCE_MODELS:
            raise ValueError(f"\033[91mError\033[0m: TURBULENCE_MODEL must be one of {list(ACCEPTED_TURBULENCE_MODELS.keys())}, got {turbulence_model_class_name}")
        return ACCEPTED_TURBULENCE_MODELS[turbulence_model_class_name]


    #-----------------#
    #- Other methods -#
    #-----------------#
    
    # Casts variable with error handling, this is not a function
    def __cast(self, input, cast_function, param_name):
        try:
            return cast_function(input)
        except (ValueError, TypeError):
            raise ValueError(f"{param_name} must be a {cast_function.__name__}")

