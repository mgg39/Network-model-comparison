import networkx as nx

#type : quantum, classic
#nodes : n of desired nodes
#topology (2d) : line, star, grid, cycle
#noise model : set to none for now
def network(type,nodes,topology): #,noise_model)
    available_types = ['quantum','classic']
    available_topologies = ['star_graph','grid_2d_graph','cycle_graph']

    for ty in available_types:
        if type == ty:
            connection = ty
        '''
        else:
            print("That was not a valid connection type. \n Valid connection types are quantum and classic Please Try again...")
        '''
    for to in available_topologies:
        if topology == 'star_graph':
            network = nx.star_graph(nodes)
        elif topology == 'grid_2d_graph':
            network = nx.grid_2d_graph(nodes)
        elif topology == 'cycle_graph':
            network = nx.cycle_graph(nodes)
        '''
        else:
            print("That was not a valid topology type. \n Valid connection types are star_graph, grid_2d_graph, & cycle_graph. Please Try again...")
        '''
    return network

print(network('classic',5,'star_graph'))