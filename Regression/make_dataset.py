# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 17:23:50 2020

@author: junes
"""

import os
os.chdir('F:/DigitalTwin_Data/python')
import convert
import pandas  as pd
from tqdm import tqdm

path = 'F:/DigitalTwin_Data/Normal_Condition_Test/태양전기/20.05.27_데이터 (정상상태)/'
dir_list = os.listdir(path +'192.168.100.100/Curr1')[5:]#140 train 141~ test 
cur1_list = []
cur2_list = []
cur3_list = []
vol1_list = []   
vol2_list = []
vol3_list = []
tacho_list = []
factor1_list = []
factor2_list = []
factor3_list = []

for i in tqdm(range(len(dir_list))):
    time = dir_list[i][-21:]
    cur1 = convert.filtering(convert.sampling(convert.conversion(path + '192.168.100.100/Curr1/Curr1'+time,'cur'),10),10)
    cur2 = convert.filtering(convert.sampling(convert.conversion(path + '192.168.100.100/Curr2/Curr2'+time,'cur'),10),10)
    cur3 = convert.filtering(convert.sampling(convert.conversion(path + '192.168.100.101/Curr3/Curr3'+time,'cur'),10),10)
    vol1 = convert.filtering(convert.sampling(convert.conversion(path + '192.168.100.100/Volt1/Volt1'+time,'cur'),10),10)
    vol2 = convert.filtering(convert.sampling(convert.conversion(path + '192.168.100.100/Volt2/Volt2'+time,'cur'),10),10)
    vol3 = convert.filtering(convert.sampling(convert.conversion(path + '192.168.100.101/Volt3/Volt3'+time,'cur'),10),10)
    tacho = convert.rpm(convert.sampling(convert.conversion(path + '192.168.100.102/TACHO/tacho'+time,'cur'),10),58,5120)
    cur1_hz = convert.hertz(cur1,58)
    cur2_hz = convert.hertz(cur2,58)
    cur3_hz = convert.hertz(cur3,58)
    vol1_hz = convert.hertz(vol1,58)
    vol2_hz = convert.hertz(vol2,58)
    vol3_hz = convert.hertz(vol3,58)
    factor1 = convert.power_factor(cur1,vol1,58)
    factor2 = convert.power_factor(cur2,vol2,58)
    factor3 = convert.power_factor(cur3,vol3,58)
    cur1_list.append(cur1_hz)
    cur2_list.append(cur2_hz)
    cur3_list.append(cur3_hz)
    vol1_list.append(vol1_hz)   
    vol2_list.append(vol2_hz)
    vol3_list.append(vol3_hz)
    tacho_list.append(tacho)
    factor1_list.append(factor1)
    factor2_list.append(factor2)
    factor3_list.append(factor3)
    
    
    

    