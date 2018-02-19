# -*- coding: utf-8 -*-
import os

from flask import Flask, request, Response, jsonify, make_response, stream_with_context
from flask_pymongo import PyMongo
from pymongo import MongoClient
import pymongo
from flask_cors import CORS, cross_origin
import json
from bson import json_util
from bson.objectid import ObjectId
from datetime import datetime
import cloudinary 
import cloudinary.uploader
import cloudinary.api
import jwt
from flask_mail import Mail, Message
from werkzeug.datastructures import ImmutableMultiDict
from passlib.hash import pbkdf2_sha256
import operator
from email.mime.text import MIMEText
import smtplib
import csv
from functools import wraps
# from flask.api import status
from flask import after_this_request


import io
import mimetypes
from werkzeug.datastructures import Headers




app = Flask(__name__)
mail = Mail()
CORS(app)
MONGO_URL = os.environ.get('MONGO_URL')


# app.register_blueprint(auth)

#DEV PURPOSE
if not MONGO_URL:
    #  MONGO_URL = "mongodb://localhost:27017/cargo_friend";
    MONGO_URL = "mongodb://localhost:27017/auto";

app.config['MONGO_URI'] = MONGO_URL
mongo = PyMongo(app)
mail.init_app(app)


cloudinary.config( 
  cloud_name = "htamml3fv", 
  api_key = "479571498319886", 
  api_secret = "wBUZ-eReQJpK_mninA2SMIP7WzI" 
)

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

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

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
    collectionName = request.args['col_name']
    print(collectionName)
    filtersName = request.args['filters_name'].split(',')
    filtersValue = request.args['filters_value'].split(',')
    valueToSelect = request.args['select']
    returnType = request.args['return_type']
    # key = ', {"'+ valueToSelect + '":1}'
    key = 'key: "'+ valueToSelect + '",'

    # print(filtersValue)
    isFiltered = False
    condition = '{'
    for (name, value) in zip(filtersName,filtersValue):
        if (value != ''):
            isFiltered = True
            if (is_number(value) and name == 'year_range'):
                print("convert")
                condition = condition + '"' + name + '":' + value +',' 
            else:
                print(value)
                condition = condition + '"' + name + '":"' + value +'",' 
                
            #condition = '{"' + filtersName[i] + '":"' + filtersValue[i] +'"}'
            
            # SI LA COLLECTION CONTIENT PLUSIEURS CHAMPS, SELECT CONTIENT CELUI A RAMENER
            # if 'select' in request.args: 
            # print(request.args['select'])
    print(condition)
    condition = condition[:-1]
    condition = condition + '}'     
    if returnType == 'btn':
        print('**********************************')
        # IF WE NEED TO TREAT A DATE RANGE
        if (valueToSelect == "date_debut"):
            collection = 'mongo.db.vehicules.aggregate([{"$match" : { "modele" : "'+ filtersValue[0]  +'" }},{ "$group": { "_id": "$modele", "maxDate" : { "$max": "$date_debut"}, "minDate": {"$min": "$date_fin"}}}])'
            cursor = eval(collection)

            docs_list  = list(cursor)

            minDate = docs_list[0]['minDate']
            maxDate = docs_list[0]['maxDate']

            output = []
            
            for i in range(minDate,maxDate):
                output.append(i)

            output.append(maxDate)
            print(output)
            return jsonify(output)

        else:
            print('iiiiiiiiiiiiiiiiiiiiiii')
            print(isFiltered)
            if (isFiltered):
                collection = 'mongo.db.'+collectionName+'.find('+ condition +').distinct("'+valueToSelect+'")'
                print(collection)
            else:
                collection = 'mongo.db.'+collectionName+'.find().distinct("'+valueToSelect+'")'
            
            cursor = eval(collection)

            docs_list  = list(cursor)
            print(docs_list)
            docs_list.sort()
            print(docs_list)
            return json.dumps(docs_list, default=json_util.default)
            


    else:
        output = []
        collection = 'mongo.db.'+collectionName+'.find().sort("order", 1)'
                
        cursor = eval(collection)
        for c in cursor:
            print(c['name'])
            output.append({ "name": c['name'], "url": c['url'], "list": c['modeles']})
        return jsonify(output)
    # for doc in cursor:
    #     json_doc = json.dumps(doc, default=json_util.default)
    #     output.append(json_doc)
    #     # output.append({lstField[0]: s[lstFi eld[0]])}
    #return output

###################################
# UPLOAD A FILE TO CLOUDIFIER      #
###################################

@app.route('/store_file', methods=['POST'])
@cross_origin()
def storeFile():
    print(request)
    print(request.files)
    
    imd = request.files
    fileList = imd.getlist('uploadFile')
    # data = request.files.get('uploadFile')
    # print(data)
    print(fileList)
    print("store_file")
    
    resultList = []
    for f in fileList:
        result = cloudinary.uploader.upload(f)
        if result:
            jsonResult = {
                'id_img' : result['public_id'],
                'file_url': result['url'],
                'step_name': f.filename 
            }
            resultList.append(jsonResult)
    print(resultList)
    # if 'file' not in data:
    #     print("not a file")
    # else:
    #     print("data is a file")
    # file = request.files['FileStorage']
    # print(file.filename)
    # value = request(force=True)
    print('ok')
    return jsonify(resultList)

