import networkx as nx #networkx lib
import matplotlib.pyplot as plt
  
I= nx.complete_multipartite_graph(bl_sz) #block sizes=10
nx.draw(I, with_labels=True)
plt.show()