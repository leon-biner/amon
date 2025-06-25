import shapely
from pathlib import Path

from py_wake.wind_farm_models.engineering_models import All2AllIterative

from amon.src.cost import lifetimeCost
from amon.src.utils import getPoint, getPath, MAX_TURBINE_HEIGHTS
from amon.src.windfarm_data import WindFarmData


# NOTE : The distinction between types and models is as follows : type is the index of the chosen model in the param file specified models, and model is the index of the model in the available models
#        Example : there are models 1, 3, 4 in the param file, the type 3 is the model 4.
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

    budget = wind_farm_data.budget

    blackbox = Blackbox(wind_farm, buildable_zone, 20, 100, budget)

    # Get the point to evaluate
    point_filepath = getPath(args.point, includes_file=True)
    point = getPoint(point_filepath)
    x, y = [float(x) for x in point['coords'][0::2]], [float(y) for y in point['coords'][1::2]]
    types = point['types']
    models = [wind_farm_data.wind_turbines_models[i] for i in types]
    
    diameters = [wind_farm_data.wind_turbines.diameter(i) for i in types]
    elevation_function = wind_farm_data.elevation_function
    default_heights = [wind_farm_data.wind_turbines.hub_height(type_) for type_ in types]
    heights = point['heights'] if point['heights'] is not None else default_heights # Actual height of the turbine
    absolute_heights = [] # Height with respect to the terrain's origin
    if heights is None:
        for x_i, y_i, default_height in zip(x, y, default_heights): # If height not specified, the model's default height is used
            absolute_heights.append(default_height + elevation_function(x_i, y_i))
    else:
        for height, x_i, y_i in zip(heights, x, y):
            absolute_heights.append(height + elevation_function(x_i, y_i))
    yaw_angles = point['yaw_angles']

    if not (len(x) == len(y) == len(types) == len(absolute_heights) == len(yaw_angles)):
        raise ValueError("\033[91mError\033[0m: All fields of evaluated point must have the same dimensions")

    # Calculate constraints
    aep = blackbox.AEP(x, y, ws=wind_farm_data.WS_BB, wd=wind_farm_data.WD_BB, types=types, heights=absolute_heights, yaw_angles=yaw_angles)
    constraints = blackbox.constraints(x, y, models, diameters, heights, default_heights)
    for name, value in constraints.items():
        print(f"{name} constraint : {value}")


    # Return the right objective function
    if wind_farm_data.obj_function.lower() == 'aep':
        return f"AEP : {aep} GWh"
    elif wind_farm_data.obj_function.lower() == 'roi':
        roi = blackbox.ROI(models, heights, default_heights)
        return f"ROI : {roi}"
    else:
        lcoe = blackbox.LCOE(models, heights, default_heights)
        return f"LCOE : {lcoe}"


class Blackbox:
    def __init__(self, wind_farm, buildable_zone, lifetime, sale_price, budget):
        self.wind_farm      = wind_farm
        self.buildable_zone = buildable_zone
        self.lifetime       = lifetime
        self.sale_price     = sale_price # per MW
        self.budget         = budget
    
    def AEP(self, x, y, ws, wd, types, heights, yaw_angles):
        self.aep = float(self.wind_farm(x, y, ws=ws, wd=wd, type=types, time=True, n_cpu=None, h=heights, yaw=yaw_angles).aep().sum())
        return self.aep

    def ROI(self, chosen_models, heights, default_heights):
        cost_over_lifetime = lifetimeCost(chosen_models, heights, default_heights, self.lifetime)
        return self.aep * self.sale_price - cost_over_lifetime

    def LCOE(self, chosen_models, heights, default_heights):
        cost_over_lifetime = lifetimeCost(chosen_models, heights, default_heights, self.lifetime)
        return cost_over_lifetime / (self.aep * self.lifetime)
    
    def constraints(self, x, y, chosen_models, diameters, heights, default_heights):
        # Spacing constraint
        points = [shapely.Point(x_i, y_i) for x_i, y_i in zip(x, y)]
        distance_matrix = [shapely.distance(point_i, points) for point_i in points]
        for i in range(len(points)):
            for j in range(0, i):
                distance_matrix[i][j] = 0
        
        sum_dist_between_wt = 0
        for i, list_distances in enumerate(distance_matrix):
            for j, d in enumerate(list_distances):
                if d == 0:
                    continue
                sum_dist_between_wt += min(d - diameters[i] - diameters[j], 0)
        sum_dist_between_wt *= -1

        # Placing constraint
        distances = shapely.distance(points, self.buildable_zone)
        sum_dist_buildable_zone = sum(distances)

        # Height constraints
        max_heights = [MAX_TURBINE_HEIGHTS[i] for i in chosen_models]
        min_heights = [diameter / 2 for diameter in diameters]
        sum_excess_height = 0
        for height, max_height, min_height in zip(heights, max_heights, min_heights):
            if height > max_height:
                sum_excess_height += height - max_height
            elif height < min_height:
                sum_excess_height += min_height - height

        # Budget constraint
        if self.budget is None:
            return { 'placing' : sum_dist_buildable_zone, 
                     'spacing' : sum_dist_between_wt,
                     'budget'  : None,
                     'height'  : sum_excess_height }

        cost_over_lifetime = lifetimeCost(chosen_models, heights, default_heights, self.lifetime)
        exceeded_budget = cost_over_lifetime - self.budget
        
        return { 'placing' : sum_dist_buildable_zone, 
                 'spacing' : sum_dist_between_wt,
                 'budget'  : exceeded_budget,
                 'height'  : sum_excess_height }