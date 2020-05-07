from sklearn.base import BaseEstimator, ClusterMixin
from sklearn.exceptions import NotFittedError
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import pandas as pd
import numpy as np
import copy

class DFKMeans(BaseEstimator, ClusterMixin):
    def __init__(self, cluster_name, columns=None,
                 eval_inertia=False, eval_silhouette=False, eval_chi=False, eval_dbi=False,
                 **kwargs):
        self.cluster_name    = cluster_name
        self.columns         = columns
        self.model           = KMeans(**kwargs)
        self.eval_inertia    = eval_inertia
        self.eval_silhouette = eval_silhouette
        self.eval_chi        = eval_chi
        self.eval_dbi        = eval_dbi
        self.transform_cols  = None
        self.eval_df         = None
        
    def fit(self, X, y=None):
        self.columns        = X.columns if self.columns is None else self.columns
        self.transform_cols = [x for x in X.columns if x in self.columns]
        self.model.fit(X[self.transform_cols])

        self.eval_df = pd.DataFrame({
            'n_cluster': [x+1 for x in range(self.model.n_clusters)],
        })

        if any([self.eval_inertia, self.eval_silhouette, self.eval_chi, self.eval_dbi]):
            inertias    = []
            silhouettes = []
            chis        = []
            dbis        = []
            self.eval_df['centroid'] = self.eval_df['n_cluster'].apply(lambda x: [])

            tmp_X = X[self.transform_cols].copy()
            for x in range(self.model.n_clusters):
                model = copy.deepcopy(self.model)
                model.n_clusters = x+1
                model.fit(tmp_X)

                # Cluster centroid
                self.eval_df.at[x, 'centroid'] = model.cluster_centers_

                # Reference: https://blog.cambridgespark.com/how-to-determine-the-optimal-number-of-clusters-for-k-means-clustering-14f27070048f
                if self.eval_inertia:
                    inertias.append(model.inertia_)

                # Reference: https://towardsdatascience.com/clustering-metrics-better-than-the-elbow-method-6926e1f723a6
                if self.eval_silhouette:
                    silhouettes.append(np.nan if x == 0 else silhouette_score(tmp_X, model.labels_, metric='euclidean', random_state=model.random_state))

                # Reference: https://stats.stackexchange.com/questions/52838/what-is-an-acceptable-value-of-the-calinski-harabasz-ch-criterion
                if self.eval_chi:
                    chis.append(np.nan if x == 0 else calinski_harabasz_score(tmp_X, model.labels_))

                # Reference: https://stackoverflow.com/questions/59279056/davies-bouldin-index-higher-or-lower-score-better
                if self.eval_dbi:
                    dbis.append(np.nan if x == 0 else davies_bouldin_score(tmp_X, model.labels_))

            if self.eval_inertia:
                self.eval_df['inertia'] = inertias

            if self.eval_silhouette:
                self.eval_df['silhouette'] = silhouettes

            if self.eval_chi:
                self.eval_df['calinski_harabasz'] = chis

            if self.eval_dbi:
                self.eval_df['davies_bouldin'] = dbis

        return self
    
    def predict(self, X):
        if self.transform_cols is None:
            raise NotFittedError(f"This {self.__class__.__name__} instance is not fitted yet. Call 'fit' with appropriate arguments before using this estimator.")

        new_X = X.copy()
        new_X[self.cluster_name] = self.model.predict(X[self.transform_cols])

        return new_X
    
    def fit_predict(self, X, y=None):
        return self.fit(X).predict(X)