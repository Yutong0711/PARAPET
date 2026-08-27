import numpy as np
import pickle

class AbstractModel():
    def __init__(self):
        self.initial = []
        self.final = []
        
class Grid(AbstractModel):
    '''
    Multiple DTMCs from a set of sets of traces
    traces: a set of sets of traces
    '''
    def __init__(self, min_val, max_val, grid_num, clipped=False):
        super().__init__()
        self.min = min_val
        self.max = max_val
        self.k = grid_num
        self.dim = max_val.shape[0]
        self.total_states = pow(grid_num,self.dim)
        self.unit = (max_val - min_val) / self.k
        self.clipped = clipped
        
    def state_abstract(self, con_states):
        con_states = con_states
        lower_bound = self.min
        upper_bound = self.max
        unit = (upper_bound - lower_bound)/self.k
        abs_states = np.zeros(con_states.shape[0],dtype=np.int8)
        
        #print(lower_bound)
        #print(upper_bound)
        indixes = np.where(unit == 0)[0]
        unit[indixes] = 1
        #print('unit:\t', unit)
        
        tmp = ((con_states-self.min)/unit).astype(int)
        if self.clipped:
            tmp = np.clip(tmp, 0, self.k-1)
        dims = tmp.shape[1]
        for i in range(dims):
            abs_states = abs_states + tmp[:,i]*pow(self.k, i)
#         abs_states = np.expand_dims(abs_states,axis=-1)
        abs_states = abs_states.tolist()
        return abs_states
    


def load_lists(filename):
    with open(filename, "rb") as f:
        list1, list2, list3 = pickle.load(f)
    return list1, list2, list3


def save_lists(list1, list2, list3, filename):
    with open(filename, "wb") as f:
        pickle.dump((list1, list2, list3), f)