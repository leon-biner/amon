#This is the blueprint for what I want the code to act like

'''
    This is for computing the Annual Energy Production (aep)
    --------------------------------------------------------

    We compute the aep through a WindFarmModel object, specifically 
    a All2AllIterative object, which inherits from the EngineeringWindFarmModel
    base class, which itself inherits from the WindFarmModel base class. 
    The optimization variables will be some arguments of its __call__ method, from which we get the aep.

    The constraints are handled outside of the All2AllIterative object, partly using
    the shapely library

    All2AllIterative object  (see https://gitlab.windenergy.dtu.dk/TOPFARM/PyWake/-/blob/master/py_wake/wind_farm_models/engineering_models.py?ref_type=heads)
    -----------------------
            This object stores all the information about the wind farm, except the surface. That is
        handled differently. This stores the wind rose, models for the physical phenomenons, types
        of turbines, etc. When we call its __call__ method, we provide points and types of turbines, possibly heights,
        for each point, and we get an aep value. So the optimisation variables are position and type of turbine.

        Constructor parameters
        ----------------------
            site                  : Site object
            windTurbines          : WindTurbines object
            wake_deficitModel     : WakeDeficitModel object
            rotorAvgModel         : RotorAvgModel object. If not specified, RotorCenter object is used 
                                    by default
            superpositionModel    : SuperpositionModel object. If not specified, LinearSum is used
            blockage_deficitModel : BlockageDeficitModel object. If not specified, blockage correction
                                    is not considered in the simulation
            deflectionModel       : DeflectionModel object. If not specified, deflection is not considered
                                    in the simulation
            turbulenceModel       : TurbulenceModel object. If not specified, turbulence is not considered
                                    in the simulation
            convergence_tolerance : float or None
    
            Note : All deficit models inherit from the DeficitModel class
    
    Site object  (We use XRSite, see https://gitlab.windenergy.dtu.dk/TOPFARM/PyWake/-/blob/master/py_wake/site/xrsite.py?ref_type=heads)
    -----------
            The site object stores the probability of each (wind_speed, wind_direction) combo, 
        the turbulence intensity the wind shear (change of wind speed with height function),
        the elevation of the terrain for x, y, the interpolation method used by scipy (used if the
        point explored is not in the data provided, it interpolates to find the wind speed and
        wing direction at that poiny)

        Constructor parameters
        ----------------------
            ds            : xarray dataset
                            data_vars={"P"  : (("wd", "ws"), probability_matrix (prob of wd_bin[i]/ws[j] combo),
                                    "TI" : float} # Joséphine used 0.1, and the examples use that too, not sure why
                            coords={"wd":wd_bin_values, "ws":ws_bin_values} (bin center values)
            interp_method : 'linear', 'nearest' or 'cubic', default is linear
            shear         : function of one argument (height) that returns a multiplier 
                            for wind speed. For example, if wind speed in the dataset is
                            ws, the wind speed used for a turbine at height h is ws*shear(h)
            distance      : Distance object, used to set how far we consider the wake effect 
                            If not specified, a StraightDistance object is used

    WindTurbines object  (see https://gitlab.windenergy.dtu.dk/TOPFARM/PyWake/-/blob/master/py_wake/wind_turbines/_wind_turbines.py?ref_type=heads)
    -------------------
            The WindTurbines object describes the wind turbines we want to use

        Constructor Parameters
        ----------------------
            names            : array_like
                               Name of each wind turbine
            diameters        : array_like
                               Diameter of each wind turbine
            hub_heights      : array_like
                               Hub height of each wind turbine, can be overwritten by solver if wanted
            powerCtFunctions : list of powerCtFunction objects
                               Power curve for each wind turbine
            **For powerCtFunctions, we use the PowerCtTabular subclass.
                    It takes in:
                        wind speed values (array_like)
                        power values associated to each wind speed (array_like)
                        power unit (one of {'W','kW','MW','GW'})
                        ct values (coefficient thrust) (array_like)
                    To construct that object, we need a list of n points, each point has
                    a windspeed, power value, and Ct value.

    Physical models
    ---------------
            The physical models are objects that model a physical phenomenon. See the PyWake
        documentation, but it's pretty straightforward : you choose the model and pass the class
        name with the constructor parameters if needed.

    Convergence tolerance
    ---------------------
            The convergence tolerance is a precision metric. Since the wind speed at each turbine 
        depends on the effects of the other turbines, it's a nonlinear coupled problem, which is 
        solved iteratively by PyWake (hence the class name All2AllIterative). The solver stops when 
        the relative change < convergence tolerance.
 
'''

# File structure
'''
    amon/
    |-- src/
        |-- *.py
    |-- instances/
        |-- instance_n/
            |-- param_file.txt
    |-- data/
        |-- shear_functions/
            |-- shear_function_n.py
        |-- wind_data/
            |-- wind_data_n/
                |-- wind_direction.csv
                |-- wind_speed.csv
        |-- wind_turbines/
            |-- wind_turbine_n/
                |-- properties.csv (name, diameter, hub_height)
                |-- powerct_curve.csv (windspeeds, power_values, ct_values)
        |-- zones/
            |-- zone_n/
                |-- boundary_zone.shp
                |-- exclusion_zone.shp
'''

# param_file structure
'''
    Can have whitelines of random lines in between, as long as the line
    starts with the right parameter name, then whitespace, then the data
    --------------------------------------------------------------------
    WIND_DATA               <id (index) of wind data file>      (*)
    NB_WIND_SPEED_BINS      <integer value>
    NB_WIND_DIRECTION_BINS  <integer value>
    TI                      <float value>
    ZONE                    <id of zone>                        (*)  
    INTERPOLATION_METHOD    <name of interpolation method>      ('linear', 'nearest', or 'cubic')
    SHEAR_FUNCTION          <id (index) of shear function>
    WAKE_DISTANCE           <name of wake distance class>       ('StraightDistance' or 'TerrainFollowingDistance')            
    WIND_TURBINES           <ids (indices) of wind turbines>    (*) (separated by commas)
    WAKE_DEFICIT_MODEL      <name of wake deficit model class>  (example : 'BastankhahGaussianDeficit')
    ROTOR_AVG_MODEL         <name of rotor avg model class>           
    SUPERPOSITION_MODEL     <name of superposition model class>
    BLOCKAGE_DEFICIT_MODEL  <name of blockage deficit model class>
    DEFLECTION_MODEL        <name of deflection model class>
    TURBULENCE_MODEL        <name of turbulence model class>
    CONVERGENCE_TOLERANCE   <float value> 
    MIN_DISTANCE_BETWEEN_WT <float value>                       (*)
    SCALE_FACTOR            <float value>
    --------------------------------------------------------------------
    Note : the ones with (*) are mandatory, others are optional

    UNITS
    -----
    **À remplir

'''

# Blackbox function
# Input  : param_file, x_positions, x_wind_turbines
# Output : constraints, aep
'''
    # Get the data to construct all objects

    # Construct the Site object

    # Construct the WindTurbines object

    # Construct the physical models objects

    # Construct the All2AllIterative object

    # Construct the buildable zone

    # Compute aep with x_positions and x_wind_turbines
    # The type (x_wind_turbine) is the id of the wind turbine,
    # in order of creation. Therefore, create them in the same 
    # order as they appear in the param file so the user can
    # know which one corresponds to which type

    # compute the spacing (distance between turbines)
    # and placing (how far they are from the buildable zone) constraints

    return the bbo : [obj, spacing_constraint, placing_constraint] and the obj
    
'''