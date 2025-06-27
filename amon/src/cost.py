# cost.py
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import weibull_min

# The baseline for all other turbines is the V80, which is the most average turbine of the time of the data used in the study
# For this first version, I will linearly ajust the price of the parts and of the other turbines according to their maximum power output compared to the V80's

# This calculation will dissapear eventually, the data will be hardcoded when we need to ajust it
v80_parts_costs    = { 'rotor'        : 162,
                       'main_bearing' : 110,
                       'gearbox'      : 202,
                       'generator'    : 150 } # In thousands of dollars

v80_loss_per_month = { 'rotor'        : 0.5,
                       'main_bearing' : 0.25,
                       'gearbox'      : 1,
                       'generator'    : 0.45 } # In thousands of dollars
                
beta_weibull  = { 'rotor'        : 3,
                  'main_bearing' : 2,
                  'gearbox'      : 3,
                  'generator'    : 2 } # Time units in months


theta_weibull = { 'rotor'        : 1e-6,
                  'main_bearing' : 6.4e-5,
                  'gearbox'      : 1.95e-6,
                  'generator'    : 8.26e-5 } # Time units in months


# Plot PDF
# x = np.linspace(0, 5, 100)
# pdf = weibull_min.pdf(x, c, scale=scale)

# plt.hist(data, bins=30, density=True, alpha=0.6, label="Samples")
# plt.plot(x, pdf, 'r-', lw=2, label=f"Weibull PDF (k={c}, λ={scale})")
# plt.legend()
# plt.show()


V80_COST         = { 'price'      : 100,                        # Purchase price of the turbine
                     'parts'      : [100, 100, 100, 100],       # Purchase price of its parts
                     'install'    : 10,                         # Cost of installing the turbine
                     'h_augment'  : 3 }                         # Cost of augmenting the height, in $USD per meter

OPEN_WIND_COST   = { 'price'      : 500,
                     'parts'      : [100, 100, 100, 100],
                     'install'    : 10,
                     'h_augment'  : 3 }

IEA_22MW_COST    = { 'price'      : 100,
                     'parts'      : [100, 100, 100, 100],
                     'install'    : 10,
                     'h_augment'  : 3 }

V82_COST         = { 'price'      : 110,
                     'parts'      : [100, 100, 100, 100],
                     'install'    : 10,
                     'h_augment'  : 3 }

BESPOKE_6MW_COST = { 'price'      : 100,
                     'parts'      : [100, 100, 100, 100],
                     'install'    : 10,
                     'h_augment'  : 3 }

IEA_3_4_MW       = { 'price'      : 100,
                     'parts'      : [100, 100, 100, 100],
                     'install'    : 10,
                     'h_augment'  : 3 }


WIND_TURBINES_COSTS = [ V80_COST, OPEN_WIND_COST, IEA_22MW_COST, V82_COST, BESPOKE_6MW_COST, IEA_3_4_MW ] # Indices consistent with data/wind_turbines folder

# @brief   : Calculates the cost of the windfarm over its lifetime
# @params  : - chosen_models   : list of integers, each corresponding to the id of the model chosen, one integer for each turbine placed
#            - heights         : list of floats corresponding to the height of each turbine
#            - default_heights : list of floats corresponding to the height each turbine has by default
#            - lifetime        : lifetime, in months, used for the calculation
# @returns : float, lifetime cost of the wind farm
def lifetimeCost(chosen_models, heights, default_heights, lifetime):
    cost = 0
    for chosen_model, height, default_height in zip(chosen_models, heights, default_heights):

        price          = WIND_TURBINES_COSTS[chosen_model]['price']
        parts_cost     = WIND_TURBINES_COSTS[chosen_model]['parts']
        install_cost   = WIND_TURBINES_COSTS[chosen_model]['install']
        h_augment_cost = WIND_TURBINES_COSTS[chosen_model]['h_augment']
        for part_cost, nb_replacements in zip(parts_cost.values(), parts_replacements.values()):
            cost += part_cost * lifetime / part_life
        height_added = height - default_height
        cost += h_augment_cost * height_added
        cost += price + install_cost

    return cost

def getNbReplacements(lifetime):
    nb_replacements = {}
    for part_name in beta_weibull:
        print(f"Doing part {part_name}")
        print("---------------------------")
        beta  = beta_weibull[part_name]
        theta = theta_weibull[part_name]**(-1/beta)
        print(fr"$\beta = ${beta}, $\theta = ${theta}")
        nb = 0
        total_lifetime = 0
        while True:
            part_lifespan = weibull_min.rvs(beta, scale=theta)
            print(f"For replacement {nb} : lifespan = {part_lifespan}")
            total_lifetime += part_lifespan
            if total_lifetime > lifetime:
                break
            nb += 1
        nb_replacements[part_name] = nb
        print(f"Total parts needed  : {nb}")
        print(f"Total part lifetime : {total_lifetime}")

print(getNbReplacements(240))
