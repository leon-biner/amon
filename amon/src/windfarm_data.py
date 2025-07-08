# windfarm_data.py
import numpy  as np
import xarray as xr
import pandas as pd
import shapefile
import csv
from py_wake.site import XRSite
# from py_wake.site.distance import StraightDistance, TerrainFollowingDistance
from py_wake.wind_turbines.power_ct_functions import PowerCtTabular
from py_wake.wind_turbines import WindTurbines
from py_wake.deficit_models import BastankhahGaussianDeficit, VortexCylinder
# from py_wake.rotor_avg_models import GaussianOverlapAvgModel
from py_wake.superposition_models import SquaredSum
# from py_wake.deflection_models import FugaDeflection, GCLHillDeflection, JimenezWakeDeflection 
from py_wake.turbulence_models import CrespoHernandez
from py_wake.site.shear import PowerShear
import shapely

from amon.src.utils import AMON_HOME, getFunctionFromFile

# Prevents negative deficits, which don't make sense physically and break PyWake
class SafeSquaredSum(SquaredSum):
    def __call__(self, deficit_jxxx, **kwargs):
        deficit_jxxx = np.maximum(deficit_jxxx, 0)
        return super().__call__(deficit_jxxx, **kwargs)


OBJECTIVE_FUNCTIONS = ['AEP', 'ROI', 'LCOE']
NB_WIND_DATA = 4
NB_ZONES = 5

# ACCEPTED_INTERPOLATION_METHODS   = ['linear', 'nearest', 'cubic']
REQUIRED_WIND_TURBINE_PROPERTIES = {'name', 'diameter[m]', 'hub_height[m]'}
ACCEPTED_BBO_VALUES              = {'OBJ', 'PLACING', 'SPACING', 'BUDGET', 'HEIGHT'}
ACCEPTED_OPT_VARIABLES           = {'COORDS', 'HEIGHTS', 'TYPES', 'YAW'}
# ACCEPTED_SUPERPOSITION_MODELS    = { 'SquaredSum' : SafeSquaredSum, 'LinearSum' : LinearSum, 'MaxSum' : MaxSum }
REQUIRED_POWERCT_CURVE_HEADERS   = {'WindSpeed[m/s]', 'Power[MW]', 'Ct'}