####################################
# SAVE STEP INTO COLLECTION
#####################################
@app.route('/save_datas', methods=['POST'])
def save_step():
    referer = request.headers.get('referer')
    print(referer)
    print(request.get_json(force=True))

    print('headers\n')
    print(request.headers.get('request'))
    data = request.get_json(force=True)
    print(data)
    fileNameList = []
    objToSave = {}
    safeOrigin = False
    x = 0
    for obj in data:
        print(x)
        print(obj)
        
        # A MODIFIER QUAND J'AURAI CREE TOKEN
        if 'app_name' in obj:
            if obj['app_name'] == 'ballet':
                safeOrigin = True
            if obj['app_name'] == 'auto':
                safeOrigin = True
            if obj['app_name'] == 'modele':
                safeOrigin = True
        if 'token' in obj:
            tokenFromApp = obj['token']
            collectionName = obj['app_name']
            print(collectionName)
            print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
            masterData = mongo.db.master.find_one({"name": collectionName})
            encodedToken = jwt.encode({'key_gen': masterData['key_gen']}, 'secret', algorithm='HS256')
            print(tokenFromApp)
            print(encodedToken)
            if collectionName == 'play':
                if referer == 'https://bde-play.herokuapp.com/step':
                    # https://bde-play.herokuapp.com
                    # if str(encodedToken) == tokenFromApp:
                    safeOrigin = True
                    print('key OK we can save source is safe')
            
            print("SAFE ORIGIN: ")
            print(safeOrigin)    
        else:
            
# ETAT TRANSACTION: 1= NEW; 2=OFFRE EN COURS; 3=ACHETE; 4 = VENDU

            # if 'file_uploaded' in obj:
            #     fileNameList.append({"name": obj['nom'], "details": [{"file_url": obj['file_url'] }]})
            #     print(obj['nom'])
            # print(obj)
            if 'app_name' in obj:
                collectionName = obj['app_name']
                # SET NEEDED DATA
                if obj['app_name'] == 'ballet':
                    obj.update({
                    "group": "WITHOUT GROUP", "DNI": "", "BECA": "",
                    "notes": "", "father": "", "dob": "", 
                    "contract":"", "intolerencia": "", "residence_duration": "", 
                    "phone2":"", "email2": "", "registred":False})
                if obj['app_name'] == 'play':
                    obj.update({ "paid": False, "registred":False})
                if obj['app_name'] == 'auto':
                    obj.update({
                        "offre_rachat": 0,
                        "achete": False,
                        "prix_vente": 0,
                        "etat_transaction": 1   
                    })
            objToSave.update(obj)
        x = x + 1

    currentDate = { "currentDate" : str(datetime.now())}
    # print(obj['master'])
    objToSave.update(currentDate)
    
    print(objToSave)    
    if safeOrigin:
        collection = 'mongo.db.'+collectionName+'.insert_one('+ str(objToSave) +')'

        new_id = eval(collection)
        print(new_id.inserted_id)
        # docs_list  = list(cursor)

        # new_id = mongo.db.insert(objToSave)
        # print(new_id)
        return str(new_id.inserted_id)
    else:
        return str('NO_NO_NO')

    # Response(
    # json_util.dumps({'id': id},mimetype='application/json')
    # ) 
    # return json_dumps(new_id, default=newEncoder)

##################################
# UPDATE CHECKBOX 
###################################
@app.route('/update_checkbox', methods=['POST'])
@cross_origin()
def updateCheckBox():
    data = request.get_json(force=True)
    idRecord = data['_id']
    newVal = data['value']
    fieldName = data['field_name']
    if "appName" in data:
        collectionName = data['appName']
        boolVal = str(newVal)
        # query = "mongo.db."+collectionName+.update({'_id': "+ idRecord +"},{ '$set': {"+ fieldName +":"+ newVal + "}},"+ upsert=False + ")"
        collection = eval("mongo.db."+collectionName)
    
        query = "mongo.db."+collectionName+".update({'_id': ObjectId('"+ idRecord+ "')}, { '$set':{'"+fieldName+"':"+ boolVal+"}}, upsert="+str(False)+")"
        new_id = eval(query)
    return str(new_id)

##################################
# UPDATE COURSE TYPE 
###################################
@app.route('/update_course_type', methods=['POST'])
@cross_origin()
def updateCourseType():
    data = request.get_json(force=True)
    idStudent = data['_id']
    course = data['course_type']

    new_id = mongo.db.ballet.update({'_id': ObjectId(idStudent)}, { '$set': {"course_type": course}})
    return str(new_id)

