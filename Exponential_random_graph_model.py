#The Exponential Graph Model 

import scipy as sp
from scipy.misc import comb
from itertools import product
from pymc import  Normal, Bernoulli, InvLogit, MCMC,deterministic

# functions to get delta matrices
def mutualDelta(am):
    return(am.copy().transpose())

def istarDelta(am,k):
    if k == 1:
        # if k == 1 then this is just density
        res = sp.ones(am.shape)
        return(res)
    res = sp.zeros(am.shape,dtype=int)
    n = am.shape[0]
    for i,j in product(xrange(n),xrange(n)):
        if i!=j:
            nin = am[:,j].sum()-am[i,j]
            res[i,j] = comb(nin,k-1,exact=True)
    return(res)

def ostarDelta(am,k):
    if k == 1:
        # if k == 1 then this is just density
        res = sp.ones(am.shape)
        return(res)
    res = sp.zeros(am.shape,dtype=int)
    n = am.shape[0]
    for i,j in product(xrange(n),xrange(n)):
        if i!=j:
            nin = am[i,:].sum()-am[i,j]
            res[i,j] = comb(nin,k-1,exact=True)
    return(res)

def makeModel(adjMat):

    # define and name the deltas
    termDeltas = {
        'deltamutual':mutualDelta(adjMat),
        'deltaistar1':istarDelta(adjMat,1),
        'deltaistar2':istarDelta(adjMat,2),
        'deltaistar3':istarDelta(adjMat,3),
        'deltaostar2':ostarDelta(adjMat,2)
    }

    # create term list with coefficients
    termList = []
    coefs = {}
    for dName,d in termDeltas.items():
        tName = 'theta'+dName[5:]
        coefs[tName] = Normal(tName,0,0.001,value=sp.rand()-0.5)
        termList.append(d*coefs[tName])

    # get individual edge probabilities
    @deterministic(trace=False,plot=False)
    def probs(termList=termList):
        probs = 1./(1+sp.exp(-1*sum(termList)))
        probs[sp.diag_indices_from(probs)]= 0
        return(probs)

    # define the outcome as 
    outcome = Bernoulli('outcome',probs,value=adjMat,observed=True)

    return(locals())

#-----------------------------------------------------------------

if __name__ == '__main__':
    # load the prison data
    with open('prison.dat','r') as f:
        rowList = list()
        for l in f:
            rowList.append([int(x) for x in l.strip().split(' ')])
        adjMat = sp.array(rowList)
    
    # make the model as an MCMC object
    m = makeModel(adjMat)
    mc = MCMC(m)

    # estimate
    mc.sample(30000,1000,50)