class WindFarmData:
    def __init__(self, param_file_path, fidelity=1):
        '''
            @brief   : sets the data used to construct the All2AllIterative object. What I call raw_data is data only used to construct other objects
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
                4 : Set the objective function, blackbox output, and budget constraint
            
            ATTRIBUTES
            ----------
                - Site
                - WindTurbines
                - Buildable zone
                - Physical models
                - Convergence tolerance
                - Wind speed and direction data
        '''


        #-----------------------------#
        #- Step 1 : Getting the data -#
        #-----------------------------#

        # All parameters and their respective handler function
        # Each handler function returns the parameter's corresponding object, or the data for building it
        parameters = { "WIND_DATA"          : self.__getWindData,             # returns dict of pandas dataFrames
                       "TI"                 : float,
                       "ZONE"               : self.__getZone,                 # returns shapefile.Reader
                       "BUDGET"             : float,
                       "OBJECTIVE_FUNCTION" : self.__getObjectiveFunction,    # returns string 
                       "ELEVATION_FUNCTION" : self.__getElevationFunction,    # returns python function object
                       "WIND_TURBINES"      : self.__getWindTurbines,         # returns dict with data
                       "SCALE_FACTOR"       : float,
                       "BLACKBOX_OUTPUT"    : self.__getBlackboxOutput,
                       "NB_WIND_TURBINES"   : self.__getNbWindTurbines,
                       "OPT_VARIABLES"      : self.__getOptVariables
                     }
        
        # Initialising optional parameters with default values
        raw_data = {
            "TI"                 : 0.1,
            "ELEVATION_FUNCTION" : lambda x, y: 0, # no elevation
            "SCALE_FACTOR"       : 1,
            "BUDGET"             : None
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
                            raise ValueError(f"\033[91mError\033[0m: Failed to parse parameter {param_name} : {e}")
        
        # Ensuring every parameter is in data
        missing_params = []
        for param_name in parameters:
            if param_name not in raw_data:
                missing_params.append(param_name)
        if missing_params:
            raise ValueError(f"\033[91mError\033[0m: Missing required parameters : {missing_params}")


        #-----------------------------------------------------------------#
        #- Step 2 : Construct the necessary objects for All2AllIterative -#
        #-----------------------------------------------------------------#

        # First, set the models, interpolation method, number of bins for the windrose, and convergence tolerance according to fidelity
        self.__setModels(fidelity)

        #---------------#
        #- Site object -#
        #---------------#

        wind_data = raw_data['WIND_DATA']
        # Initialising an empty dataset
        degrees_per_bin     = 360 / self.nb_wd_bins
        max_wind_speed      = wind_data['WIND_SPEED'].max().values[0]
        speed_units_per_bin = max_wind_speed / self.nb_ws_bins
        wind_direction_bins = np.array([i*degrees_per_bin for i in range(self.nb_wd_bins)])
        wind_speed_bins     = np.array([0] + [0.5+speed_units_per_bin*i for i in range(self.nb_ws_bins)])
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
                            interp_method = self.interp_method,
                            shear         = PowerShear(alpha=0.2), # PowerShear is the most common shear function, and 0.2 is common when on land 
                            distance      = self.wake_dist_model() if self.wake_dist_model is not None else None ) 

        #-----------------------#
        #- WindTurbines object -#
        #-----------------------#

        names          = raw_data['WIND_TURBINES']['names']
        diameters      = raw_data['WIND_TURBINES']['diameters']
        hub_heights    = raw_data['WIND_TURBINES']['hub_heights']
        powerct_curves = raw_data['WIND_TURBINES']['powerct_curves']

        self.wind_turbines = WindTurbines(names, diameters, hub_heights, powerct_curves)

        self.wind_turbines_models = [index - 1 for index in raw_data['WIND_TURBINES']['indices']] # We will use this as list indices, so starting at 0 is necessary


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

        self.elevation_function = raw_data['ELEVATION_FUNCTION']
        

        #------------------------------------------------------------#
        #- Nb turbines, Obj function, opt variables, BBO and budget -#
        #------------------------------------------------------------#

        self.nb_turbines = raw_data['NB_WIND_TURBINES']
        self.obj_function = raw_data['OBJECTIVE_FUNCTION']
        self.opt_variables = raw_data['OPT_VARIABLES']
        self.bbo = raw_data['BLACKBOX_OUTPUT']
        self.budget = raw_data['BUDGET']


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
            raise ValueError(f"OBJECTIVE_FUNCTION must be one of {OBJECTIVE_FUNCTIONS}, got {function_name}")
        return function_name

    def __getElevationFunction(self, id):
        id = self.__cast(id, int, "ELEVATION_FUNCTION")
        data_filepath = AMON_HOME / 'data' / 'elevation_functions' / f'elevation_function_{id}.py'
        return getFunctionFromFile(data_filepath)

    def __getWindTurbines(self, wind_turbines_indices):
        wt_data = { 'names' : [], 'diameters' : [], 'hub_heights' : [], 'powerct_curves' : []}
        wind_turbines_indices = [self.__cast(index.strip(), int, "WIND_TURBINES") for index in wind_turbines_indices.split(',')]
        for index in wind_turbines_indices:
            data_folder_path = AMON_HOME / 'data' / 'wind_turbines' / f'wind_turbine_{index}'
            if not data_folder_path.is_dir():
                raise FileNotFoundError(f"No wind turbine for index = {index}, no directory at {data_folder_path}")
            
            # dealing with the properties
            with open(data_folder_path / 'properties.csv') as properties_file:
                properties = next(csv.DictReader(properties_file))
                if not REQUIRED_WIND_TURBINE_PROPERTIES.issubset(properties):
                    raise ValueError(f"csv header must include {REQUIRED_WIND_TURBINE_PROPERTIES}")
            wt_data['names'].append(properties['name'])
            wt_data['diameters'].append(int(properties['diameter[m]']))
            wt_data['hub_heights'].append(int(properties['hub_height[m]']))

            # dealing with the powerct curve
            powerct_curve_file_data = pd.read_csv(data_folder_path / 'powerct_curve.csv')
            headers = powerct_curve_file_data.columns
            if not REQUIRED_POWERCT_CURVE_HEADERS.issubset(headers):
                raise ValueError(f"PowerCt curve headers must include {REQUIRED_POWERCT_CURVE_HEADERS}")
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
        wt_data['indices'] = wind_turbines_indices
        return wt_data

    def __getBlackboxOutput(self, list_outputs):
        list_outputs = [output.strip() for output in list_outputs.split(',')]
        if not set(list_outputs).issubset(ACCEPTED_BBO_VALUES):
            raise ValueError(f"BLACKBOX_OUTPUT must be within {ACCEPTED_BBO_VALUES}")
        return list_outputs 

    def __getNbWindTurbines(self, nb):
        try:
            nb_turbines = int(nb)
        except ValueError:
            if nb.strip().lower() == 'var':
                nb_turbines = None
            else:
                raise ValueError("NB_TURBINES must be an integer or VAR")
        return nb_turbines

    def __getOptVariables(self, variables):
        variables = [var.strip().upper() for var in variables.split(',')]
        if not set(variables).issubset(ACCEPTED_OPT_VARIABLES):
            raise ValueError(f"OPT_VARIABLES must be within {ACCEPTED_OPT_VARIABLES}")
        return variables



    #-----------------#
    #- Other methods -#
    #-----------------#
    
    # Casts variable with error handling, this is not a function
    def __cast(self, input, cast_function, param_name):
        try:
            return cast_function(input)
        except (ValueError, TypeError):
            raise ValueError(f"{param_name} must be a {cast_function.__name__}")

    def __setModels(self, fidelity):
        self.nb_ws_bins = 41
        self.nb_wd_bins = 36
        self.interp_method = 'linear'
        self.wake_dist_model = None
        self.rotor_avg_model = None
        self.wake_deficit_model = BastankhahGaussianDeficit(use_effective_ws=True,rotorAvgModel=self.rotor_avg_model)
        self.superposition_model = SafeSquaredSum()
        self.blockage_deficit_model = VortexCylinder(superpositionModel= self.superposition_model, rotorAvgModel=self.rotor_avg_model, use_effective_ws=True)
        self.deflection_model = None
        self.turbulence_model = CrespoHernandez(rotorAvgModel=self.rotor_avg_model)
        self.convergence_tolerance = 1e-6
