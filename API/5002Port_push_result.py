# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:16:13 2020

@author: junes
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 11:02:30 2019

@author: junes
"""

from flask import request
from flask import Flask
from flask import jsonify
from flask_restful import  Api
import 5002Port_push_result as backend3
from flask_cors import CORS, cross_origin
#from django.core.serializers.json import DjangoJSONEncoder
#import jsondumper
#import json
app = Flask(__name__)
CORS(app)
api = Api(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/', methods=['GET'])
@cross_origin(origins = '*')

def get():
    pressure_get = str(request.args.get('p'))
    volume_get = str(request.args.get('q'))
    rpm_get = str(request.args.get('r'))
    fan_key = str(request.args.get('fan_key'))
    motor_key = str(request.args.get('motor_key'))
    result = backend3.val(pressure_get,volume_get,rpm_get,fan_key,motor_key)
    #print(result)
    #return_val = json.dumps(result,cls = DjangoJSONEncoder)
    try:
        return jsonify(result)
    except:
        return jsonify(False)
    #finally:
     #   jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0',port = '5002',debug = True)
