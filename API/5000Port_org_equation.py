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
from flask_restful import Resource, Api
import pymysql.cursors
import mysql_auth
from flask import Flask
import numpy as np
from flask import jsonify
import cv2 
from io import BytesIO
import PIL.Image
from sklearn.linear_model import LinearRegression



app = Flask(__name__)
api = Api(app)

@app.route('/', methods=['GET'])

def get():
    try:
        id_get = str(request.args.get('model_key'))
        rpm_get = str(request.args.get('rpm'))
        login = mysql_auth.info#db_auth_info
        connection = pymysql.connect(host = login['host'],#connection_info
                                 port = login['port'],
                                 user = login['user'], 
                                 password = login['password'], 
                                 db = login['db'] , 
                                 charset = login['charset'], 
                                 autocommit = True)
        cursor = connection.cursor()#connection cursor
        sql = 'select * from twin.model_graph where model_key ="{}"and rpm = "{}"'.format(id_get,rpm_get)#get data from db using id parameter
        cursor.execute(sql)
        result = cursor.fetchall()
        for sql_result in range(len(result)):
            if result[sql_result][3] == 'F' or result[sql_result][3] == 'M' :
                record = result[sql_result][16]#get image info line 
                file_like= BytesIO(record)# converting byte to image data
                pil_img=PIL.Image.open(file_like).convert('RGB')
                img = np.array(pil_img)
                img = img[:, :, ::-1].copy() 
                b,g,r = cv2.split(img)#split bgr band
                # get db img (record)
                # each type graph fix degree
                start_point = result[sql_result][13].split(',')#get start point and pharse string data
                start_point = [int(start_point[0]),int(start_point[0])]
                start_location = list(img[int(start_point[0])][int(start_point[1])])
                zero_point = (int(result[sql_result][10].split(',')[0]),int(result[sql_result][10].split(',')[1]))
                x_max = result[sql_result][6]
                y_max = result[sql_result][8]
                x_max_point = result[sql_result][11].split(',')
                y_max_point = result[sql_result][12].split(',')
                img = img[int(y_max_point[1]):int(x_max_point[1]),int(y_max_point[0]):int(x_max_point[0])]#crop image tight x,y line
                if start_location.index(min(start_location)) == 0:
                    band = b
                    r[(r != -1)] = 255
                    g[(g != -1)] = 255
                elif start_location.index(min(start_location)) == 1:
                    band = g
                    r[(r != -1)] = 255
                    b[(b != -1)] = 255
                elif start_location.index(min(start_location)) == 2:
                    band = r
                    b[(b != -1)] = 255
                    g[(g != -1)] = 255
                #down to up remove line
                
                for vertical in range(img.shape[1]):
                    if band[zero_point[0]-2][vertical] < 255:
                        vertical_line = 0
                        vertical_line_val = []
                        for j in range(10):
                            if band[zero_point[0] - j][vertical] < 255:
                                vertical_line = vertical_line +1
                                vertical_line_val.append(g[zero_point[0] - j][vertical])
                                if vertical_line >3:  
                                    img[:,vertical, :] = 255#erase line
                                
                    else:
                        pass#none pixel pass   
                #left to right
                for i in range(img.shape[0]):
                    if g[i][start_location[1]] < 255:# start at starting point's x location
                        if start_location[0] - 15  < i <= start_point[0] + 15 :
                            pass# graph is pass
                        else:
                            horizon_line = 0#check line
                            horizon_line_val = []
                            for j in range(5):    
                                if g[i][start_location[1] + j ] < 255:
                                    horizon_line = horizon_line + 1
                                    horizon_line_val.append(g[i][start_location[1] + j ])
                                    if horizon_line == 5:# if line is true
                                        img[:,i, :] = 255#erase line                 
                    else:
                        pass#none pixel pass
                #same step like above that trace horizen(vertical) line
                #up to down
                for i in range(img.shape[1]):
                    if g[start_point[0]][i] < 255:
                        if start_point[1] - 15  < i <= start_point[1] + 15:
                            pass
                        else:       
                            vertical_line = 0
                            vertical_line_val = []
                            for j in range(10):
                                if g[start_point[0] + j][i] < 255:
                                    vertical_line = vertical_line +1
                                    vertical_line_val.append(g[start_point[0] + j][i])
                                    if vertical_line >4:
                                        for k in range(img.shape[0]):
                                            img[k][i] = [255,255,255]#erase line
                    else:
                        pass
    
                img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                ret, thr = cv2.threshold(img_gray, 127,255, cv2.THRESH_BINARY) 
                thr = thr[0: thr.shape[0] - 3, 3: thr.shape[1]]
                location = np.where(thr == 0)
                x_rate = x_max/thr.shape[1]
                y_rate = y_max/thr.shape[0] 
                location_y = list(location[0])
                location_x = list(location[1])
                equation_x = []
                for i in range(len(location_y)):
                    location_y[i] = (thr.shape[0] - location_y[i])*y_rate
                    location_x[i] = location_x[i]*x_rate
                for j in range(len(location_x)):
                    equation_x.append([(location_x[j]**3),(location_x[j]**2),(location_x[j]**1)])# get x plot in list
                
                model = LinearRegression().fit(equation_x,location_y)
                solution = list(model.coef_)
                solution.append(model.intercept_)    
                sql_excute = 'update twin.model_graph set org_equation ="{}*Math.pow(x,3)+ {}*Math.pow(x,2)+ {}*x+ {}" where mgraph_key = "{}" and rpm = "{}" and mgraph_type = "{}" '.format(solution[0],solution[1],solution[2],solution[3],result[sql_result][0],result[sql_result][5],result[sql_result][1])#insert graph equation
                cursor.execute(sql_excute)
                
        #end loop
        connection.commit()
        connection.close()

        return jsonify({'status' : True})
    except:
        return jsonify({'status' : False})

   
    
if __name__ == '__main__':
  app.run(host='0.0.0.0',port = '5000',debug = True)