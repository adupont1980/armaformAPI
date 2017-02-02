# -*- coding: utf-8 -*-
import os

from flask import Flask, request, Response, jsonify
from flask_pymongo import PyMongo
from pymongo import MongoClient
import pymongo
# from flask_cors import CORS, cross_origin
import json
from bson import json_util
from bson.objectid import ObjectId


# from flask_mail import Mail, Message

# mail = Mail()



# app.config['MAIL_SERVER']='smtp.live.com'
# app.config['MAIL_PORT'] = 25
# app.config['MAIL_USERNAME'] = 'anthony_dupont@hotmail.com'
# app.config['MAIL_PASSWORD'] = 'Goodbye2012'
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = False

# mail.init_app(app)

# CORS(app)

app = Flask(__name__)


MONGO_URL = os.environ.get('MONGO_URL')
# print(MONGO_URL)
if not MONGO_URL:
     MONGO_URL = "mongodb://localhost:27017/auto";


app.config['MONGO_URI'] = MONGO_URL
# mongo = PyMongo(app)
mongo = MongoClient(MONGO_URL)
db = client.test
# connection = pymongo.MongoClient("ds135029.mlab.com", 35029)
# db = connection["heroku_p754dw74"]
# db.authenticate("russianBallet", "Axonian456")


# mongo = PyMongo(app, config_prefix='MONGO')
# APP_URL = "http://127.0.0.1:5000"



# def newEncoder(o):
#     if type(o) == ObjectId:
#         return str(o)
#     return o.__str__


@app.route('/')
def index():
    
    return 'SERVER STARTED'

# #################################
# GET FORM DATA     _id param
##################################
@app.route('/getFormData', methods=['GET'])
def get_form_data():
    idRecord = request.args['_id']
    # collection = request.args['collName']

    # filtersName = request.args['filters_name'].split(',')
    # filtersValue = request.args['filters_value'].split(',')
    # print(collection)
    # print(filtersName)
    # print(filtersValue)
    print(idRecord)
    result = mongo.db.datas.find_one({'_id': ObjectId(idRecord)})
    # print(result)
    
    return json.dumps(result, default=json_util.default)

###################################
# GET DATA FROM CUSTOM COLLECTION
@app.route('/custom_collection', methods=['GET'])
def get_data():
    #  TODO TESTER SI PLUSIEURS VALEURS SONT PASSEES DANS LE FILTRE
    collectionName = request.args['collName']
    filtersName = request.args['filters_name'].split(',')
    filtersValue = request.args['filters_value'].split(',')
    valueToSelect = request.args['select']
    # key = ', {"'+ valueToSelect + '":1}'
    key = 'key: "'+ valueToSelect + '",'

    # print(filtersValue)
    isFiltered = False
    condition = '{'
    for (name, value) in zip(filtersName,filtersValue):
        if (value != ''):
            condition = condition + '"' + name + '":"' + value +'",' 
            isFiltered = True
            #condition = '{"' + filtersName[i] + '":"' + filtersValue[i] +'"}'
            
            # SI LA COLLECTION CONTIENT PLUSIEURS CHAMPS, SELECT CONTIENT CELUI A RAMENER
            # if 'select' in request.args: 
            # print(request.args['select'])
    print(condition)
    condition = condition[:-1]
    condition = condition + '}'     
    if (isFiltered):
        collection = 'mongo.db.'+collectionName+'.find('+ condition +').distinct("'+valueToSelect+'")'
    else:
        collection = 'mongo.db.'+collectionName+'.find().distinct("'+valueToSelect+'")'
        
    
    print(collection)

    cursor = eval(collection)

    docs_list  = list(cursor)

    docs_list.sort()
    print(docs_list)
    return json.dumps(docs_list, default=json_util.default)

    # for doc in cursor:
    #     json_doc = json.dumps(doc, default=json_util.default)
    #     output.append(json_doc)
    #     # output.append({lstField[0]: s[lstFi eld[0]])}
    #return output

####################################
# SAVE CURRENT STEP INTO COLLECTION
#####################################
@app.route('/save_datas', methods=['POST'])
def save_step():
    data = request.get_json(force=True)
    objToSave = {}
    for obj in data:
        print(obj)
        objToSave.update(obj)

    new_id = mongo.db.datas.insert(objToSave)
    # print(new_id)
    return str(new_id)

    # Response(
    # json_util.dumps({'id': id},mimetype='application/json')
    # ) 
    # return json_dumps(id, default=newEncoder)


