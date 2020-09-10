# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 10:36:09 2020

@author: junes
"""

import pandas as pd
import numpy as np
from sklearn.neural_network import MLPRegressor 
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt


dataset = pd.read_csv('Front_simulation_dataset.csv')
x = dataset[['Line 1 Current RMS', 'Line 2 Current RMS',
       'Line 3 Current RMS', 'Line 1 Voltage RMS', 'Line 2 Voltage RMS',
       'Line 3 Voltage RMS', 'Line 1 power factor', 'Line 2 power factor',
       'Line 3 power factor','motor_temperature']]

y = dataset[['TachoSpeed(RPM)']]


X_train = x[:11571]
y_train = y[:11571]
X_test = x[11571:]
y_test = y[11571:]


scalerX = StandardScaler()
scalerX.fit(X_train)
X_train_scaled = scalerX.transform(X_train)
X_test_scaled = scalerX.transform(X_test)
scalerY = StandardScaler()
scalerY.fit(y_train)
y_train_scaled = scalerY.transform(y_train)
y_test_scaled = scalerY.transform(y_test)


model =  MLPRegressor(hidden_layer_sizes=[1024, 512, 4], max_iter=5000, alpha=0.005, random_state=42)

regre = model.fit(X_train_scaled,y_train_scaled)

print(model.__class__)
print(r2_score(y_train_scaled, model.predict(X_train_scaled)))
print(r2_score(y_test_scaled, model.predict(X_test_scaled)))

x = np.arange(len(y[:11571]))
plt.figure(figsize=(12, 6))
plt.scatter(x,y_train_scaled[:11571])
plt.scatter(x,model.predict(X_train_scaled))