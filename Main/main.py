from network_generator import network

#setting variables
n_nodes = 10
t_topology = "line"
n_distance = 1

network1 = network("quantum",n_nodes,t_topology,n_distance) #,noise_model)
network2 = network("classic",n_nodes,t_topology,n_distance) #noise_model)

