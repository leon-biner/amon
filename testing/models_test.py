import time

from py_wake.examples.data.iea37._iea37 import IEA37Site, IEA37WindTurbines
from py_wake.wind_farm_models.engineering_models import All2AllIterative
from py_wake.examples.data.iea37 import iea37_path
from py_wake.examples.data.iea37.iea37_reader import read_iea37_windfarm

from py_wake.deficit_models import NOJDeficit, TurboNOJDeficit, BastankhahGaussianDeficit ,IEA37SimpleBastankhahGaussianDeficit, NiayifarGaussianDeficit, ZongGaussianDeficit, CarbajofuertesGaussianDeficit, GCLDeficit
from py_wake.superposition_models import LinearSum, MaxSum
from py_wake.deficit_models import SelfSimilarityDeficit, SelfSimilarityDeficit2020, VortexCylinder, VortexDipole, RankineHalfBody, HybridInduction, Rathmann
from py_wake.rotor_avg_models import RotorCenter, GridRotorAvg, EqGridRotorAvg, GQGridRotorAvg, PolarGridRotorAvg, CGIRotorAvg, GaussianOverlapAvgModel
from py_wake.deflection_models import JimenezWakeDeflection, GCLHillDeflection
from py_wake.turbulence_models import STF2005TurbulenceModel, STF2017TurbulenceModel, GCLTurbulence, CrespoHernandez
from amon.src.windfarm_data import SafeSquaredSum

# All the GCLHill models are made to be used togethere and should only be used together
# GCLTurbulence(rotorAvgModel=rotor_avg_model)
# GCLHillDeflection(wake_deficitModel=wake_deficit_model)
# GCLDeficit

def main():
    n_wt = 64
    def getRotorAvgModel():
        return [ RotorCenter(), PolarGridRotorAvg(), EqGridRotorAvg(), CGIRotorAvg(4), CGIRotorAvg(7), CGIRotorAvg(9), CGIRotorAvg(21) ]
    def getWakeDefModels(rotor_avg_model):
        return [ NOJDeficit(rotorAvgModel=rotor_avg_model),
                 BastankhahGaussianDeficit(rotorAvgModel=rotor_avg_model, use_effective_ws=True),
                 ZongGaussianDeficit(rotorAvgModel=rotor_avg_model, use_effective_ws=True),
                 CarbajofuertesGaussianDeficit(rotorAvgModel=rotor_avg_model, use_effective_ws=True) ]
    def getSuperpModels():
        return [ MaxSum(), LinearSum(), SafeSquaredSum() ]
    def getBlockageModels(sup_model, rotor_model):
        return [ Rathmann(superpositionModel=sup_model, rotorAvgModel=rotor_model) ]
    def getDeflectionModels():
        return [ JimenezWakeDeflection() ]
    def getTurbModels(rotor_avg_model):
        return [ CrespoHernandez(rotorAvgModel=rotor_avg_model) ]
    
    differences = []
    rotor_avg_models = getRotorAvgModel()
    superposition_models = getSuperpModels()
    deflection_models = getDeflectionModels()
    for i_w in range(4):
        for i_s in range(3):
            for i_r in range(7):
                superposition_model = superposition_models[i_s]
                deflection_model = deflection_models[0]
                rotor_avg_model = rotor_avg_models[i_r]
                wake_deficit_model = getWakeDefModels(rotor_avg_models[i_r])[i_w]
                blockage_deficit_model = getBlockageModels(superposition_models[i_s], rotor_avg_models[i_r])[0]
                turbulence_model = getTurbModels(rotor_avg_models[i_r])[0]
                try:
                    start_time = time.time()
                    wfm = All2AllIterative( site                  = IEA37Site(n_wt),
                                            windTurbines          = IEA37WindTurbines(),
                                            wake_deficitModel     = wake_deficit_model,
                                            superpositionModel    = superposition_model,
                                            blockage_deficitModel = blockage_deficit_model,
                                            deflectionModel       = deflection_model,
                                            turbulenceModel       = turbulence_model,
                                            rotorAvgModel         = rotor_avg_model,
                                            convergence_tolerance = 1e-6 )
                    x, y, aep_ref = read_iea37_windfarm(iea37_path + 'iea37-ex%d.yaml' % n_wt)
                    aep_sim = wfm(x, y, tilt=0, yaw=0).aep().sum().item()
                    differences.append({
                        "aep": abs(aep_sim),
                        "indices": [i_w, i_s, i_r],
                        "time": time.time() - start_time
                    })
                    print("----------------------------------------------------")
                    print(f"wake_def: {wake_deficit_model.__class__.__name__}\nsuperp: {superposition_model.__class__.__name__}\nblock: {blockage_deficit_model.__class__.__name__}\ndeflection: {deflection_model.__class__.__name__}\nturbulence: {turbulence_model.__class__.__name__}\nrotor: {rotor_avg_model.__class__.__name__}")
                    print(f"\033[93mAEP\033[0m = {aep_sim:3.6f}, \033[94mTime\033[0m = {time.time() - start_time:3.6f}")
                except Exception:
                    print(f"Couldn't do [{i_w}, {i_s}, {i_r}]")

    sorted_time = sorted(differences, key=lambda d: d["time"])
    with open("sorted_time.txt", "w") as f:
        for diff in sorted_time:
            f.write(f"AEP: {diff['aep']:.6f}, Indices: {diff['indices']}, Time: {diff['time']:.2f} s\n")
main()
print('-----------------------')
wfm = All2AllIterative( site                  = IEA37Site(64),
                        windTurbines          = IEA37WindTurbines(),
                        wake_deficitModel     = CarbajofuertesGaussianDeficit(rotorAvgModel=GaussianOverlapAvgModel(), use_effective_ws=True),
                        superpositionModel    = SafeSquaredSum(),
                        blockage_deficitModel = Rathmann(superpositionModel=SafeSquaredSum(), rotorAvgModel=CGIRotorAvg(21)),
                        deflectionModel       = JimenezWakeDeflection(),
                        turbulenceModel       = CrespoHernandez(rotorAvgModel=CGIRotorAvg(21)),
                        rotorAvgModel         = GaussianOverlapAvgModel(),
                        convergence_tolerance = 1e-6 )
x, y, aep_ref = read_iea37_windfarm(iea37_path + 'iea37-ex%d.yaml' % 64)
aep_sim = wfm(x, y, tilt=0, yaw=0).aep().sum().item()
print(aep_sim)