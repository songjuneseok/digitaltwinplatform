# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 11:02:27 2019

@author: junes
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 10:54:41 2019

@author: junes
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 09:41:44 2019

@author: junes
"""

from flask import request
from flask_restful import Api
import pymysql.cursors
import mysql_auth
from flask import Flask
from flask import jsonify
from sympy import solve, symbols
import math
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
api = Api(app)

@app.route('/', methods=['GET'])

def get():
    try:
        fan_key = str(request.args.get('fan_key'))
        motor_key = str(request.args.get('motor_key'))
        inverter_row = request.args.get('in')
        if inverter_row == 'true' :    
            inverter = True
        elif inverter_row == 'false':
            inverter = False
        login = mysql_auth.info#db_auth_info
        connection = pymysql.connect(host = login['host'],#connection_info
                                 port = login['port'],
                                 user = login['user'], 
                                 password = login['password'], 
                                 db = login['db'] , 
                                 charset = login['charset'], 
                                 autocommit = True)
        cursor = connection.cursor()#connection cursor
        rpm_get_sql = 'select rpm from model_graph where model_key="{}" and model_type="F" group by rpm'.format(fan_key)#get data from db using id parameter
        cursor.execute(rpm_get_sql)
        rpm_list = cursor.fetchall()
        rpm = []
        motor_rated_rpm_sql = 'select rpm from twin.model_graph where model_key = "{}" and model_type="M"'.format(motor_key)
        cursor.execute(motor_rated_rpm_sql)
        motor_rpm_row = cursor.fetchall()
        motor_rpm = motor_rpm_row[0][0]
        for loop in rpm_list:
            rpm.append(loop[0])
        if inverter == False:
            isRep = min(rpm, key=lambda x:abs(x-motor_rpm))#유사 rpm
            rep_sql = 'update twin.model_set set isRep = "{}" where rpm = "{}" and fan_key = "{}" and motor_key = "{}"'.format(1,isRep,fan_key, motor_key)
            cursor.execute(rep_sql)
        ###################인버터 유무로 수정 수식 주기.
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
            
            fan_equation_sql = 'select * from twin.model_graph where model_key = "{}" and model_type="F" and rpm = "{}"'.format(fan_key, isRep)
            cursor.execute(fan_equation_sql)
            fan_equation = cursor.fetchall()
            pq = fan_equation[0][18].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
            sq = fan_equation[1][18].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
            ef = fan_equation[2][18].replace('*Math.pow(x,3)','').replace('*Math.pow(x,2)','').replace('*Math.pow(x,2)','').replace('*x','').replace('+','').split(' ')
            mod_p = []
            mod_q = []
            for i in range(int(fan_equation[0][6]/10),fan_equation[0][6],300):
                pressure = float(pq[0])*(i**3) + float(pq[1])*(i**2) + float(pq[2])*(i**1)+ float(pq[3])
                if pressure > 0:
                    power = float(sq[0])*(i**3) + float(sq[1])*(i**2) + float(sq[2])*(i**1)+ float(sq[3])
                    efficiency = float(ef[0])*(i**3) + float(ef[1])*(i**2) + float(ef[2])*(i**1)+ float(ef[3])
                    torque = (power*1000.0*30.0)/math.pi/isRep#Nm
                    torque_kg = torque/9.80665
                    effi_torque = torque_kg/(efficiency/100)
                    c1 = effi_torque/(isRep**2)
                    mod_rpm ,mod_torque = symbols('mod_rpm,mod_torque')
                    equation_fan_t_n = c1*(mod_rpm**2) - mod_torque
                    equation_motor_t_n = c2*mod_rpm + t_0 - mod_torque
                    coef_cross = solve((equation_fan_t_n,equation_motor_t_n),dict = True)
                    for k in range(len(coef_cross)):
                        if coef_cross[k][mod_rpm] > 0:
                            result_pre = (coef_cross[k][mod_rpm],coef_cross[k][mod_torque])
                            if len(result_pre) >1 :
                                result = max(result_pre)
                                
                    mod_p.append(((int(result)/isRep)**2)*pressure)
                    mod_q_val = ((int(result)/isRep)*i)
                    mod_q.append([(mod_q_val**3),(mod_q_val**2),(mod_q_val**1)])# get x plot in list
            model = LinearRegression().fit(mod_q,mod_p)
            solution = list(model.coef_)
            solution.append(model.intercept_)
            sql_result = 'update twin.model_set set mod_equation ="{}*Math.pow(x,3)+ {}*Math.pow(x,2)+ {}*x+ {}" where fan_key = "{}" and rpm = "{}" and motor_key = "{}"'.format(solution[0],solution[1],solution[2],solution[3],fan_key,isRep,motor_key)#insert graph equation
            cursor.execute(sql_result)
            connection.commit()
            connection.close()
        return jsonify({'status' : True,
                        'sql':sql_result})
    except:
        return jsonify({'status' : False})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port = '5001',debug = True)
    





