# -*- coding: utf-8 -*-
import os

from flask import Flask, request, Response, jsonify
from flask_pymongo import PyMongo
from pymongo import MongoClient
import pymongo
from flask_cors import CORS, cross_origin
import json
from bson import json_util
from bson.objectid import ObjectId
from datetime import datetime

from flask_mail import Mail, Message

mail = Mail()






app = Flask(__name__)



app.config['MAIL_SERVER']='smtp.live.com'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USERNAME'] = 'anthony_dupont@hotmail.com'
app.config['MAIL_PASSWORD'] = 'Goodbye2012'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

CORS(app)
MONGO_URL = os.environ.get('MONGO_URL')



if not MONGO_URL:
     MONGO_URL = "mongodb://localhost:27017/auto";

app.config['MONGO_URI'] = MONGO_URL
mongo = PyMongo(app)
mail.init_app(app)


# mongo = MongoClient(MONGO_URL)

# mongo = client.test
# connection = pymongo.MongoClient("ds135029.mlab.com", 35029)
# db = connection["heroku_p754dw74"]
# mongo.authenticate("russianBallet", "Axonian456")


# mongo = PyMongo(app, config_prefix='MONGO')
# APP_URL = "http://127.0.0.1:5000"



# def newEncoder(o):
#     if type(o) == ObjectId:
#         return str(o)
#     return o.__str__


@app.route('/')
def index():
    
    return 'SERVER STARTED'

# ##d###############################
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
###################################
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
            print(value)
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

    currentDate = { "currentDate" : datetime.now()}
    objToSave.update(currentDate)

    new_id = mongo.db.datas.insert(objToSave)
    # print(new_id)
    return str(new_id)

    # Response(
    # json_util.dumps({'id': id},mimetype='application/json')
    # ) 
    # return json_dumps(id, default=newEncoder)

##################################
# UPDATE CHECKBOX 
###################################
@app.route('/update_checkbox', methods=['POST'])
@cross_origin()
def updateCheckBox():
    data = request.get_json(force=True)
    idRecord = data['_id']
    newVal = data['value']
    new_id = mongo.db.datas.update({'_id':  ObjectId(idRecord)}, { '$set':{'registred': newVal}}, upsert=False)
    print(new_id)
    print(idRecord)
    # objToSave = {"result": "ok"}
    # for obj in data:
    #     print(obj)
    #     objToSave.update(obj)
    #print()
    return "ok"


