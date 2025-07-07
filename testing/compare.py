import time

from py_wake.examples.data.hornsrev1 import Hornsrev1Site, HornsrevV80
from py_wake.wind_farm_models.engineering_models import All2AllIterative
from py_wake.deficit_models.gaussian import BastankhahGaussianDeficit
from py_wake.deficit_models import ( SelfSimilarityDeficit, VortexCylinder, VortexDipole, RankineHalfBody, HybridInduction, Rathmann,
    RankineHalfBody, SelfSimilarityDeficit2020,
)

# Setup site and turbine model
site = Hornsrev1Site()
windTurbines = HornsrevV80()
x, y = site.initial_position.T

# Define blockage models
blockage_models = [
    RankineHalfBody(),
    VortexDipole(),
    RankineHalfBody(),
    HybridInduction(),
    Rathmann()
]

# Store AEP results
aep_results = {}

# Loop over each model and compute AEP
st = time.time()
for model in blockage_models:
    wfm = All2AllIterative(
        site=site,
        windTurbines=windTurbines,
        wake_deficitModel=BastankhahGaussianDeficit(),
        blockage_deficitModel=model
    )
    sim_res = wfm(x, y)
    aep = sim_res.aep().sum()  # Total AEP in GWh
    aep_results[model.__class__.__name__] = aep
    print(model.__class__.__name__, end='\n----------------\n')
    print(time.time()-st)

# Print results
print("Blockage Model Comparison on Hornsrev1 (Total AEP in GWh):")
for name, aep in aep_results.items():
    print(f"{name:<25}: {aep:.2f} GWh")
