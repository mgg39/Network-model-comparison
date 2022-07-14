#Complete multipartite graph with the specified block sizes

import networkx as nx #networkx lib
import matplotlib.pyplot as plt
from Model_variables import bl_sz

I= nx.complete_multipartite_graph(bl_sz+1) #block sizes=10
nx.draw(I, with_labels=True)
plt.show()
