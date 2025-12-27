import pandas as pd
import numpy as np

values = np.random.randint(45000, 55000, size=24)
pd.DataFrame({"ercot": values}).to_csv("last_known_load.csv", index=False)

print("Fallback file created: last_known_load.csv")