# ########################
# GET STEPS CONFIGURATION
##########################
@app.route('/step', methods=['GET'])
@cross_origin()
def get_steps():
    # LIST OF STEPS FROM SELECTED MASTER
    output = []
    appName = request.args['app_name']
    master = mongo.db.master.find_one({"name": appName})
    
    # for master in masterSteps:

    # print(m['save_button'])
        
    # master name: TO FIND WHICH STEPS WE NEED
    # master type: WORKFLOW || FORM 

    Steps = mongo.db.steps.find({"master": appName}).sort("step_id",1)
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
@cross_origin()
def get_datas():
    # try:
        gridName = request.args['grid_name']
        print(gridName)
        print('start grid')
        dataCollection = mongo.db.datas
        gridCollection = mongo.db.grids
        
        grid = gridCollection.find_one({"name":gridName})
        
        if 'filtered' in grid:
            objFilter = {}
            for i, val in enumerate(grid['filtered']):
                obj = { grid['filtered'][i]['by']:grid['filtered'][i]['value_by'] }
                objFilter.update(obj)

            datas = dataCollection.find(objFilter)
        else:
            datas = dataCollection.find()
        print(datas)
        # data = dataCollection.find({filterBy:valueBy})

        
        # try:
        #     record = cols.next()
        # except StopIteration:
        #     print("No columns  in the cursor grid!")
        # print(record)
        # for col in cols:
        #     print(col['cols'])
        output = []
        output.append({'config': grid['cols']})
        print('startDataCollections')
        # Pour chaque élement de la collection data
        for s in datas:
            print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC")
            print(s)
            # print(str(s["_id"]))
            record = {"step_id": str(s["step_id"])}
            record.update({"_id": str(s["_id"])})
            # READ ADD COLS FROM DATA GRID CONFIG
            listValuesFieldPanel = []
            # pour chaque element defini dans la collection grid
            for dicCol in grid['cols']:
                # colsName.append(colName) 
                if 'field_panel_name' in dicCol: 
                    print('dans field panel')
                    print(dicCol['field_panel_name'])
                    print(dicCol['field_panel_values'])
                # print("value")
                # print(s[colName])
                   
                    
                    # print(colName)
                    # print('is dict')
                    # for keyName in dicCol:
                    #      print("keyName " + keyName )
                    #     # print(colName[keyName])
                    #     # 
                        
                    for i,val in enumerate(dicCol['field_panel_values']):
                        try:
                            print(val)
                            # x = val.index({'data':'email'})
                            # print(x)
                            print("for field_panel_values: ")
                            print(i)
                            print(val['data'])
                            print('***************************************')
                            tmpFieldValue = ''
                            #  value du champs field (ex value of profile.nom)
                            # print(s[keyName][i][val])
                            # print(val)
                            # print(s[keyName][0][val])
                            # if s[keyName][0][val] != '':
                            #     print('ici')
                        #     # print('169' + val)
                        #     print(s[keyName][0][val])
                            cle = dicCol['field_panel_name'] + '_' + val['data']
                            print(cle)
                            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@ avant Val")
                            print(s[dicCol['field_panel_name']])
                            print(val['data'])
                           
                            # x = s[dicCol['field_panel_name']].index({'data': val['data']})
                            # print('ddddddddddddddddddddddddddddd ' + x)
                            valeur = next((item for item in s[dicCol['field_panel_name']] if item.get(val['data'])), '')
                            if (valeur != ''):
                                valeur = valeur[val['data']]
                            # valeur = next((item for item in s[dicCol['field_panel_name']] if item.get(val['data'])), None)[val['data']]
                            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            print(valeur)
                            # valeur = s[dicCol['field_panel_name']][i][val['data']]
                            # newVal = 
                            print('--------------------------------------------')
                            print(dicCol)
                            print('+++++++++++++++++++++++++++++++++++++++++++++++')
                            print(s[dicCol['field_panel_name']][i])
                            # print(valeur)
                            record.update({cle:valeur})
                            # listValuesFieldPanel.append({val['data']: s[dicCol['field_panel_name']][i][val['data']]})
                            # tmpField.update({val['data']: s[dicCol['field_panel_name']][i][val['data']]})
                           
                            # print(listValuesFieldPanel[i])
                            # newKeyName = keyName + '_' + val
                            # tmpFieldValue = s[keyName][i][val]
                            # if(tmpFieldValue != ''):
                            #     # print(newKeyName)
                            #     # print("tmpFieldValue "+  tmpFieldValue)
                                
                            #     record.update({newKeyName: tmpFieldValue})
                        #     print(record)
                        except KeyError:
                            print('not defined')
                    # record.update({dicCol['field_panel_name']: listValuesFieldPanel})    
                elif 'type' in dicCol: 
                    if dicCol['type'] == 'checkbox':
                        print('ùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùùù')
                        print(dicCol['type'])
                        
                        if dicCol['data'] in s:
                            record.update({dicCol['data']: s[dicCol['data']]})
                        else:
                            record.update({dicCol['data']: False})
                        
                        
                else:
                    #SI PAS FIELD PANEL ALORS COLONNE CLASIQUE TITLE + DATA
                    print('field_panel_name not in dic')
                    print(dicCol['data'])
                    print(dicCol['title'])
                    print(s[dicCol['data']])
                    record.update({dicCol['data']: s[dicCol['data']]})
                    # record.update({'title': dicCol['title']})
            
            

            print(record)
            print(listValuesFieldPanel)
            output.append(record)
            print("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
            print(grid)
            # print(grid['filtered'][0]['by'])
        
        # p rint(output)

        # cursor = eval(data)

    # docs_list  = list(data)
    # print(docs_list)
        print(output)
        return jsonify(output)

    # except (ValueError):
    #     print("Value Error")
    #     return Response({"JSON Format Error."}, status=400, mimetype='application/json')
    # except (KeyError):
    #     print(KeyError)
    #     return Response({"JSON Format Error."}, status=400, mimetype='application/json')
    # except (TypeError):
    #     print(TypeError)
    #     return Response({"JSON Format Error."}, status=400, mimetype='application/json')
        # resp = Response({"JSON Format Error."}, status=400, mimetype='application/json')
        

    # return jsonify(json.dumps(docs_list, default=json_util.default))

    # return jsonify(docs_list)

###################
# GET LIST OF GRIDS
###################"
@app.route('/get_grids', methods=['GET'])
def getGrids():
    
    # MAYBE WE CAN REMOVE THIS ARG IF WE USE 1 APP FOR ONLY ONE PROJECT
    # master = request.args['master']

    gridCollection = mongo.db.grids

    gridList = gridCollection.find({"activated": True })
    output = []
    try:
        for grid in gridList:
            print(grid['name'])
            output.append({
            "name": grid['name']
            })

    

    except StopAsyncIteration:
        print("Empty cursor")

    return jsonify(output) 


############### 
#  SEND EMAIL #
###############
@app.route('/send_mail', methods=['GET'])
def send_email():
    mailId = request.args['mail_id']
    formId = request.args['form_id']
    
    mailCollection = mongo.db.mails
    dataCollection = mongo.db.datas

    mailInfo = mailCollection.find_one({"mail_id": int(mailId)})
    formData = dataCollection.find_one({"_id":ObjectId(formId)})

    try:
        # GET INFO TO PUT IN TEMPLATE
        age      = formData['age']
        xp       = formData['years_of_experience']
        duration = formData['duration']
        course   = formData['course_type']
        
        profile  = formData['profile']
        nom      = profile[0]['nom']
        email    = profile[2]['email']
        country  = profile[3]['country']

        print(mailInfo)
        sender   = mailInfo['sender']

        # PREPARE CONFIRMATION MSG
        html = "Thank your for your request <br> Nom:" + nom + "<br> Course selected: " + course + "<br> Duration of the course: " + duration
        
        msg = Message("Russian ballet, Automatic email",
                  sender=sender,
                  html=html,
                  recipients=[email])
                  
                  
        mail.send(msg)

    except StopAsyncIteration:
        print("Empty cursor")

    return ('OK')





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