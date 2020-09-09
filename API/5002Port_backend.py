# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 17:09:33 2020

@author: junes
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 11:02:30 2019

@author: junes
"""


import pymysql.cursors
import mysql_auth
from sympy import solve, symbols
from math import pi as pi

def val(p,q,r,f,m):
    try:
        pressure_get = p
        volume_get = q
        rpm_get = r
        fan_key = f
        motor_key = m
        login = mysql_auth.info#db_auth_info
        connection = pymysql.connect(host = login['host'],#connection_info
                                 port = login['port'],
                                 user = login['user'], 
                                 password = login['password'], 
                                 db = login['db'] , 
                                 charset = login['charset'], 
                                 autocommit = True)

        cursor = connection.cursor()#connection cursor
        model_set_sql = 'select * from twin.model_set where fan_key = "{}" and motor_key = "{}"'.format(fan_key,motor_key)
        cursor.execute(model_set_sql)
        model_set = cursor.fetchall()
        if model_set[0][10] == 0:    
            is_inverter = False
            for inverter_check in range(len(model_set)):
                if model_set[inverter_check][11] == 1:#inverter
                    inverter_index = inverter_check
                    grid_rpm = model_set[inverter_check][2]
        elif model_set[0][10] == 1:
            is_inverter = True
            
                
        if is_inverter == False:
            fan_model_graph_sql = 'select mgraph_type, org_equation from twin.model_graph where model_key = "{}" and rpm = "{}"'.format(fan_key,grid_rpm)
            cursor.execute(fan_model_graph_sql)
            fan_model_graph = cursor.fetchall()
            fe_coef = fan_model_graph[2][1].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
            fp_coef = fan_model_graph[1][1].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
            if pressure_get != '' :
                mod_coef = model_set[inverter_index][9].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                x = symbols('x')
                equation_volume = float(mod_coef[0])*(x**3) + float(mod_coef[1])*(x**2) + float(mod_coef[2])*x + float(mod_coef[3]) - float(pressure_get)
                coef_volume = solve((equation_volume),dict = True)
                for j in range(len(coef_volume)):
                        if float(str(coef_volume[j][x]).split(' ')[0]) > 0:
                            volume = float(str(coef_volume[j][x]).split(' ')[0])
                fe = float(fe_coef[0])*(volume**3) + float(fe_coef[1])*(volume**2) + float(fe_coef[2])*volume + float(fe_coef[3]) 
                fp = float(fp_coef[0])*(volume**3) + float(fp_coef[1])*(volume**2) + float(fp_coef[2])*volume + float(fp_coef[3]) 
                motor_rated_rpm_sql = 'select rpm from twin.model_graph where model_key = "{}" and model_type="M"'.format(motor_key)
                cursor.execute(motor_rated_rpm_sql)
                motor_rpm_row = cursor.fetchall()
                motor_rpm = motor_rpm_row[0][0]
                motor_equation_sql = 'select * from twin.model where model_key = "{}"'.format(motor_key)
                cursor.execute(motor_equation_sql)
                motor_equation_result = cursor.fetchall() 
                poll = motor_equation_result[0][11]
                hertz = motor_equation_result[0][13]
                #watt = motor_equation_result[0][12]
                torque = motor_equation_result[0][9]
                rated_rpm= motor_rpm
                max_rpm = 120*hertz/poll
                c2 = (-torque)/(max_rpm-rated_rpm)
                t_0 = torque-(c2*rated_rpm)
                fan_equation_sql = 'select * from twin.model_graph where model_key = "{}" and model_type="F" and rpm = "{}"'.format(fan_key, grid_rpm)
                cursor.execute(fan_equation_sql)
                fan_equation = cursor.fetchall()
                pq = fan_equation[0][18].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                sq = fan_equation[1][18].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                ef = fan_equation[2][18].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                i = volume 
                pressure = float(pq[0])*(i**3) + float(pq[1])*(i**2) + float(pq[2])*(i**1)+ float(pq[3])
                if pressure > 0:
                    power = float(sq[0])*(i**3) + float(sq[1])*(i**2) + float(sq[2])*(i**1)+ float(sq[3])
                    efficiency = float(ef[0])*(i**3) + float(ef[1])*(i**2) + float(ef[2])*(i**1)+ float(ef[3])
                    torque = (power*1000.0*30.0)/pi/grid_rpm#Nm
                    torque_kg = torque/9.80665
                    effi_torque = torque_kg/(efficiency/100)
                    c1 = effi_torque/(grid_rpm**2)
                    mod_rpm ,mod_torque = symbols('mod_rpm,mod_torque')
                    equation_fan_t_n = c1*(mod_rpm**2) - mod_torque
                    equation_motor_t_n = c2*mod_rpm + t_0 - mod_torque
                    coef_cross = solve((equation_fan_t_n,equation_motor_t_n),dict = True)
                    for k in range(len(coef_cross)):
                        if coef_cross[k][mod_rpm] > 0:
                            result_pre = (coef_cross[k][mod_rpm],coef_cross[k][mod_torque])
                            if len(result_pre) >1 :
                                result = max(result_pre)
                if  result < 1760:
                    me = (7e-09*float(result)**3) - (4e-05*float(result)**2) + (0.058*float(result))+ 60.033
                else:
                    me = 89.5
                mp = fp/(me/100)         
                case = 0
                case_0_dict = {'status' : True,
                               'x_location': int(volume),
                               'y_location': int(pressure_get),
                               'q': round(volume,2),
                               'mp': round(mp,2),
                               'fp': round(fp,2),
                               'fe': round(fe,2),
                               'me': round(me,2),
                               'r':round(result,2)}

            
            elif volume_get!= '':

                mod_coef = model_set[inverter_index][9].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                pressure = float(mod_coef[0])*(float(volume_get)**3) + float(mod_coef[1])*(float(volume_get)**2) + float(mod_coef[2])*float(volume_get)+ float(mod_coef[3]) 
                fe = float(fe_coef[0])*(float(volume_get)**3) + float(fe_coef[1])*(float(volume_get)**2) + float(fe_coef[2])*float(volume_get) + float(fe_coef[3]) 
                fp = float(fp_coef[0])*(float(volume_get)**3) + float(fp_coef[1])*(float(volume_get)**2) + float(fp_coef[2])*float(volume_get)+ float(fp_coef[3]) 
                motor_rated_rpm_sql = 'select rpm from twin.model_graph where model_key = "{}" and model_type="M"'.format(motor_key)
                cursor.execute(motor_rated_rpm_sql)
                motor_rpm_row = cursor.fetchall()
                motor_rpm = motor_rpm_row[0][0]
                motor_equation_sql = 'select * from twin.model where model_key = "{}"'.format(motor_key)
                cursor.execute(motor_equation_sql)
                motor_equation_result = cursor.fetchall() 
                poll = motor_equation_result[0][11]
                hertz = motor_equation_result[0][13]
                #watt = motor_equation_result[0][12]
                torque = motor_equation_result[0][9]
                rated_rpm= motor_rpm
                max_rpm = 120*hertz/poll
                c2 = (-torque)/(max_rpm-rated_rpm)
                t_0 = torque-(c2*rated_rpm)
                fan_equation_sql = 'select * from twin.model_graph where model_key = "{}" and model_type="F" and rpm = "{}"'.format(fan_key, grid_rpm)
                cursor.execute(fan_equation_sql)
                fan_equation = cursor.fetchall()
                pq = fan_equation[0][18].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                sq = fan_equation[1][18].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                ef = fan_equation[2][18].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                i = float(volume_get)
                pressure = float(pq[0])*(i**3) + float(pq[1])*(i**2) + float(pq[2])*(i**1)+ float(pq[3])
                if pressure > 0:
                    power = float(sq[0])*(i**3) + float(sq[1])*(i**2) + float(sq[2])*(i**1)+ float(sq[3])
                    efficiency = float(ef[0])*(i**3) + float(ef[1])*(i**2) + float(ef[2])*(i**1)+ float(ef[3])
                    torque = (power*1000.0*30.0)/pi/grid_rpm#Nm
                    torque_kg = torque/9.80665
                    effi_torque = torque_kg/(efficiency/100)
                    c1 = effi_torque/(grid_rpm**2)
                    mod_rpm ,mod_torque = symbols('mod_rpm,mod_torque')
                    equation_fan_t_n = c1*(mod_rpm**2) - mod_torque
                    equation_motor_t_n = c2*mod_rpm + t_0 - mod_torque
                    coef_cross = solve((equation_fan_t_n,equation_motor_t_n),dict = True)
                    for k in range(len(coef_cross)):
                        if coef_cross[k][mod_rpm] > 0:
                            result_pre = (coef_cross[k][mod_rpm],coef_cross[k][mod_torque])
                            if len(result_pre) >1 :
                                result = max(result_pre)
                if result < 1760:
                    me = 7e-09*float(result)**3 - 4e-05*float(result)**2 + 0.058*float(result)+ 60.033
                else:
                    me = 89.1
                case = 1
                case_1_dict = {'status' : True,
                               'x_location': int(pressure),
                               'y_location': int(volume_get),
                               'p':round(pressure,2),
                               'mp':round(mp,2),
                               'fp':round(fp,2),
                               'fe':round(fe,2),
                               'me':round(me,2),
                               'r': round(result,2)}
#inverter is True
                
        elif is_inverter == True:
            if rpm_get != '':#get rpm parameter
                rpm = []
                for i in range(len(model_set)):
                    rpm.append(model_set[i][2])        
                if rpm_get in rpm:#rpm is exist in measured value
                    fan_model_graph_sql = 'select mgraph_type, org_equation from twin.model_graph where model_key = "{}" and rpm = "{}"'.format(fan_key,rpm_get)
                    cursor.execute(fan_model_graph_sql)
                    fan_model_graph = cursor.fetchall()
                    coef = fan_model_graph[rpm.index(rpm_get)][9].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                    fe_coef = fan_model_graph[2][1].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                    fp_coef = fan_model_graph[1][1].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                    if pressure_get != '':#get pressure(y) parameter and empty volume(x)
                        x = symbols('x')
                        equation_volume = float(coef[0])*(x**3) + float(coef[1])*(x**2) + float(coef[2])*x + float(coef[3]) - float(pressure_get)
                        coef_volume = solve((equation_volume),dict = True)
                        for j in range(len(coef_volume)):
                            if float(str(coef_volume[j][x]).split(' ')[0]) > 0:
                                volume = float(str(coef_volume[j][x]).split(' ')[0]) 
                        fe = float(fe_coef[0])*(volume**3) + float(fe_coef[1])*(volume**2) + float(fe_coef[2])*volume + float(fe_coef[3]) 
                        fp = float(fp_coef[0])*(volume**3) + float(fp_coef[1])*(volume**2) + float(fp_coef[2])*volume + float(fp_coef[3]) 
                        if float(rpm_get) < 1760:
                            me = 7e-09*float(rpm_get)**3 - 4e-05*float(rpm_get)**2 + 0.058*float(rpm_get)+ 60.033
                        else:
                            me = 89.1
                        mp = fp/(me/100)
                        #return_value
                        case = 2
                        case_2_dict = {'status' : True,
                                        'x_location': int(volume),
                                        'y_location': int(pressure_get),
                                        'q':round(volume,2),
                                        'r':round(rpm_get,2),
                                        'fe':round(fe,2),
                                        'fp':round(fp,2),
                                        'me':round(me,2),
                                        'mp':round(mp,2)}
                     #########수정##############   
                    elif volume_get != '':#get volume(x) parameter and empty pressure(y)
                        volume = float(volume_get)
                        pressure = float(coef[0])*(volume**3) + float(coef[1])*(volume**2) + float(coef[2])*volume + float(coef[3])
                        fe = float(fe_coef[0])*(volume**3) + float(fe_coef[1])*(volume**2) + float(fe_coef[2])*volume + float(fe_coef[3]) 
                        fp = float(fp_coef[0])*(volume**3) + float(fp_coef[1])*(volume**2) + float(fp_coef[2])*volume + float(fp_coef[3]) 
                        if float(rpm_get) < 1760:
                            me = 7e-09*float(rpm_get)**3 - 4e-05*float(rpm_get)**2 + 0.058*float(rpm_get)+ 60.033
                        else:
                            me = 89.1
                        mp = fp/(me/100)
                        #return_value
                        case = 3
                        case_3_dict = {'status' : True,    
                                       'x_location': int(volume_get),
                                       'y_location': int(pressure),
                                       'p':round(pressure,2),
                                       'r':round(rpm_get,2),
                                       'fe':round(fe,2),
                                       'fp':round(fp,2),
                                       'me':round(me,2),
                                       'mp':round(mp,2)}

                elif rpm_get not in rpm:
                    fan_model_graph_sql = 'select mgraph_type, rpm, org_equation from twin.model_graph where model_key = "{}"'.format(fan_key)
                    cursor.execute(fan_model_graph_sql)
                    fan_model_graph = cursor.fetchall()
                    plus_rpm_list = []#rpm이 클때
                    minus_rpm_list = []#rpm이 작을때
                    for i in range(len(rpm)):
                        if rpm[i] - float(rpm_get) > 0:
                            plus_rpm_list.append(rpm[i])
                        elif rpm[i] - float(rpm_get) < 0:
                            minus_rpm_list.append(rpm[i])
                    if len(plus_rpm_list) > 0 and len(minus_rpm_list) > 0:    
                        plus_rpm = min(plus_rpm_list)#유사 rpm중 큰 
                        minus_rpm = max(minus_rpm_list)#유사 rpm중 작은 수 
                        for j in range(len(fan_model_graph)):#플러스 마이너스 PQ수식 찾기.
                            if fan_model_graph[j][1] == plus_rpm : 
                                if fan_model_graph[j][0] == 'PQ':
                                    plus_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                                elif fan_model_graph[j][0] == 'SP':
                                    plus_sp_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                                elif fan_model_graph[j][0] == 'EF':
                                    plus_ef_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                            elif fan_model_graph[j][1] == minus_rpm :
                                if fan_model_graph[j][0] == 'PQ':
                                    minus_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                                elif fan_model_graph[j][0] == 'SP':
                                    minus_sp_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                                elif fan_model_graph[j][0] == 'EF':
                                    minus_ef_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                        if pressure_get != '':
                            plus_x = symbols('plus_x')
                            plus_equation = float(plus_coef[0])*(plus_x**3) + float(plus_coef[1])*(plus_x**2) + float(plus_coef[2])*plus_x + float(plus_coef[3]) - float(pressure_get)
                            plus_volume = solve((plus_equation),dict = True)
                            for k in range(len(plus_volume)):
                                if float(str(plus_volume[k][plus_x]).split(' ')[0]) > 0:
                                    if float(str(plus_volume[k][plus_x]).split(' ')[0]) < 30000:    
                                        p_volume = float(str(plus_volume[k][plus_x]).split(' ')[0]) 
                            minus_x = symbols('minus_x')
                            minus_equation = float(minus_coef[0])*(minus_x**3) + float(minus_coef[1])*(minus_x**2) + float(minus_coef[2])*minus_x + float(minus_coef[3]) - float(pressure_get)
                            minus_volume = solve((minus_equation),dict = True)
                            for k in range(len(minus_volume)):
                                if float(str(minus_volume[k][minus_x]).split(' ')[0]) > 0:
                                    if float(str(minus_volume[k][minus_x]).split(' ')[0]) < 30000:
                                        m_volume = float(str(minus_volume[k][minus_x]).split(' ')[0])
                            volume_rate = (p_volume - m_volume)/(plus_rpm - minus_rpm)
                            volume = m_volume + ((float(rpm_get) - minus_rpm)*volume_rate)
                            plus_fe = float(plus_ef_coef[0])*(volume**3) + float(plus_ef_coef[1])*(volume**2) + float(plus_ef_coef[2])*volume + float(plus_ef_coef[3])
                            minus_fe = float(minus_ef_coef[0])*(volume**3) + float(minus_ef_coef[1])*(volume**2) + float(minus_ef_coef[2])*volume + float(minus_ef_coef[3])
                            fe_rate = (plus_fe - minus_fe)/(plus_rpm - minus_rpm)
                            fe = minus_fe + ((float(rpm_get) - minus_rpm)*fe_rate)
                            plus_fp = float(plus_sp_coef[0])*(volume**3) + float(plus_sp_coef[1])*(volume**2) + float(plus_sp_coef[2])*volume + float(plus_sp_coef[3]) 
                            minus_fp = float(minus_sp_coef[0])*(volume**3) + float(minus_sp_coef[1])*(volume**2) + float(minus_sp_coef[2])*volume + float(minus_sp_coef[3])
                            fp_rate = (plus_fp - minus_fp)/(plus_rpm - minus_rpm)
                            fp = minus_fp + ((float(rpm_get) - minus_rpm)*fp_rate)
                            if float(rpm_get) < 1760:
                                me = 7e-09*float(rpm_get)**3 - 4e-05*float(rpm_get)**2 + 0.058*float(rpm_get)+ 60.033
                            else:
                                me = 89.5
                            mp = fp/(me/100)
                            case = 4
                            case_4_dict = {'status' : True,    
                                           'x_location': int(volume),
                                           'y_location': int(pressure_get),
                                           'q':round(volume,2),
                                           'r':round(float(rpm_get),2),
                                           'fe':round(fe,2),
                                           'fp':round(fp,2),
                                           'me':round(me,2),
                                           'mp':round(mp,2)}
                        elif volume_get != '':
                            volume = float(volume_get)                             
                            plus_p= float(plus_coef[0])*(volume**3) + float(plus_coef[1])*(volume**2) + float(plus_coef[2])*volume+ float(plus_coef[3])
                            minus_p = float(minus_coef[0])*(volume**3) + float(minus_coef[1])*(volume**2) + float(minus_coef[2])*volume+ float(minus_coef[3]) 
                            p_rate = (plus_p - minus_p)/(plus_rpm - minus_rpm)
                            pressure = minus_p + ((float(rpm_get) - minus_rpm)*p_rate)
                            plus_fe = float(plus_ef_coef[0])*(volume**3) + float(plus_ef_coef[1])*(volume**2) + float(plus_ef_coef[2])*volume + float(plus_ef_coef[3])
                            minus_fe = float(minus_ef_coef[0])*(volume**3) + float(minus_ef_coef[1])*(volume**2) + float(minus_ef_coef[2])*volume + float(minus_ef_coef[3])
                            fe_rate = (plus_fe - minus_fe)/(plus_rpm - minus_rpm)
                            fe = minus_fe + ((float(rpm_get) - minus_rpm)*fe_rate)
                            plus_fp = float(plus_sp_coef[0])*(volume**3) + float(plus_sp_coef[1])*(volume**2) + float(plus_sp_coef[2])*volume + float(plus_sp_coef[3]) 
                            minus_fp = float(minus_sp_coef[0])*(volume**3) + float(minus_sp_coef[1])*(volume**2) + float(minus_sp_coef[2])*volume + float(minus_sp_coef[3])
                            fp_rate = (plus_fp - minus_fp)/(plus_rpm - minus_rpm)
                            fp = minus_fp + ((float(rpm_get) - minus_rpm)*fp_rate)
                            if float(rpm_get) < 950:
                                me = 7e-09*float(rpm_get)**3 - 4e-05*float(rpm_get)**2 + 0.058*float(rpm_get)+ 60.033
                            else:
                                me = 89.5
                            mp = fp/(me/100)
                            case = 5
                            case_5_dict = {'status' : True,    
                                           'x_location': int(volume),
                                           'y_location': int(pressure),
                                           'p':round(pressure,2),
                                           'r':round(float(rpm_get),2),
                                           'fe':round(fe,2),
                                           'fp':round(fp,2),
                                           'me':round(me,2),
                                           'mp':round(mp,2)}

                    else:
                        case = 7
                        msg = 'your point is out of range data that can measure by original data graph'
                        
            elif rpm_get == '':
                pressure_get1 = float(pressure_get)
                fan_model_graph_sql = 'select mgraph_type, rpm, org_equation from twin.model_graph where model_key = "{}"'.format(fan_key)
                cursor.execute(fan_model_graph_sql)
                fan_model_graph = cursor.fetchall()
                volume = float(volume_get)
                p = []
                r= []
                for i in range(len(fan_model_graph)):
                    if fan_model_graph[i][0] == 'PQ':
                        coef = fan_model_graph[i][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                        p.append(float(coef[0])*(volume**3) + float(coef[1])*(volume**2) + float(coef[2])*volume + float(coef[3]))
                        r.append(fan_model_graph[i][1])
                minus_p = []
                plus_p = []
                minus_r = []
                plus_r = []
                for j in range(len(p)):
                    if p[j] >  0:
                        if pressure_get1 - p[j] > 0:
                            plus_p.append(p[j])
                            plus_r.append(r[j])
                        elif pressure_get1 - p[j] < 0:
                            minus_p.append(p[j])
                            minus_r.append(r[j])
                plus_rpm = min(plus_r)#유사 rpm중 큰 
                minus_rpm = max(minus_r)#유사 rpm중 작은 수 
                plus_pressure = min(plus_p)
                minus_pressure = max(minus_p)
                rate = (plus_rpm - minus_rpm)/(plus_pressure - minus_pressure)
                rpm_result = minus_rpm + ((float(pressure_get1) - minus_pressure)*rate)
                for j in range(len(fan_model_graph)):#플러스 마이너스 PQ수식 찾기.
                    if fan_model_graph[j][1] == plus_rpm : 
                        if fan_model_graph[j][0] == 'PQ':
                            plus_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                        elif fan_model_graph[j][0] == 'SP':
                            plus_sp_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                        elif fan_model_graph[j][0] == 'EF':
                            plus_ef_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                    elif fan_model_graph[j][1] == minus_rpm :
                        if fan_model_graph[j][0] == 'PQ':
                            minus_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                        elif fan_model_graph[j][0] == 'SP':
                            minus_sp_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                        elif fan_model_graph[j][0] == 'EF':
                            minus_ef_coef = fan_model_graph[j][2].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
                plus_fe = float(plus_ef_coef[0])*(volume**3) + float(plus_ef_coef[1])*(volume**2) + float(plus_ef_coef[2])*volume + float(plus_ef_coef[3])
                minus_fe = float(minus_ef_coef[0])*(volume**3) + float(minus_ef_coef[1])*(volume**2) + float(minus_ef_coef[2])*volume + float(minus_ef_coef[3])
                fe_rate = (plus_fe - minus_fe)/(plus_rpm - minus_rpm)
                fe = minus_fe + ((float(pressure_get) - minus_pressure)*fe_rate)
                plus_fp = float(plus_sp_coef[0])*(volume**3) + float(plus_sp_coef[1])*(volume**2) + float(plus_sp_coef[2])*volume + float(plus_sp_coef[3]) 
                minus_fp = float(minus_sp_coef[0])*(volume**3) + float(minus_sp_coef[1])*(volume**2) + float(minus_sp_coef[2])*volume + float(minus_sp_coef[3])
                fp_rate = (plus_fp - minus_fp)/(plus_rpm - minus_rpm)
                fp = minus_fp + ((float(pressure_get) - minus_pressure)*fe_rate)
                if float(rpm_result) < 1760:
                    me = 7e-09*rpm_result**3 - 4e-05*rpm_result**2 + 0.058*rpm_result + 60.033
                else:
                    me = 89.5
                mp = fp/(me/100)
                case = 6

                case_6_dict = {'status' : True,    
                               'x_location': int(volume),
                               'y_location': int(pressure_get),
                               'p':round(float(pressure_get),2),
                               'r':round(rpm_result,2),
                               'fe':round(fe,2),
                               'fp':round(fp,2),
                               'me':round(me,2),
                               'mp':round(mp,2)}


                 
                        
        
        if case == 0:
            return_val = case_0_dict 
        elif case == 1:   
            return_val = case_1_dict
        elif case == 2:   
            return_val = case_2_dict
        elif case == 3:   
            return_val = case_3_dict
        elif case == 4:   
            return_val = case_4_dict
        elif case == 5:
            return_val = case_5_dict
        elif case == 6:
            return_val = case_6_dict
        elif case == 7:
            return_val = {'status': False,
                          'msg': msg}
        
        #response = jsonify(return_val)
        #response.headers.add("Access-Control-Allow-Origin", "*")
        #response.headers.add("Access-Control-Allow-Headers", "*")
        #response.headers.add("Access-Control-Allow-Methods", "*")
        #return response
        
        '''
        value list name rules = case_'number'_list 
        case 0 => get = rpm, pressure | rpm in  
        case 1 => get = rpm, volume   | rpm in 
        case 2 => get = rpm, pressure | rpm not in 
        case 3 => get = rpm, volume   | rpm not in 
        case 4 => get = rpm, pressure | rpm is ''
        '''
        # get db img (record)
        # each type graph fix degree
        connection.commit()
        connection.close()
        #logging.getLogger('flask_cors').level = logging.DEBUG
        return (return_val)
    
    except:
        return ({'status' : False})







