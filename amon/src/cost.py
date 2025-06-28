# cost.py
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import weibull_min

# The baseline for all other turbines is the V80, which is the most average turbine of the time of the data used in the study
# For this first version, I will linearly ajust the price of the parts and of the other turbines according to their maximum power output compared to the V80's

rng = np.random.default_rng(None)

v80_parts_costs    = { 'rotor'        : 162,
                       'main_bearing' : 110,
                       'gearbox'      : 202,
                       'generator'    : 150 } # In thousands of dollars

# These calculations will dissapear and the data will be hardcoded, this is just to start
openwind_parts_costs  = {part : cost * 10.5 / 2 for part, cost in v80_parts_costs.items()}
iea_22_parts_costs    = {part : cost * 22.0 / 2 for part, cost in v80_parts_costs.items()}
v82_parts_costs       = {part : cost * 1.65 / 2 for part, cost in v80_parts_costs.items()}
bespoke_6_parts_costs = {part : cost * 6.00 / 2 for part, cost in v80_parts_costs.items()}
iea_3_4_parts_costs   = {part : cost * 3.37 / 2 for part, cost in v80_parts_costs.items()}

# v80_loss_per_month = { 'rotor'        : 0.5,
                       # 'main_bearing' : 0.25,
                       # 'gearbox'      : 1,
                       # 'generator'    : 0.45 } # In thousands of dollars
                
# The definition of the scale parameter is different in the paper, the usual lambda is theta raised to the power of -1/beta
beta  = { 'rotor'        : 3,
          'main_bearing' : 2,
          'gearbox'      : 3,
          'generator'    : 2 } # Time units in months

theta = { 'rotor'        : 1e-6,
          'main_bearing' : 6.4e-5,
          'gearbox'      : 1.95e-6,
          'generator'    : 8.26e-5 } # Time units in months


V80_COST         = { 'price'      : 400,                        # Purchase price of the turbine ($1000)
                     'parts'      : v80_parts_costs,            # Purchase price of its parts
                     'install'    : 100,                        # Cost of installing the turbine
                     'h_augment'  : 3 }                         # Cost of augmenting the height, in $USD per meter

OPEN_WIND_COST   = { 'price'      : 500,
                     'parts'      : openwind_parts_costs,
                     'install'    : 10,
                     'h_augment'  : 3 }

IEA_22MW_COST    = { 'price'      : 100,
                     'parts'      : iea_22_parts_costs,
                     'install'    : 10,
                     'h_augment'  : 3 }

V82_COST         = { 'price'      : 110,
                     'parts'      : v82_parts_costs,
                     'install'    : 10,
                     'h_augment'  : 3 }

BESPOKE_6MW_COST = { 'price'      : 100,
                     'parts'      : bespoke_6_parts_costs,
                     'install'    : 10,
                     'h_augment'  : 3 }

IEA_3_4_MW       = { 'price'      : 100,
                     'parts'      : iea_3_4_parts_costs,
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
        parts_replacements = getNbReplacements(lifetime)
        for part_cost, nb_replacements in zip(parts_cost.values(), parts_replacements.values()):
            cost += part_cost * nb_replacements
        height_added = height - default_height
        if height_added > 0:
            cost += h_augment_cost * height_added
        cost += price + install_cost

    return cost

def getNbReplacements(lifetime, details=None):
    time.sleep(1.5)
    nb_replacements = {}
    for part_name in beta:
        k = beta[part_name]
        lambd = theta[part_name]**(-1/k)
        nb = 0
        total_lifetime = 0
        if details:
            print(f"Part : {part_name}")
            print("---------------------------")
            print(f"k = {k}, lambda = {lambd:.4f}")
        while True:
            part_lifespan = weibull_min.rvs(k, scale=lambd, random_state=rng)
            if details:
                print(f"For replacement {nb} : lifespan = {part_lifespan:.2f} months")
            total_lifetime += part_lifespan
            if total_lifetime >= lifetime:
                break
            nb += 1
        nb_replacements[part_name] = nb
        if details:
            print(f"Total replacements needed  : {nb}")
            print(f"Cost of replacements : ${nb * v80_parts_costs[part_name]} 000")
            print(f"Total part lifetime : {total_lifetime:.2f} months\n")
    return nb_replacements

def plotWeibullPdfs(lifetime):
    x = np.linspace(0, lifetime, lifetime*10)
    for part in beta:
        k = beta[part]
        lambd = theta[part]**(-1/k)
        pdf = weibull_min.pdf(x, c=k, scale=lambd)
        plt.plot(x, pdf, label=part)
    plt.axvline(x=240, color='tab:red', linestyle='dotted', label='Wind farm lifetime')
    plt.title("Probability density function of lifetime of main wind turbine parts")
    plt.xlabel("Months")
    plt.ylabel("Probability")
    plt.grid()
    plt.legend()
    plt.show()

if __name__ == '__main__':
    getNbReplacements(240)
    # plotWeibullPdfs(240)