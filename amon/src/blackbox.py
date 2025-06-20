import shapely
from pathlib import Path

from py_wake.wind_farm_models.engineering_models import All2AllIterative

from amon.src.cost import lifetimeCost
from amon.src.utils import getPoint, getPath
from amon.src.windfarm_data import WindFarmData


def runBB(args): 
    param_filepath = Path(args.instance_or_param_file)

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

    blackbox = Blackbox(wind_farm, buildable_zone, 20, 100)

    # Get the point to evaluate
    point_filepath = getPath(args.point, includes_file=True)
    point = getPoint(point_filepath)
    x, y = [float(x) for x in point['coords'][0::2]], [float(y) for y in point['coords'][1::2]]
    models = point['models']
    
    print("Points :")
    for x_i, y_i in zip(x, y):
        print(f'({x_i}, {y_i})')
    print("\nModels :")
    for model in models:
        print(model)
    print('\nHeights before elevation function')
    for model in models:
        print(wind_farm_data.wind_turbines.hub_height(model))
    
    diameters = [wind_farm_data.wind_turbines.diameter(i) for i in models]
    elevation_function = wind_farm_data.elevation_function
    heights = []
    if point['heights'] is None:
        for x_i, y_i, model in zip(x, y, models): # If height not specified, the model's default height is used
            heights.append(wind_farm_data.wind_turbines.hub_height(model) + elevation_function(x_i, y_i))
    else:
        for height, x_i, y_i in zip(point['heights'], x, y):
            heights.append(height + elevation_function(x_i, y_i))
    yaw_angles = point['yaw_angles']

    if not (len(x) == len(y) == len(models) == len(heights) == len(yaw_angles)):
        raise ValueError("\033[91mError\033[0m: All fields of evaluated point must have the same dimensions")

    # Calculate annual electricity production and constraints
    aep = blackbox.compute_aep(x, y, ws=wind_farm_data.WS_BB, wd=wind_farm_data.WD_BB, types=models, heights=heights, yaw_angles=yaw_angles)
    constraints = blackbox.constraints(x, y, turbine_diameters=diameters)

    
    print('\nHeights after elevation function')
    for height in heights:
        print(height)
    print('\nDiameters')
    for diameter in diameters:
        print(diameter)
    print('\nyaw angles')
    for angle in yaw_angles:
        print(angle)

    # Return the right objective function
    if wind_farm_data.obj_function.lower() == 'aep':
        return f"AEP                : {aep} GWh\nSpacing constraint : {constraints['spacing']} m\nPlacing constraint : {constraints['placing']} m"
    elif wind_farm_data.obj_function.lower() == 'roi':
        turbines_properties = {'models' : models, 'heights' : heights, 'default_heights' : [wind_farm_data.wind_turbines.hub_height(model) for model in models]}
        roi = blackbox.ROI(turbines_properties, aep)
        return f"ROI : {roi}"
    else:
        turbines_properties = {'models' : models, 'heights' : heights, 'default_heights' : [wind_farm_data.wind_turbines.hub_height(model) for model in models]}
        lcoe = blackbox.LCOE(turbines_properties, aep)
        return f"LCOE : {lcoe}"


class Blackbox:
    def __init__(self, wind_farm, buildable_zone, lifetime, sale_price):
        self.wind_farm      = wind_farm
        self.buildable_zone = buildable_zone
        self.lifetime       = lifetime
        self.sale_price     = sale_price # per MW
    
    def compute_aep(self, x, y, ws, wd, types, heights, yaw_angles):
        return float(self.wind_farm(x, y, ws=ws, wd=wd, type=types, time=True, n_cpu=None, h=heights, yaw=yaw_angles).aep().sum())

    def ROI(self, chosen_turbines_properties, aep):
        chosen_models = chosen_turbines_properties['models']
        heights = chosen_turbines_properties['heights']
        default_heights = chosen_turbines_properties['default_heights']
        cost_over_lifetime = lifetimeCost(chosen_models, heights, default_heights, self.lifetime)
        return aep * self.sale_price - cost_over_lifetime

    def LCOE(self, chosen_turbines_properties, aep):
        chosen_models = chosen_turbines_properties['models']
        heights = chosen_turbines_properties['heights']
        default_heights = chosen_turbines_properties['default_heights']
        cost_over_lifetime = lifetimeCost(chosen_models, heights, default_heights, self.lifetime)
        return cost_over_lifetime / (aep * self.lifetime)
    
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