##################################
# SET GROUP TO USER 
###################################
@app.route('/set_group_to_user', methods=['POST'])
@cross_origin()
def setGroupToUser():
    data = request.get_json(force=True)
    idRecord = data['_id']
    newVal = data['groupName']
    new_id = mongo.db.ballet.update({'_id':  ObjectId(idRecord)}, { '$set':{'group': newVal}}, upsert=False)
    print(new_id)
    print(idRecord)

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
    print(appName)
    master = mongo.db.master.find_one({"name": appName})
    print(master)
    # for master in masterSteps:

    # print(m['save_button'])
        
    # master name: TO FIND WHICH STEPS WE NEED
    # master type: WORKFLOW || FORM || ADMIN 

    # if (pbkdf2_sha256.verify(credentials['password'], user['password'])):

    encodedToken = jwt.encode({'key_gen': master['key_gen']}, 'secret', algorithm='HS256')

    if 'template' in master:
        template = mongo.db.templates.find_one({"master": master['template']})
        design_page = {
            "back_btn" : template['back_btn'],
            "background_color" : template['background_color'],
            "list_btn" : template['list_btn'],
            "panel_heading" : template['panel_heading'],
            "hover_btn" : template['hover_btn'],
            "grid_btn" : template['grid_btn']
        }


    Steps = mongo.db.steps.find({"master": appName}).sort("step_id",1)
    # .sort("step_id",1)  {$elemMatch:{$eq:"auto"}}}, {"_id":0})
    logoUrl = ""
    if "logo_url" in master:
        logoUrl = master['logo_url'] 
    
    menu_level = 0
    if "menu_level" in master:
        menu_level = master['menu_level']
    
    output.append({
        "default_language": master['default_language'],
        "languages": master['languages'],
        "template": master['template'],
        "logo_url": logoUrl,
        "design" : design_page,
        "menu_level": menu_level 
    })

    for step in Steps:
        print(step['step_id'])
        
        if 'conditions' in step: 
            conditions = step['conditions']
        else:
            conditions = []
        
               
        output.append({
        "step_id": step['step_id'],
        "master_name": master['name'],
        "master_type": master['type'],
        "logo_url": logoUrl,
        "name": step['name'],
        "type": step['type'],
        "configuration": step['configuration'],
        "conditions": conditions,
        "token": str(encodedToken)
        })
        

    return jsonify(output)

########################
# GET DETAILS AUTO APP (CAR APP)#
########################
@app.route('/grid_details', methods=['GET'])
@cross_origin()
def get_details():
    objId = request.args['id']
    print(objId)
    dataCollection = mongo.db.auto
    details = dataCollection.find_one({"_id":ObjectId(objId)})
    # result = mongo.db.datas.find_one({'_id': ObjectId(idRecord)})
    # print(details['import'])
    print('jjjjjjjjjjjj')
    # print(details)
    return json.dumps(details, default=json_util.default)

########################
# GET DETAILS CARGO (CARGO APP)  #
########################
@app.route('/cargo_details', methods=['GET'])
@cross_origin()
def get_cargo_details():
    objId = request.args['id']
    print(objId)
    dataCollection = mongo.db.rates
    details = dataCollection.find_one({"_id":ObjectId(objId)})
    # result = mongo.db.datas.find_one({'_id': ObjectId(idRecord)})
    # print(details['import'])
    print('jjjjjjjjjjjj')
    # print(details)
    return json.dumps(details, default=json_util.default)



########################
# GET TECH DETAILS (CAR APP)  #
########################
@app.route('/tech_details', methods=['GET'])
@cross_origin()
def get_tech_details():
    version = request.args['version']
    dataCollection = mongo.db.vehicules
    details = dataCollection.find_one({"version": version})
    # result = mongo.db.datas.find_one({'_id': ObjectId(idRecord)})
    # print(details['import'])
    print('tech details')
    # print(details)
    return json.dumps(details, default=json_util.default)

########################
# GET DETAILS BALLET (BALLET APP)  #
########################
@app.route('/ballet_details', methods=['GET'])
@cross_origin()
def get_ballet_details():
    objId = request.args['id']
    print(objId)
    dataCollection = mongo.db.ballet
    details = dataCollection.find_one({"_id":ObjectId(objId)})
    # result = mongo.db.datas.find_one({'_id': ObjectId(idRecord)})
    # print(details['import'])
    print('jjjjjjjjjjjj')
    # print(details)
    return json.dumps(details, default=json_util.default)

