import shapely

from py_wake.wind_farm_models.engineering_models import All2AllIterative

from amon.src.utils import getPoint, getPath, INSTANCES_PARAM_FILEPATHS
from amon.src.windfarm_data import WindFarmData


def runBB(args): # , blackbox, wind_farm_data):
    # Figure out if user provided instance number or his own param file
    try:
        instance = int(args.instance_or_param_file) # If user provided an instance, get its param_file
        param_filepath = INSTANCES_PARAM_FILEPATHS[instance - 1]
        print(f"Running with instance {instance}")
    except (ValueError, TypeError):
        param_filepath = getPath(args.instance_or_param_file)
        print(f"Running with file {param_filepath}")

    # Construct the blackbox
    wind_farm_data = WindFarmData(param_filepath)

    wind_farm = All2AllIterative( site                  = wind_farm_data.site,
                                  windTurbines          = wind_farm_data.wind_turbines,
                                  wake_deficitModel     = wind_farm_data.wake_deficit_model,
                                  superpositionModel    = wind_farm_data.superposition_model,
                                  blockage_deficitModel = wind_farm_data.blockage_deficit_model,
                                  deflectionModel       = wind_farm_data.deflection_model,
                                  turbulenceModel       = wind_farm_data.turbulence_model,
                                  rotorAvgModel         = wind_farm_data.rotor_avg_model,
                                  convergence_tolerance = wind_farm_data.convergence_tolerance ) 
    buildable_zone = wind_farm_data.buildable_zone

    blackbox = Blackbox(wind_farm, buildable_zone, wind_farm_data.min_dist_between_wt)

    # Get the path to the point to evaluate
    point_filepath = getPath(args.point, includes_file=True)

    x, y = getPoint(point_filepath)
    aep = blackbox.compute_aep(x, y, ws=wind_farm_data.WS_BB, wd=wind_farm_data.WD_BB)
    constraints = blackbox.constraints(x, y)

    return f"AEP                : {aep} GWh\nSpacing constraint : {constraints['spacing']} m\nPlacing constraint : {constraints['placing']} m"

# def buildBB(args):
    # # Figure out if user provided instance number or his own param file
    # try:
        # instance = int(args.instance_or_param_file) # If user provided an instance, get its param_file
        # param_filepath = INSTANCES_PARAM_FILEPATHS[instance - 1]
        # print(f"Running with instance {instance}")
    # except (ValueError, TypeError):
        # param_filepath = getPath(args.instance_or_param_file)
        # print(f"Running with file {param_filepath}")

    # # Construct the blackbox
    # wind_farm_data = WindFarmData(param_filepath)

    # wind_farm = All2AllIterative( site                  = wind_farm_data.site,
                                  # windTurbines          = wind_farm_data.wind_turbines,
                                  # wake_deficitModel     = wind_farm_data.wake_deficit_model,
                                  # superpositionModel    = wind_farm_data.superposition_model,
                                  # blockage_deficitModel = wind_farm_data.blockage_deficit_model,
                                  # deflectionModel       = wind_farm_data.deflection_model,
                                  # turbulenceModel       = wind_farm_data.turbulence_model,
                                  # rotorAvgModel         = wind_farm_data.rotor_avg_model,
                                  # convergence_tolerance = wind_farm_data.convergence_tolerance ) 
    # buildable_zone = wind_farm_data.buildable_zone

    # blackbox = Blackbox(wind_farm, buildable_zone, wind_farm_data.min_dist_between_wt)

    # return blackbox, wind_farm_data

class Blackbox:
    def __init__(self, wind_farm, buildable_zone, min_dist_between_wt):
        self.wind_farm           = wind_farm
        self.buildable_zone      = buildable_zone
        self.min_dist_between_wt = min_dist_between_wt
    
    def compute_aep(self, x, y, ws, wd,types=0):
        return float(self.wind_farm(x, y, ws=ws, wd=wd, type=types, time=True, n_cpu=None).aep().sum())
    
    def constraints(self, x, y):
        points = [] # first create shapely points
        for x_i, y_i in zip(x, y):
            points.append(shapely.Point(x_i, y_i))
        distance_matrix = [shapely.distance(point_i, points) for point_i in points]
        for i in range(len(points)):
            for j in range(0, i):
                distance_matrix[i][j] = 0
        
        sum_dist_between_wt = 0
        for list_distances in distance_matrix:
            for d in list_distances:
                if d == 0:
                    continue
                sum_dist_between_wt += min(d - 2*self.min_dist_between_wt, 0)
        distances = shapely.distance(points, self.buildable_zone)
        sum_dist_buildable_zone = sum(distances)

        return { 'placing' : sum_dist_buildable_zone, 
                 'spacing' : sum_dist_between_wt }