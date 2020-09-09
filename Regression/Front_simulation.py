# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 10:36:09 2020

@author: junes
"""

import numpy as np
from sklearn.linear_model import LinearRegression, ElasticNet
from sklearn.neural_network import MLPRegressor 
from sklearn.preprocessing import StandardScaler





scalerX = StandardScaler()
scalerX.fit(X_train)
X_train_scaled = scalerX.transform(X_train)
X_test_scaled = scalerX.transform(X_test)
scalerY = StandardScaler()
scalerY.fit(y_train)
y_train_scaled = scalerY.transform(y_train)
y_test_scaled = scalerY.transform(y_test)

models =  MLPRegressor(hidden_layer_sizes=[512, 4], max_iter=5000, alpha=0.005, random_state=42)

regre = models.fit()