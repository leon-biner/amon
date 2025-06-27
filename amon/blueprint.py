# blueprint.py


#----------------#
#- Introduction -#
#----------------#
'''
Blueprint for the AMON code

--------------------------------------------------------

For every objective function, we need the annual electricity production (aep)
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
        convergence_tolerance : Float or None
    
        Note : All deficit models inherit from the DeficitModel class
    
    Site object  (We use XRSite, see https://gitlab.windenergy.dtu.dk/TOPFARM/PyWake/-/blob/master/py_wake/site/xrsite.py?ref_type=heads)
    -----------
            The site object stores the probability of each (wind_speed, wind_direction) combo, 
        the turbulence intensity the wind shear (change of wind speed with height function),
        the elevation of the zone for x, y, the interpolation method used by scipy (used if the
        point explored is not in the data provided, it interpolates to find the wind speed and
        wing direction at that poiny)

        Constructor parameters
        ----------------------
            ds            : xarray dataset
                            data_vars={"P"  : (("wd", "ws"), probability_matrix (prob of wd_bin[i]/ws[j] combo),
                                    "TI" : float} # Joséphine used 0.1, and the examples use that too, not sure why
                            coords={"wd":wd_bin_values, "ws":ws_bin_values} (bin center values)
            interp_method : 'linear', 'nearest' or 'cubic', default is linear
            shear         : Function of one argument (height) that returns a multiplier 
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

Constraints
-----------

We have multiple constraints :
    Spacing constraint     : There needs to be enough space between turbines
    Placing constraint     : The turbines need to be inside the determined zone
    Height constraints     : The turbines cannot be infinitely high
    Budget constraints
    Maybe yaw angles constraints

    The buildable zone, aka the zone where turbines can be placed, is defined using shapely polygons.
The placing constraint is calculated by finding how far away from the zone the turbine is, if it's outside.
The spacing constraint depends on the diameters of each wind turbine.
The height constraint depends on the model of wind turbine used.


How are the parameters chosen ?
-------------------------------
    The wind data (windrose), the zone, the objective function and the wind turbine models all need to be specified in a parameters file.
Optionaly, one can specify a scale factor for the size of the zone, an elevation function to add a vertical aspect, and a turbulence intensity.
If not specified, default values are used.
As for models, convergence tolerance, and other precision parameters, they are determined by a fidelity number that is passed as an argument to the blackbox


How to run the program ?
------------------------
    The program uses the "amon" main command to launch it from the terminal, then some subcommands can be used.
At any point, adding -h to the command will pull up a help menu for more detail. Here are the subcommands :
    "run"            : run blackbox with a certain instance or param file and a point to evaluate
    "show-windrose"  : plot the windrose of a certain wind data folder
    "show-zone"      : plot a certain zone, optionaly with a point to plot. Good to determine a starting point
    "show-elevation" : plot the elevation function used
    "serve"          : start a local server that handles requests. This prevents reimporting all the libraries at every iteration.
                       Use -s when running the blackbox to send requests to the server for it to make the calculations instead of doing them from the current session
    "shutdown"       : shuts down the server

There are multiple arguments and flags, use the -h menu or look at the argarsing.py file for details

'''

#----------------------------#
#- Description of .py files -#
#----------------------------#
'''
Main files :
    argparsing.py : Defines the command-line arguments and parses them, making sure they are adequate
    main.py       : Starts the right process according to the command-line arguments (run the blackbox, show the windrose, start the server, etc)
    utils.py      : Functions and global variables used across the code

Command-specific files :
    client.py      : Sends the right request to the server, according to command-line arguments
    server.py      : Runs the appropriate code according to the request received and responds with the result
    blackbox.py    : Runs the blackbox with given parameter file, point, seed, and fidelity
    plot_functions : Plots the windrose, the zone, the turbine's power/ct curve, or the elevstion function

Other files :
    windfarm_data.py : Builds the objects necessary to run the blackbox from the parameter file
    cost.py          : Defines how the cost over lifetime of the windfarm is calculated
'''

#------------------#
#- File structure -#
#------------------#
'''
    amon/
    |-- src/
        |-- *.py
    |-- instances/
        |-- instance_n/
            |-- param_file.txt
    |-- data/
        |-- elevation_functions/
            |-- elevation_function_n.py
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

#------------------------#
#- param_file structure -#
#------------------------#
'''
    Can have whitelines of random lines in between, as long as the line
    starts with the right parameter name, then whitespace, then the data.
    Order does not matter.
    --------------------------------------------------------------------
    OBJECTIVE_FUNCTION      <name of objective function>        (*)
    ZONE                    <id of zone>                        (*)  
    BUDGET                  <Budget in USD>
    WIND_DATA               <id (index) of wind data folder>    (*)
    TI                      <float value>
    ELEVATION_FUNCTION      <id (index) of shear function>
    WIND_TURBINES           <ids (indices) of wind turbines>    (*) (separated by commas)
    SCALE_FACTOR            <float value>
    --------------------------------------------------------------------
    Note : the ones with (*) are mandatory, others are optional
'''