# ######################
#   GET DATA FOR GRID
########################
@app.route('/data_grid', methods=['GET'])
@cross_origin()
def get_datas():
    # try:
        gridName = request.args['grid_name']
        filterSelected = request.args['filter']
        print(gridName)
        print(filterSelected)
        print('start grid')

        gridCollection = mongo.db.grids
        
        grid = gridCollection.find_one({"name":gridName })
        if "collection" in grid:
            collectionName = grid['collection']
            tmpDataCol = "mongo.db." + collectionName
            dataCollection = eval(tmpDataCol)
        elif "master" in grid:
            collectionName = grid['master']
            tmpDataCol = "mongo.db." + collectionName
            dataCollection = eval(tmpDataCol)
        else:
            dataCollection = mongo.db.datas

        print( )
        
        # FILTERED
        if 'filtered' in grid:
            objFilter = {}
            for i, val in enumerate(grid['filtered']):
                print(val)
                if grid['filtered'][i]['value_by'] == 'filterSelected':
                    valueBy = filterSelected
                else:
                    valueBy = grid['filtered'][i]['value_by']
                obj = { grid['filtered'][i]['by']:valueBy }
                objFilter.update(obj)

            print(objFilter)

            datas = dataCollection.find(objFilter)
        else:
            datas = dataCollection.find({})
        
        # SORTED
        if 'sorted' in grid:
            # sortBy = grid['sorted'][0]
            sortBy = []
            for toSort in grid['sorted']:
                by = toSort['by']
                order = 1
                if order in toSort:
                    order = toSort['order']
                # print(toSort.values())
                sortBy.append((by, order))
            # datas.sort([(sortBy,-1), ("duration", 1)])
            datas.sort(sortBy)
            
       
            print(sortBy)
        
        
        output = []
        config = {}
        if "details" in grid:
            config.update({'config': grid['cols']})
            # output.append({'config': grid['cols']})
        else:
            config.update({'config': grid['cols']})

        if 'export' in grid['details']:
            config.update({"details": {"export": True, "export_id":grid['details']['export_id']}})
        output.append(config)

        course_list = []
        # Pour chaque élement de la collection data
        for s in datas:
            # print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC")
            # print(s)
            # print(str(s["_id"]))
            if "step_id" in s:
                record = {"step_id": str(s["step_id"])}
            else:
                record = {}
            record.update({"_id": str(s["_id"])})

            if "id_rate" in s:
                record.update({"id_rate": str(s["id_rate"])})
            # READ ADD COLS FROM DATA GRID CONFIG
            listValuesFieldPanel = []
            # pour chaque element defini dans la collection grid
            for dicCol in grid['cols']:
                # colsName.append(colName) 
                if 'field_panel_name' in dicCol: 
                #     print('dans field panel')
                #     print(dicCol['field_panel_name'])
                #     print(dicCol['field_panel_values'])
                # # print("value")
                # print(s[colName])
                   
                    
                    # print(colName)
                    # print('is dict')
                    # for keyName in dicCol:
                    #      print("keyName " + keyName )
                    #     # print(colName[keyName])
                    #     # 
                        
                    for i,val in enumerate(dicCol['field_panel_values']):
                        try:

                            cle = dicCol['field_panel_name'] + '_' + val['data']

                            valeur = next((item for item in s[dicCol['field_panel_name']] if item.get(val['data'])), '')
                            if (valeur != ''):
                                valeur = valeur[val['data']]

                            record.update({cle:valeur})

                        except KeyError:
                            print('not defined')
                    # record.update({dicCol['field_panel_name']: listValuesFieldPanel})    
                elif 'type' in dicCol: 
                    if dicCol['type'] == 'checkbox':
                        if dicCol['data'] in s:
                            record.update({dicCol['data']: s[dicCol['data']]})
                        else:
                            record.update({dicCol['data']: False})
                        
                    if dicCol['type'] == 'combo':
                        if (len(course_list) == 0):
                            course_cursor = mongo.db.balletCourse.find({"stage": filterSelected},{"name":1})
                            print(filterSelected)
                            print(course_cursor)
                            for courses in course_cursor:
                                course_list.append(courses['name'])
                            print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                            print(course_list)
                        if dicCol['data'] in s:
                            record.update({dicCol['data']: s[dicCol['data']]})
                            record.update({'course_list': course_list}) 

                        
                else:
                    #SI PAS FIELD PANEL ALORS COLONNE CLASIQUE TITLE + DATA
                    record.update({dicCol['data']: s[dicCol['data']]})
                    record.update({'title': dicCol['title']})
            
            
            
            if 'details' in grid:
                details = {}
                if 'activated' in grid['details']:
                    details.update({"activated": grid['details']['activated'] })
                else:
                    details.update({"activated": False })
                if 'group' in grid['details']:
                    details.update({"group": grid['details']['group'] })
                else:
                    details.update({"group": False })


                record.update({"details": details})
            else:
                record.update({"details": {"activated": False, "group":False}})
            

            if 'cargo_details' in grid:
                if 'activated' in grid['cargo_details']:
                    record.update({"cargo_details": {"activated": True}})
                else:
                    record.update({"cargo_details": {"activated": False}})
            else:
                record.update({"cargo_details": {"activated": False}})  

            # print(listValuesFieldPanel)
            output.append(record)
            # print("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
            # print(record)
            # print(grid)
            # print(grid['filtered'][0]['by'])
        
        # print(output)

        # cursor = eval(data)

    # docs_list  = list(data)
    # print(docs_list)
        # print(output)
    
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
@app.route('/get_grids', methods=['POST'])
@cross_origin()
def getGrids():
    
    # MAYBE WE CAN REMOVE THIS ARG IF WE USE 1 APP FOR ONLY ONE PROJECT
    # master = request.args['master']
    data = request.get_json(force=True)
    # master = request.args['master']
    gridCollection = mongo.db.grids
    print(data)
    print("master")
    
    gridList = gridCollection.find({"activated": True, "master": data['master'] })
    dataCollection = eval('mongo.db.'+data['master'])
    output = []
    if data['master'] == 'ballet':
        listCourse = []
        for grid in gridList:
            if "type" in grid and grid['type'] == 'get_grids':
                for infos in grid['list']:
                    for children in infos['children']:
                        res = dataCollection.count({"stage":infos['value'], "course_type":children})
                        if res == 0:
                            filters = gridCollection.find({"name": children},{"filtered": 1})
                            clauses = {}
                            for filtered in filters:
                                for obj in filtered['filtered']:
                                    if (obj['value_by'] != 'filterSelected'):
                                        clauses.update({obj['by']:obj['value_by']})
                                    else:
                                        clauses.update({obj['by']:infos['value']})
                                    
                            if clauses == {}:
                                nb = 0
                            else:
                                nb = dataCollection.count(clauses)
                        else:
                            nb = dataCollection.count({"stage":infos['value'], "course_type":children, "registred": True})
                        listCourse.append({'name':infos['value'],'children': children, 'nbRecords': nb })
                output.append({  "name": grid['name'], "listBtn":listCourse, "display": True })
            else: 
                output.append({"name": grid['name'], "display": True})
    else:
        try:
            for grid in gridList:
                # if "type" in grid:
                #     output.append({  "name": grid['name'], "listBtn": grid['list'], "display": True })
                # else: 
                output.append({"name": grid['name'], "display": True})

        except StopAsyncIteration:
            print("Empty cursor")

    return jsonify(output) 

