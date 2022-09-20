import pandas as pd
import matplotlib.pyplot as plt

var = pd.read_excel('/home/maria/Network-model-comparison/Tests/Network comparison results.xlsx', skiprows=2)
print(var)
var.head()

varNew = var[['Topology','Node number','Quantum Fidelity','Classical Fidelity','Quantum Speed','Classical Speed']]
varNew.head()

plt.plot(var['column name'])
var.head()

plt.savefig('test.png')