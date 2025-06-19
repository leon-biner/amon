import shapely
from pathlib import Path

from py_wake.wind_farm_models.engineering_models import All2AllIterative

from amon.src.utils import getPoint, getPath
from amon.src.windfarm_data import WindFarmData


def runBB(args): # , blackbox, wind_farm_data):
    # Figure out if user provided instance number or his own param file
    # try:
        # instance = int(args.instance_or_param_file) # If user provided an instance, get its param_file
        # param_filepath = INSTANCES_PARAM_FILEPATHS[instance - 1]
        # print(f"Running with instance {instance}")
    # except (ValueError, TypeError):
        # param_filepath = getPath(args.instance_or_param_file)
        # print(f"Running with file {param_filepath}")
    param_filepath = Path(args.instance_or_param_file)

    # Construct the blackbox
    wind_farm_data = WindFarmData(param_filepath)

    print(wind_farm_data.wind_turbines._diameters)
    print('------------')
    for i in range(len(wind_farm_data.wind_turbines._diameters)):
        print(wind_farm_data.wind_turbines.diameter(i), end='=?=')
        print(wind_farm_data.wind_turbines._diameters[i])

    wind_farm = All2AllIterative( site                  = wind_farm_data.site,
                                  windTurbines          = wind_farm_data.wind_turbines,
                                  wake_deficitModel     = wind_farm_data.wake_deficit_model,
                                  superpositionModel    = wind_farm_data.superposition_model,
                                  blockage_deficitModel = None, # wind_farm_data.blockage_deficit_model,
                                  deflectionModel       = wind_farm_data.deflection_model,
                                  turbulenceModel       = wind_farm_data.turbulence_model,
                                  rotorAvgModel         = wind_farm_data.rotor_avg_model,
                                  convergence_tolerance = wind_farm_data.convergence_tolerance ) 
    buildable_zone = wind_farm_data.buildable_zone

    blackbox = Blackbox(wind_farm, buildable_zone, wind_farm_data.min_dist_between_wt)

    # Get the path to the point to evaluate
    point_filepath = getPath(args.point, includes_file=True)

    point = getPoint(point_filepath)
    x, y = [float(x) for x in point['coords'][0::2]], [float(y) for y in point['coords'][1::2]]
    types = point['turbines']
    heights = point['heights']
    yaw_angles = point['yaw']
    if isinstance(types, int):
        diameters = [wind_farm_data.wind_turbines.diameter(0) for _ in range(len(x))]
    else:
        diameters = [wind_farm_data.wind_turbines.diameter(i) for i in types]
    print("Diameters :")
    print(diameters)
    print("coords :")
    print(x, '\n', y)
    print('types :')
    print(types)
    print('heights')
    print(heights)
    print('yaw angles')
    print(yaw_angles)

    constraints = blackbox.constraints(x, y, turbine_diameters=diameters)
    aep = blackbox.compute_aep(x, y, ws=wind_farm_data.WS_BB, wd=wind_farm_data.WD_BB, types=types, heights=heights, yaw_angles=yaw_angles)
    # if return on inversment 

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
    
    def compute_aep(self, x, y, ws, wd, types, heights, yaw_angles):
        return float(self.wind_farm(x, y, ws=ws, wd=wd, type=types, time=True, n_cpu=None, h=heights, yaw=yaw_angles).aep().sum())
    
    def constraints(self, x, y, turbine_diameters):
        turbines = [ 
        {"point": shapely.Point(x_i, y_i), "diameter": d} 
        for x_i, y_i, d in zip(x, y, turbine_diameters)
        ]
        points = [turbine["point"] for turbine in turbines]
        distance_matrix = [shapely.distance(point_i, points) for point_i in points]
        for i in range(len(points)):
            for j in range(0, i):
                distance_matrix[i][j] = 0
        
        sum_dist_between_wt = 0
        for i, list_distances in enumerate(distance_matrix):
            for j, d in enumerate(list_distances):
                if d == 0:
                    continue
                sum_dist_between_wt += min(d - turbines[i]['diameter'] - turbines[j]['diameter'], 0)
        distances = shapely.distance(points, self.buildable_zone)
        sum_dist_buildable_zone = sum(distances)

        return { 'placing' : sum_dist_buildable_zone, 
                 'spacing' : sum_dist_between_wt }