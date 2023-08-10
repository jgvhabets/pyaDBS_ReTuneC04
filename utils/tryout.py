import numpy as np
import pandas as pd


a = np.arange(24)
print(a)
a = np.reshape(a, (3, 8), order='C')

print(a)
