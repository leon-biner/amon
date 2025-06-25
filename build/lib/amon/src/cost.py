# cost.py
from amon.src.utils import AVAILABLE_TURBINES_NAMES

V80_COST         = { 'price'      : 100,                        # Purchase price of the turbine
                     'parts'      : [100, 100, 100, 100, 100],  # Purchase price of its parts
                     'parts_life' : [10, 10, 10, 10, 10],       # Life expectancy of its parts in years
                     'install'    : 10,                         # Cost of installing the turbine
                     'h_augment'  : 3 }                         # Cost of augmenting the height, in $USD per meter

OPEN_WIND_COST   = { 'price'      : 500,
                     'parts'      : [100, 100, 100, 100, 100],
                     'parts_life' : [10, 10, 10, 10, 10],
                     'install'    : 10,
                     'h_augment'  : 3 }

IEA_22MW_COST    = { 'price'      : 100,
                     'parts'      : [100, 100, 100, 100, 100],
                     'parts_life' : [10, 10, 10, 10, 10],
                     'install'    : 10,
                     'h_augment'  : 3 }

V82_COST         = { 'price'      : 110,
                     'parts'      : [100, 100, 100, 100, 100],
                     'parts_life' : [10, 10, 10, 10, 10],
                     'install'    : 10,
                     'h_augment'  : 3 }

BESPOKE_6MW_COST = { 'price'      : 100,
                     'parts'      : [100, 100, 100, 100, 100],
                     'parts_life' : [10, 10, 10, 10, 10],
                     'install'    : 10,
                     'h_augment'  : 3 }

IEA_3_4_MW       = { 'price'      : 100,
                     'parts'      : [100, 100, 100, 100, 100],
                     'parts_life' : [10, 10, 10, 10, 10],
                     'install'    : 10,
                     'h_augment'  : 3 }


WIND_TURBINES_COSTS = [ V80_COST, OPEN_WIND_COST, IEA_22MW_COST, V82_COST, BESPOKE_6MW_COST, IEA_3_4_MW ] # Indices consistent with data/wind_turbines folder

# @brief   : Calculates the cost of the windfarm over its lifetime
# @params  : - chosen_models   : list of integers, each corresponding to the id of the model chosen, one integer for each turbine placed
#            - heights         : list of floats corresponding to the height of each turbine
#            - default_heights : list of floats corresponding to the height each turbine has by default
#            - lifetime        : lifetime, in years, used for the calculation
# @returns : float, lifetime cost of the wind farm
def lifetimeCost(chosen_models, heights, default_heights, lifetime): # might be a good idea to make an object with the turbine's properties here instead of passing heights as parameters 
    cost = 0
    for chosen_model, height, default_height in zip(chosen_models, heights, default_heights):
        price          = WIND_TURBINES_COSTS[chosen_model]['price']
        parts_cost     = WIND_TURBINES_COSTS[chosen_model]['parts']
        parts_life     = WIND_TURBINES_COSTS[chosen_model]['parts_life']
        install_cost   = WIND_TURBINES_COSTS[chosen_model]['install']
        h_augment_cost = WIND_TURBINES_COSTS[chosen_model]['h_augment']
        for part_cost, part_life in zip(parts_cost, parts_life):
            cost += part_cost * lifetime / part_life
        height_added = height - default_height
        cost += h_augment_cost * height_added
        cost += price + install_cost

    return cost