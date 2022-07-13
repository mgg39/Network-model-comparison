import networkx as nx #networkx lib
import matplotlib.pyplot as plt
  
I= nx.erdos_renyi_graph(10,0) #N=10, p =0
nx.draw(I, with_labels=True)
plt.show()