###############
# LOG MAIL    #    
###############
@app.route('/log_mail', methods=['POST'])
def log_email():
    

    data = request.get_json(force=True)

    app.config['MAIL_SERVER']='smtp.live.com'
    app.config['MAIL_PORT'] = 25
    app.config['MAIL_USERNAME'] = 'anthony_dupont@hotmail.com'
    app.config['MAIL_PASSWORD'] = 'Goodbye2012'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False

    mail.init_app(app)    

    html = "<div>ERROR IN APP " + str(data) +"</div>"          
    msg = Message( "ERROR LOG",
    sender=('BALLET', "anthony_dupont@hotmail.com"),
    html=html,
    recipients=["anthony_dupont@hotmail.com"])       

    mail.send(msg)
    return ('OK')

############### 
#  SEND EMAIL #
###############
@app.route('/send_mail', methods=['POST'])
def send_email():
    
    data = request.get_json(force=True)

    mailId = data['mail_id']
    formId = data['form_id']
    appName = data['app_name']

    mailCollection = mongo.db.mails
    mailInfo = mailCollection.find_one({"mail_id": int(mailId)})


    # if appName == 'ballet':
    app.config['MAIL_SERVER']='smtp.live.com'
    app.config['MAIL_PORT'] = 25
    app.config['MAIL_USERNAME'] = 'armanaly@hotmail.com'
    app.config['MAIL_PASSWORD'] = 'Goodbye2012'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False

    mail.init_app(app)

    if appName == 'ballet':
    
        dataCollection = mongo.db.ballet
        formData = dataCollection.find_one({"_id":ObjectId(formId)})
        profile = formData['profile']
        nom     = profile[1]['nom']
        prenom  = profile[0]['firstname']
        email   = profile[3]['email']
    
    sender  = mailInfo['sender']

    # PREPARE CONFIRMATION MSG
    html = "Thanks for your interest in Armanaly! <br> This is an automatic notification following your registration in our application test."          
    
    try:
        msg = Message( mailInfo['subject'],
        sender=('Armanaly', sender),
        html=html,
        recipients=[email])       

        mail.send(msg)
    except Exception as err:
        print(err)
        print(err.args)
        return str(err)
        
        # # PROD
        # app.config['MAIL_SERVER']='smtp.live.com'
        # app.config['MAIL_PORT'] = 25
        # app.config['MAIL_USERNAME'] = 'bde.play.2018@hotmail.com'
        # app.config['MAIL_PASSWORD'] = 'bdeplay2018'
        # app.config['MAIL_USE_TLS'] = True
        # app.config['MAIL_USE_SSL'] = False
        
        # TEST

        # me = 'anthony_dupont@hotmail.com'
        # password = 'Goodbye2012'
        
        # dataCollection = mongo.db.ballet
        # formData = dataCollection.find_one({"_id":ObjectId(formId)})
        # sender = mailInfo['sender']

        # # GET INFO TO PUT IN TEMPLATE
        # profile  = formData['profile']
        # prenom   = profile[0]['firstname']
        # nom      = profile[1]['nom']
        # email    = profile[3]['email']
        # stage    = formData['stage']
        # course   = formData['course_type']

        

        # confirmMsg = MIMEText("Dear "+ prenom + ",\n\nWe have received your registration form and will contact you in a short time.\n\nYours sincerely,\n\n----------------------------------------------------------------------------------------\n\nEstimado/a "+ prenom + ",\n\nHemos recibido su formulario de registro, contactaremos con usted en breve.\n\nAtentamente,  \n\nYulia Mahilinskaya \nMobile: + 34 609816395\nSkype: russianmastersballet\n ")
        # confirmMsg['Subject'] = mailInfo['subject']
        # confirmMsg['From'] = me
        # confirmMsg['To'] = email

        
        # session = smtplib.SMTP("smtp.live.com", 25)
        # session.login(me, password)
        # session.sendmail(me, me, confirmMsg.as_string())
        # session.quit()


        # mail.send(msg)
      
      
        # session = smtplib.SMTP("smtp.1and1.com", 587)
        # session.login(me, password)
        # session.sendmail(me, email, msg.as_string())
        # session.quit()

        # SEND NOTIFICATION TO ADMIN
        # msg = MIMEText(prenom + " " + nom + " has registred to the "+ course + " course for "+ stage   )

        # session = smtplib.SMTP("smtp.1and1.com", 587)
        # session.login(me, password)
        # session.sendmail(me, me, msg.as_string())
        # session.quit()
        # mail.send(msg)
      

        # # SEND MESSAGE TO ADMIN WITH DATABACKUP
        
        # bckMessage = MIMEText(prenom + " " + nom + " has registred to the "+ course + 
        #         " course for "+ stage +
        #         "\n\n age:  " + formData['age'] +
        #         "\n duration: "+ formData['duration'] +
        #         "\n Residence: "+ formData['residence'] +
        #         "\n Years of  experience: "+ formData['years_of_experience'] +
        #         "\n email: "+ email )
        
      
        # bckMessage['Subject'] = "New registration received"
        # bckMessage['From'] = me
        # bckMessage['To'] = to
        # mail.send(bckMessage)


        # session = smtplib.SMTP("smtp.1and1.com", 587)
        # session.login(me, password)
        # session.sendmail(me, to, bckMessage.as_string())
        # session.quit()

    return ('OK')

