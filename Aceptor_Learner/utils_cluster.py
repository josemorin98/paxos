# Librerias
import pandas as pd
import numpy as np
from datetime import datetime
import time
import random
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture


def read_CSV(name):
    return pd.read_csv("./data/"+name+".csv")


# Clustering-------------------------
def K_means(k,data_clima):
    X_clima = data_clima.iloc[:,[7,8,9,10]]
    kmeans = KMeans(n_clusters=k).fit(X_clima)
    k_labels = kmeans.predict(X_clima)
    return k_labels


def MixtureModel(k,data_clima):
    X_clima = data_clima.iloc[:,[7,8,9,10]]
    modelo_gmm = GaussianMixture(
                n_components    = k,
                covariance_type = 'full',
                random_state    = 123)
    modelo_gmm.fit(X_clima)
    k_labels = modelo_gmm.predict(X_clima)
    return k_labels