# ########################
# GET STEPS CONFIGURATION
##########################
@app.route('/step', methods=['GET'])
def get_steps():
    # LIST OF STEPS FROM SELECTED MASTER
    output = []
    
    masterSteps = mongo.db.master.find({})
    
    for master in masterSteps:
        print(master['name'])
        print(master)
        # print(m['save_button'])
        
        # master name: TO FIND WHICH STEPS WE NEED
        # master type: WORKFLOW || FORM 

        Steps = mongo.db.steps.find({"master": master['name']}).sort("step_id",1)
        # .sort("step_id",1)  {$elemMatch:{$eq:"auto"}}}, {"_id":0})
        for step in Steps:
            print(step['step_id'])
            output.append({
            "step_id": step['step_id'],
            "master_name": master['name'],
            "master_type": master['type'],
            "name": step['name'],
            "type": step['type'],
            "configuration": step['configuration']
            })

    return jsonify(output)




# ######################
#   GET DATA FOR GRID
########################
@app.route('/data_grid', methods=['GET'])
def get_datas():
    try:
        dataCollection = mongo.db.datas
        gridCollection = mongo.db.grids
        
        cols = gridCollection.find_one({"name":"grid1"}, {"cols": 1, "_id":1})
        data = dataCollection.find()
        print(cols['cols'])
        # try:
        #     record = cols.next()
        # except StopIteration:
        #     print("No columns in the cursor grid!")
        # print(record)
        # for col in cols:
        #     print(col['cols'])
        output = []
        output.append({'colNames': cols['cols']})
        
        for s in dataCollection.find():
            print(s)
            # print(str(s["_id"]))
            record = {"step_id": str(s["step_id"])}
            record.update({"_id": str(s["_id"])})
            # READ ADD COLS FROM DATA GRID CONFIG
            for colName in cols['cols']:
                # colsName.append(colName) 
                print(colName)
                # print("value")
                # print(s[colName])
                if isinstance(colName,dict):
                    # print(colName)
                    # print('is dict')
                    for keyName in colName:
                        # print("keyName " + keyName )
                        # print("keyName: " + keyName)
                        # print(colName[keyName])
                        tmpField = {}
                        
                        for i,val in enumerate(colName[keyName]):
                            try:
                                # print("val: " +val)
                                tmpFieldValue = ''
                                #  value du champs field (ex value of profile.nom)
                                # print(s[keyName][i][val])
                                # print(val)
                                # print(s[keyName][0][val])
                                # if s[keyName][0][val] != '':
                                #     print('ici')
                            #     # print('169' + val)
                            #     print(s[keyName][0][val])
                                
                                # tmpField.update({val: s[keyName][i][val]})
                                newKeyName = keyName + '_' + val
                                # print('keyname: 185 ' + newKeyName)
                                tmpFieldValue = s[keyName][i][val]
                                if(tmpFieldValue != ''):
                                    # print(newKeyName)
                                    # print("tmpFieldValue "+  tmpFieldValue)
                                    
                                    record.update({newKeyName: tmpFieldValue})
                            #     print(record)
                            except KeyError:
                                print('not defined')
                        
                else:
                    print('not dic')
                    record.update({colName: s[colName]})
            print(record)
            
            output.append(record)
            
        
        # print(output)

        # cursor = eval(data)

    # docs_list  = list(data)
    # print(docs_list)
        return jsonify(output)

    except (ValueError, KeyError, TypeError):
        resp = Response({"JSON Format Error."}, status=400, mimetype='application/json')
        return resp

    # return jsonify(json.dumps(docs_list, default=json_util.default))

    # return jsonify(docs_list)

############### 
#  SEND EMAIL #
###############
# @app.route('/send_mail', methods=['GET'])
# def send_email():
#     mailId = request.args['mail_id']
#     mailCollection = mongo.db.mails
#     mailInfo = mailCollection.find()
#     for a in mailInfo:
#         msg = Message("Hello",
#                   sender=a['sender'],
#                   recipients=[a['recipient']])
#         print(a['sender'])
#         mail.send(msg)
#         print(a["recipient"])
#         print(a["subject"])
#     print(mailId)
#     return ('OK')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# def main():
#     """Main entry point of the app."""
#     try:
#         http_server = WSGIServer(('0.0.0.0', 8080),
#                                  app,
#                                  log=logging,
#                                  error_log=logging)

#         http_server.serve_forever()
#     except Exception as exc:
#         logger.error(exc.message)
#     finally:
#         # get last entry and insert build appended if not completed
#         # Do something here
#         pass