#####################
# SIGNUP A NEW USER #
#####################
@app.route('/auth_signup', methods=['POST'])
@cross_origin()
def signup():
    user = request.get_json()
    # Add creation date 
    user.update({ "date_creation" : datetime.now()})

    # Encrypt password
    user.update({"password": pbkdf2_sha256.hash(user['password'])})
    
    try:
        new_id = mongo.db.users.insert(user)
        return jsonify({"processed": True, "message": "User created" })
        
    except expression as identifier:
        pass

#############################
# GET GROUPS BY COURSE_TYPE #
#############################
@app.route('/get_groups', methods=['GET'])
@cross_origin()
def getGroups():
    courseType = request.args['course']
    stage = request.args['stage']
    print(courseType)
    print(stage)
    groups = collection = mongo.db.balletCourse.find({"name": courseType, "stage": stage}).distinct("groups")
    jsonGroups = {}
    jsonGroupsArray= []
    if stage != 'Alicante Winter Intensive 2017':
        
        pipeLine1 = [
            { "$match" : { "$and": [  {"course_type" : courseType, "stage": stage }, 
                                    {"duration" : { "$in": ["1","3"]} }]}}, 
            { "$group": {  "_id": {"group": "$group", "week": "1"}, "count": {"$sum":1} }  }  
        ]
        week1 = mongo.db.ballet.aggregate(pipeLine1)
        print(pipeLine1)
        pipeLine = [
            { "$match" : { "$and": [  {"course_type" : courseType, "stage": stage }, 
                                    {"duration" : { "$in": ["2","3"]} }]}}, 
            { "$group": {  "_id": {"group": "$group", "week": "2"}, "count": {"$sum":1} }  }  
        ]
        week2 = mongo.db.ballet.aggregate(pipeLine)
        print(week1)
        print(week2)
        
        wk1List  = list(week1)
        print(wk1List)
        wk2List  = list(week2)
        print(wk2List)
        print(len(wk1List))
        print(len(wk2List))
        
        try:
            for group in groups:
                jsonGroups = { "group" : group, "lst": []}
                jsonGroupsArray.append(jsonGroups)
        except StopAsyncIteration:
            print("Empty cursor")

        for grp in jsonGroupsArray:
            print(grp)
            
            group1Find = False
            group2Find = False
            for wk1 in wk1List:
                print("wk1")
                if wk1['_id']['group'] == grp['group']:
                    grp['lst'].append({"week": wk1['_id']["week"], "people": wk1['count']})
                    group1Find = True
                    print("week: " + wk1['_id']["week"])
                    print(group + ":" + str(wk1['count']))
                    break
                # jsonGroupsArray.append(jsonGroups)
            for wk2 in wk2List:        
                print("wk2")
                print(grp['group'])
                if wk2['_id']['group'] == grp['group']:
                    grp['lst'].append({"week": wk2['_id']["week"], "people": wk2['count']})
                    grp['lst'].append({"week": "3", "people": wk2['count']})
                    group2Find = True
                    print("week: " + wk2['_id']["week"])
                    print(group + ":" + str(wk2['count']))
                    print(grp['lst'])
                    break
            
            if group1Find == False:
                    grp['lst'].append({"week": "1", "people": 0})

            if group2Find == False:
                    grp['lst'].append({"week": "2", "people": 0})
                    grp['lst'].append({"week": "3", "people": 0})   
            
            grp['lst'].sort(key=operator.itemgetter("week"))


        jsonGroupsArray.sort(key=operator.itemgetter("group"))
        print(jsonGroupsArray)
        jsonGroupsArray.append({"groups": groups})
        return json.dumps(jsonGroupsArray, default=json_util.default)
    else:
        jsonGroupsArray.append({ "group" : "WITHOUT GROUP", "lst": []})
        for group in groups:
            jsonGroups = { "group" : group, "lst": []}
            jsonGroupsArray.append(jsonGroups)
        
        pipeLine = [
            {"$match": {"stage": "Alicante Winter Intensive 2017"}}, 
            { "$group": { "_id": "$group", "count": {"$sum":1}}}  
        ]
        groups_week = mongo.db.ballet.aggregate(pipeLine)
        groups_weekList  = list(groups_week)

        
        for grp in jsonGroupsArray:
            print(grp['group'])
            print('XXXXXXXXXX')
            groupFound = False
            for group in groups_weekList:
                print(group['_id'])
                if grp['group'] == group['_id']:
                    grp['lst'].append({"week": 1, "people": group['count']})
                    groupFound = True
                    
            if groupFound == False:
                grp['lst'].append({"week": 1, "people": 0})
            grp['lst'].sort(key=operator.itemgetter("week"))
        jsonGroupsArray.sort(key=operator.itemgetter("group"))
        print(jsonGroupsArray)
        jsonGroupsArray.append({"groups": groups})

        return json.dumps(jsonGroupsArray, default=json_util.default)

