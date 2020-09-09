# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 09:08:27 2020

@author: junes
"""
import os
os.chdir('F:/DigitalTwin_Data/python')
import numpy as np
import pandas as pd
from scipy.signal import lfilter
import statistics



def conversion(directory,data_type):
    if data_type =='pressure'  or data_type =='temperature':
        data = pd.read_csv(directory, sep=' |,', engine='python', header=None)
        if data_type == 'pressure' :
            motor_temperature = (1/(np.log10((((4096/data[3])-1)*4700)/10000)/3984 + (1/(25+273.15))))-273.15
            differential_pressure = (((data[5]*0.439)/58)-4)/(16/5000)
            air_pressure = (((data[7]*0.439)/58)-4)/(16/10)
            date = data[0]
            conversion_data = pd.concat([date,motor_temperature,differential_pressure,air_pressure],axis= 1,
                                        ignore_index=True)
            conversion_data.columns = ['date','motor_temperature', 'differential_pressure','air_pressure']
        elif data_type == 'temperature' :
            data = data.drop([2], axis = 1)
            data.columns = ['date','temperature','humidity']
            conversion_data = data
    else:
        data = np.fromfile(directory, dtype = np.int16)
        if data_type == 'cur' :
            data = data * 0.305 / 0.05
            conversion_data = data
        elif data_type == 'vol' :
            data = data * 0.305 / 0.01
            conversion_data = data
        elif data_type == 'mic' :
            data = data * 0.305/45
            conversion_data = data
        elif data_type == 'vib' :
            data = ((data * 0.305)/100)*9.8
            conversion_data = data
        elif data_type == 'tacho' :
            conversion_data = data
    return conversion_data

def sampling(data, sampling_rate):
    result = []
    for i in range(len(data)) :
        if (i+1)%sampling_rate == 0 :
            result.append(data[i])
    return result

def power_factor(current,voltage,fs):
    factor_list = []
    try:
        for i in range(fs):
            #초단위로 나눔
            cur = current[int(len(current)*(i/fs)):int(len(current)*((i+1)/fs))]
            vol = voltage[int(len(voltage)*(i/fs)):int(len(voltage)*((i+1)/fs))]
            if len(cur) ==len(vol):
                #초단위 데이터 역률 찾기
                cur_point = []
                vol_point = []
                j = 0
                while True:
                    if cur[j]*cur[j+1] <0:
                        cur_point.append(j)
                        j = j + 5
                    elif cur[j]*cur[j+1] <0:
                        j = j + 5
                        cur_point.append(j)
                    else:
                         j = j +1
                    if j >=(len(cur)-1):
                        break
                j2 = 0
                while True:
                    if vol[j2]*vol[j2+1] <0:
                        vol_point.append(j2)
                        j2 = j2 + 5
                    elif vol[j2]*vol[j2+1] <0:
                        j2 = j2 + 5
                        vol_point.append(j2)
                    else:
                         j2 = j2 +1
                    if j2 >=(len(vol)-1):
                        break
                circle = 180/(sum(cur_point)/len(cur_point))
                gap = []
                if len(cur_point) != len(vol_point):
                    loop = min([len(cur_point),len(vol_point)])
                else:
                    loop = len(cur_point)
                for k in range(loop):
                    gap.append(np.cos(abs(cur_point[k] - vol_point[k])*(circle)*(np.pi/180)))
                factor_list.append(sum(gap)/len(gap))

            else:
                print('not match data point')
                break

    except:
        print('error')

    return factor_list

def filtering(data,n):
    b = [1.0 / n] * n
    a = 1
    data_fliter = lfilter(b,a,data)
    return data_fliter


def hertz(min_data,sec):
    try:
        hertz_list = []
        for i in range(sec):
            hertz = 0
            rest_hertz = 0
            data = min_data[int((len(min_data)/sec*i)):int((len(min_data)/sec*(i+1)))]
            cycle = []
            j = 0
            while True:
                if data[j]*data[j+1] <0:
                    hertz = hertz + 1
                    cycle.append(j)
                    j = j + 5
                elif data[j]*data[j+1] ==0:
                    hertz = hertz + 1
                    cycle.append(j)
                    j = j + 5
                else:
                    pass
                    j = j + 1
                if j >= (len(data)-1):
                    break
            circle = round(sum(cycle)/len(cycle))
            first_circle = np.where(abs(data[:circle]) == np.amin(np.abs(data[:circle])))[0][0]
            last_cilrcle = np.where(abs(data[len(data)-circle:len(data)]) == np.amin(np.abs(data[len(data)-circle:len(data)])))[0][0]

            if first_circle != 0 :
                rest_hertz = rest_hertz + first_circle
            if last_cilrcle != len(data[len(data)-circle:len(data)]):
                rest_hertz = rest_hertz + (len(data[len(data)-circle:len(data)]) - 4)
            rest_hertz = rest_hertz/circle
            hertz = hertz/2 + rest_hertz
            hertz_list.append(hertz)
    except:
        print(i)
    return hertz_list

def rpm(tacho,sec,fs):
    try:
        rpm = []
        for i in range(sec):
            sec_tacho = tacho[int(len(tacho)*(i/sec)):int(len(tacho)*((i+1)/sec))]
            sig_list = []
            j = 0

            while True:
                if abs(abs(sec_tacho[j]) - abs(sec_tacho[(j+1)])) > 4000:
                    sig_list.append(j)
                if len(sig_list) >=20:
                    break
                j = j +1
            gap = []
            for k in range(len(sig_list)-2):
                gap.append(sig_list[k+2] - sig_list[k])
            interval = statistics.median(gap)
            rpm_val = (fs*60)/interval
            rpm.append(rpm_val)
    except:
        print('error')
    return rpm


def peak(raw):
    peak = []
    for i in range(58):
        data = raw[int((len(raw)/58*i)):int((len(raw)/58*(i+1)))]
        j = 0
        index = []
        while True:
            if data[j]*data[j+1] < 0:
                index.append(j)
                j = j + 5
            elif data[j]*data[j+1] == 0:
                index.append(j)
                j = j + 5
            else:
                j = j + 1

            if j >=(len(data)-1):
                break
        sec_peak = []
        k = 0
        while True:
            if data[index[0]+10] > 0:
                sec_peak.append(max(data[index[k]:index[k+1]]))
                k = k + 2
            elif data[index[0]+10] < 0:
                sec_peak.append(max(data[index[k]:index[k+2]]))
                k = k+3
            if k >= (len(index)-5):
                break
        peak.append(np.average(sec_peak))
    return peak
