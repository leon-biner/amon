from amon.src.utils import AVAILABLE_TURBINES_NAMES

V80_COST         = { 'price'       : 100,
                     'parts'       : [100, 100, 100, 100, 100],
                     'life_exp'    : [10, 10, 10, 10, 10],
                     'install'     : 10,
                     'h_reduction' : 1,
                     'cut'         : 1,
                     'h_augment'   : 3 }

OPEN_WIND_COST   = { 'price'       : 500,
                     'parts'       : [100, 100, 100, 100, 100],
                     'life_exp'    : [10, 10, 10, 10, 10],
                     'install'     : 10,
                     'h_reduction' : 1,
                     'cut'         : 1,
                     'h_augment'   : 3 }

IEA_22MW_COST    = { 'price'       : 100,
                     'parts'       : [100, 100, 100, 100, 100],
                     'life_exp'    : [10, 10, 10, 10, 10],
                     'install'     : 10,
                     'h_reduction' : 1,
                     'cut'         : 1,
                     'h_augment'   : 3 }

V82_COST         = { 'price'       : 110,
                     'parts'       : [100, 100, 100, 100, 100],
                     'life_exp'    : [10, 10, 10, 10, 10],
                     'install'     : 10,
                     'h_reduction' : 1,
                     'cut'         : 1,
                     'h_augment'   : 3 }

BESPOKE_6MW_COST = { 'price'       : 100,
                     'parts'       : [100, 100, 100, 100, 100],
                     'life_exp'    : [10, 10, 10, 10, 10],
                     'install'     : 10,
                     'h_reduction' : 1,
                     'cut'         : 1,
                     'h_augment'   : 3 }

IEA_3_4_MW       = { 'price'       : 100,
                     'parts'       : [100, 100, 100, 100, 100],
                     'life_exp'    : [10, 10, 10, 10, 10],
                     'install'     : 10,
                     'h_reduction' : 1,
                     'cut'         : 1,
                     'h_augment'   : 3 }


WIND_TURBINES_COSTS = { 'V80'         : V80_COST,
                        'OpenWind'    : OPEN_WIND_COST,
                        'IEA_22MW'    : IEA_22MW_COST,
                        'V82'         :  V82_COST,
                        'Bespoke_6MW' : BESPOKE_6MW_COST,
                        'IEA_3.4MW'   : IEA_3_4_MW }


def lifetimeCost(chosen_models, heights, default_heights, lifetime): # might be a good idea to make an object with the turbine's properties here instead of passing heights as parameters
    # The models_chosen are the optimisation variable
    # The models_available are those specified in the param file
    wt_costs = [WIND_TURBINES_COSTS[name] for name in AVAILABLE_TURBINES_NAMES]
    # Now the models_chosen list refers directly to wt_costs
    cost = 0
    for chosen_model, height, default_height in zip(chosen_models, heights, default_heights):
        price            = wt_costs[chosen_model]['price']
        parts_cost       = wt_costs[chosen_model]['parts']
        life_exp         = wt_costs[chosen_model]['life_exp']
        install_cost     = wt_costs[chosen_model]['install']
        h_reduction_cost = wt_costs[chosen_model]['h_reduction']
        cut_cost         = wt_costs[chosen_model]['cut']
        h_augment_cost   = wt_costs[chosen_model]['h_augment']
        for part_cost, part_life in zip(parts_cost, life_exp):
            cost += part_cost * lifetime / part_life
        height_added = height - default_height
        if height_added < 0:
            cost += cut_cost + h_reduction_cost * -height_added
        else:
            cost += h_augment_cost * height_added
        cost += price + install_cost
    return cost