######################################
# SIGN IN                            #
######################################

@app.route('/auth_signin', methods=['POST'])
@cross_origin()
def signin():
    credentials = request.get_json()
    # Add creation date 
    # user.update({ "date_creation" : datetime.now()})
    # output = {}
    print(credentials)
    user = mongo.db.users.find_one({"email": credentials['email'], "master": credentials['app']})
    if (user != None):
        if (pbkdf2_sha256.verify(credentials['password'], user['password'])):
            message = {
                'user': user['email'],
                'exp': 1485972805
            }
            encoded = jwt.encode(message, 'secret', algorithm='HS256')
            print(encoded)
            output = {"logged": True, "message": "User connected", "token": encoded, "user_id": user['_id'] }
        else:
            print('error')
            output = {"logged": False, "message": "Erreur authentification" }
    else:
        output = {"logged": False, "message": "Erreur authentification" }
    
    return json.dumps(output, default=json_util.default)
    # return output


#############################################
# UPDATE DATA FROM student.service          #
#############################################
@app.route('/update_student', methods=['POST'])
@cross_origin()
def updateStudent():
    formValues = request.get_json()
    print('avant check')
    if checkAuthentication(formValues['token']):
        print('check is true')
        # print(formValues['_id'])
        studentId = formValues['_id']
        # print(studentId['$oid'])
        print(formValues)
        new_id = mongo.db.ballet.update(
            {'_id': ObjectId(studentId['$oid']) }, 
            { '$set':
                { 
                    'DNI': formValues['DNI'],
                    'father': formValues['father'],
                    'BECA': formValues['BECA'],
                    'intolerencia': formValues['intolerencia'],
                    'email2': formValues['email2'],
                    'phone2': formValues['phone2'],
                    'notes': formValues['notes'],
                    'audition': formValues['audition'],
                    'duration': formValues['duration'],
                    'age' : formValues['age'],
                    'course_type' : formValues['course_type'],
                    'registred': formValues['registred'],
                    'profile.5.country': formValues['country'],
                    'profile.6.city': formValues['city'],
                    'profile.4.birthdate': formValues['birthday'],
                    'profile.3.email': formValues['email'],
                    'profile.2.phone': formValues['phone'],
                    'profile.7.studied_places': formValues['studied_places'],
                    'years_of_experience' : formValues['years_of_experience']
                }
            }, upsert=False)
        return json.dumps({'message': 'User updated'}, default=json_util.default)
    else:
        return  json.dumps({'message': 'error Auth'}, default=json_util.default)
        
    
##########################################
# EXPORT DATA TO EXCEL (BALLET APP)      #
##########################################

