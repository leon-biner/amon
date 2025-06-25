import numpy as np

def elevationInstance5(x, y):
    return (
        10 * np.sin(0.001 * x) * np.cos(0.001 * y) +
        5 * np.sin(0.005 * y) +
        15 * np.sinc(0.002 * (x - 150))
    )