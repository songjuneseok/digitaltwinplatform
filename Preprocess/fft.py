# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 14:04:00 2020

@author: junes
"""
import os
import numpy as np
path = 'F:/DigitalTwin_Data/Normal_Condition_Test/태양전기/20.05.27_데이터 (정상상태)/192.168.100.102/TACHO'
os.chdir(path)
dir_list = os.listdir()
#tacho_2020_05_27_16_06.dat
tacho = np.fromfile(dir_list[60], dtype = np.int16)

sep_tacho = []
i = 0 
while True:    
    sec_data = tacho[i*51200:(i+1)*51200]
    sep_tacho.append(list(sec_data))
    i = i +1
    if i >= 58:
        break


Ts = 1/51200
Fs = 1/Ts
n = len(sep_tacho[1])
T = n/Fs
Y = np.fft.fft(sep_tacho[1])/n 
k = np.arange(n)