@app.route('/export_excel', methods=['POST'])
@cross_origin()
def exportExcel():

    formValues = request.get_json()
    
    stage = formValues['stage']
    course = formValues['course_type']
    
    export_id = formValues['export_id']
    print(stage)

    def generate():
        print(course)
        data = io.StringIO()
        w = csv.writer(data)



        if export_id > 0:
            configExport = mongo.db.exports_templates.find({"export_id": export_id})
            colTitle = []
            for cols in configExport[0]['cols']:
                colTitle.append(cols['title'])
            w.writerow(( colTitle ))

            clause = {}
            for filterValue in configExport[0]['filtered']:
                print(filterValue)
                clause.update({filterValue['by']: filterValue['value_by']})
            
            students = mongo.db.ballet.find(clause)
        else:
             # write header
            w.writerow((
                    'Course', 'Grupo', 'Nombre', 
                    'Apellido', 'Fecha',  'DNI',
                     'Duration', 'Contrato', 'Ciudad', 'pagado',
                    'Telefono', 'Telefono 2', 'E-mail' ,
                    'E-mail 2', 'Padres', 'Escuela', 'notas'
                   ))
        
            if course == 'New demands':
                students = mongo.db.ballet.find({"stage": stage, "course_type": course}).sort( "group", 1).sort("course_type", 1)
            else: 
                students = mongo.db.ballet.find({"stage": stage, "course_type": course, "registred": True}).sort( "group", 1).sort("course_type", 1)

        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        try:
            for student in students:
                if export_id > 0:
                    values = []
                    for colsValue in configExport[0]['cols']:
                        # print(colsValue['data'])
                        tmpColVal = colsValue['data']
                        # print("tmpColVal: " + tmpColVal)
                        if 'ori' in colsValue:
                            ori = student[colsValue['ori']]
                            for i, val in enumerate(ori):
                                if tmpColVal in val:
                                    values.append(ori[i][tmpColVal])
                                    break
                        else:
                            values.append(student[tmpColVal])
                            # print(student[tmpColVal])
                    w.writerow((values))
                    
                        
                else:
                    profile  = student['profile']
                    prenom   = profile[0]['firstname']
                    nom      = profile[1]['nom']
                    phone    = profile[2]['phone']
                    email    = profile[3]['email']
                    city     = profile[6]['city']
                    birthday = profile[4]['birthdate']
                    studiedPlace = profile[7]['studied_places']

                    paid = 'no'
                    if "paid" in student:
                        if student["paid"] == True:
                            paid = 'si'

                    w.writerow((
                        student['course_type'], student['group'], prenom,
                        nom, birthday, student['DNI'],
                        student['duration'],'', city, paid,
                        phone, student['phone2'], email,
                        student['email2'], student['father'] ,studiedPlace, student['notes']
                    
                    ))
                yield data.getvalue()
                data.seek(0)
                data.truncate(0)
            
        except StopAsyncIteration:
            print("Empty cursor")   
    # add a filename
    headers = Headers()
    headers.set('Content-Disposition', 'attachment', filename='log.csv')
    
    # stream the response as the data is generated
    return Response(
        stream_with_context(generate()),
        mimetype='text/csv', headers=headers
    )

def checkAuthentication(token):
    try:
        print(token)
        if token != None:
            print('token valid')
            payload = jwt.decode(token, 'secret', algorithm='HS256')
            print(payload)
            print('dDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD')
            result = True
        else:
            print('token invalid')
            result = False
        return result
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return json.dumps({'message': 'Token is invalid'}, default=json_util.default)


@app.route('/make_offer', methods=['POST'])
@cross_origin()
def makeOffer():
    
    formValues = request.get_json()
    token = formValues['token']
    print(formValues['token'])
    _id = formValues['_id']
    if checkAuthentication(formValues['token']):
        carId =  formValues['_id']
        new_id = mongo.db.auto.update(
            {'_id': ObjectId(carId['$oid']) }, 
            { '$set':
                { 
                    'offre_rachat': formValues['offre_rachat'],
                    'etat_transaction': 2
                }
            }, upsert=False)
        
        # new_id = eval(query)
        print('token Valid')
        return jsonify({"etat": 2,"title": "Offre en cours", "message": "Offre rachat enregistrée" }) 
    else: 
        print('token invalid')
        return jsonify({"title": "Erreur", "message": "Veuillez-vous connecter pour mettre à jour ce champs"})




@app.route('/save_buying_price', methods=['POST'])
@cross_origin()
def buyingPrice():
    formValues = request.get_json()
    token = formValues['token']
    print(formValues['token'])
    _id = formValues['_id']
    if checkAuthentication(formValues['token']):
        carId =  formValues['_id']
        new_id = mongo.db.auto.update(
            {'_id': ObjectId(carId['$oid']) }, 
            { '$set':
                { 
                    'prix_achat': formValues['price'],
                    'etat_transaction': 3
                }
            }, upsert=False)
        
        # new_id = eval(query)
        print('token Valid')
        return jsonify({"etat": 3, "title": "Acheté", "message": "Achat véhicule enregistré" }) 
    else: 
        print('token invalid')
        return jsonify({"title": "Erreur", "message": "Veuillez-vous connecter pour mettre à jour ce champs"})

@app.route('/save_selling_price', methods=['POST'])
@cross_origin()
def sellingPrice():
    formValues = request.get_json()
    token = formValues['token']
    _id = formValues['_id']
    if checkAuthentication(formValues['token']):
        carId =  formValues['_id']
        new_id = mongo.db.auto.update(
            {'_id': ObjectId(carId['$oid']) }, 
            { '$set':
                { 
                    'prix_vente': formValues['price'],
                    'etat_transaction': 4
                }
            }, upsert=False)
        
        # new_id = eval(query)
        print('token Valid')
        return jsonify({"etat": 4, "title": "Vendu", "message": "Vente véhicule enregistré" }) 
    else: 
        print('token invalid')
        return jsonify({"title": "Erreur", "message": "Veuillez-vous connecter pour mettre à jour ce champs"})


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