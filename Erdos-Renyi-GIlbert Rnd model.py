import networkx as nx #networkx lib
import matplotlib.pyplot as plt
from Model_variables import N, p
  
I= nx.erdos_renyi_graph(N,p) 
nx.draw(I, with_labels=True)
plt.show()

