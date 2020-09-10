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
dir_list = os.listdir(path +'192.168.100.100/Curr1')[5:290]#140 train 141~ test 
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
    cur1_list = cur1_list + cur1_hz
    cur2_list = cur2_list + cur2_hz
    cur3_list = cur3_list + cur3_hz  
    vol1_list = vol1_list + vol1_hz   
    vol2_list = vol2_list + vol2_hz
    vol3_list = vol3_list + vol3_hz
    tacho_list = tacho_list + tacho
    factor1_list = factor1_list + factor1
    factor2_list = factor2_list + factor2
    factor3_list = factor3_list + factor3

dataset_alue = pd.DataFrame(zip(cur1_list,cur2_list,cur3_list,vol1_list,vol2_list,vol3_list,factor1_list,factor2_list,factor3_list,tacho_list))
dataset_alue.columns = ['Line 1 Current RMS', 'Line 2 Current RMS', 'Line 3 Current RMS',
                   'Line 1 Voltage RMS', 'Line 2 Voltage RMS', 'Line 3 Voltage RMS',
                   'Line 1 power factor', 'Line 2 power factor', 'Line 3 power factor',
                   'TachoSpeed(RPM)']


motor_path = 'F:/DigitalTwin_Data/Normal_Condition_Test/태양전기/20.05.27_데이터 (정상상태)/192.168.100.103/pressure/'
motor_dir_list = os.listdir(motor_path)
motor_sr = pd.DataFrame(columns = ['date','motor_temperature'])
for j in range(len(motor_dir_list)):    
    temp_pd = convert.conversion(motor_path + motor_dir_list[j],'pressure')
    motor_sr = pd.concat([motor_sr,temp_pd[['date','motor_temperature']]])

motor_sr = motor_sr.reset_index(drop= True)
motor_sr_time = motor_sr[2110:19209]
motor_sr_time = motor_sr_time.reset_index(drop= True)
for k in range(len(motor_sr_time)):
    if motor_sr_time['date'][k][15:17] == '58' or motor_sr_time['date'][k][15:17] == '59' :
        motor_sr_time = motor_sr_time.drop([k])
motor_sr_time = motor_sr_time.drop([17098])       
motor_sr_time = motor_sr_time.reset_index(drop= True)        
    

dataset = pd.concat([dataset_alue,motor_sr_time],axis = 1)
dataset = dataset[[ 'date','Line 1 Current RMS', 'Line 2 Current RMS', 
                    'Line 3 Current RMS', 'Line 1 Voltage RMS', 'Line 2 Voltage RMS',
                    'Line 3 Voltage RMS', 'Line 1 power factor', 'Line 2 power factor',
                    'Line 3 power factor', 'motor_temperature','TachoSpeed(RPM)']]
dataset.to_csv('Front_simulation_dataset.csv', index = False)
    



















