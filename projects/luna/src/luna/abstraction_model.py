from luna.utils.interfaces import Grid
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans as KMeansClustering
from tqdm import tqdm
import os
import pickle

class AbstractModel(object):
    def __init__(self):
        self.clustering = None
    
    def fit_transform(self, partition_model_path, train_set, val_set, test_set):
        if os.path.exists(partition_model_path):
            print("Loading partition model...")
            with open(partition_model_path, "rb") as f:
                self.clustering = pickle.load(f)
            print("Finished loading partition model!")
        else:
            self.clustering.fit(train_set)
            # save partition
            with open(partition_model_path, "wb") as f:
                pickle.dump(self.clustering, f)
        cluster_labels_train = self.clustering.predict(train_set)
        cluster_labels_val = self.clustering.predict(val_set) if len(val_set) != 0 else []
        cluster_labels_test = self.clustering.predict(test_set)
        print("Training set size: {}".format(len(cluster_labels_train)))
        print("Validation set size: {}".format(len(cluster_labels_val)))
        print("Test set size: {}".format(len(cluster_labels_test)))
        return cluster_labels_train, cluster_labels_val, cluster_labels_test

class GMM(AbstractModel):
    def __init__(self, components):
        super().__init__()
        self.clustering = GaussianMixture(n_components=components, covariance_type='diag')


class KMeans(AbstractModel):
    def __init__(self, components):
        super().__init__()
        self.clustering = KMeansClustering(components)


class RegularGrid(AbstractModel):
    def __init__(self, components, step):
        super().__init__()
        self.components = components
        self.step = step

    def pca_to_abstract_traces(self, grid, pca_traces):
        """Convert PCA traces to abstract traces"""
        abst_traces = []
        for trace in tqdm(pca_traces, desc="Grid: PCA to Abstract Traces"):
            abst_trace = []
            for i in range(0, len(trace) - self.step):
                con_pattern = trace[i : i + self.step]
                con_pattern = np.mean(con_pattern, axis=0)
                con_pattern = np.array([con_pattern])
                abs_pattern = grid.state_abstract(con_pattern)[0]
                abst_trace.append(abs_pattern)
            if len(abst_trace) < 2:
                abst_trace = [-1, -1]
            abst_traces.append(abst_trace)

        return abst_traces

    def fit_transform(self, partition_model_path, train_set, val_set, test_set):
        # step = 1 for regular analysis, 2 or greater means multi-step analysis
        # compute lower/upper bound for grid partitioning
        stacked_pca_traces = np.vstack(train_set)
        lbd = np.min(stacked_pca_traces, axis=0)
        ubd = np.max(stacked_pca_traces, axis=0)

        ############################ two important args for grid-based abstraction ##################
        print("####### Grid Partitioning #######")

        grid_num = self.components  # the grid number on each dimension of the reducted features
        if os.path.exists(partition_model_path):
            print("Loading partition model...")
            with open(partition_model_path, "rb") as f:
                grid = pickle.load(f)
            print("Finished loading partition model!")
        else:
            grid = Grid(lbd, ubd, grid_num)  # create a grid-based abstracter
            # save grid
            with open(partition_model_path, "wb") as f:
                pickle.dump(grid, f)
        self.clustering = grid
        print(f"grid_num: {grid_num}")

        train_abst_traces = self.pca_to_abstract_traces(grid, train_set)
        # train_abst_traces = [item for sublist in train_abst_traces for item in sublist]
        val_abst_traces = self.pca_to_abstract_traces(grid, val_set) if len(val_set) != 0 else []
        # val_abst_traces = [item for sublist in val_abst_traces for item in sublist]
        test_abst_traces = self.pca_to_abstract_traces(grid, test_set)
        # test_abst_traces = [item for sublist in test_abst_traces for item in sublist]

        # train_abst_traces = [item for sublist2d in train_abst_traces for sublist in sublist2d for item in sublist]
        # val_abst_traces = [item for sublist2d in val_abst_traces for sublist in sublist2d for item in sublist]
        # test_abst_traces = [item for sublist2d in test_abst_traces for sublist in sublist2d for item in sublist]

        return train_abst_traces, val_abst_traces, test_abst_traces
       