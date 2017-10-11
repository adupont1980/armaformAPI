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
from flask.ext import excel
# from io import StringIO
# import csv
# from openpyxl import Workbook
# from werkzeug.datastructures import Headers


# from flask import excel

mail = Mail()

app = Flask(__name__)

CORS(app)
MONGO_URL = os.environ.get('MONGO_URL')

# app.config['MAIL_SERVER']='smtp.live.com'
# app.config['MAIL_PORT'] = 25
# app.config['MAIL_USERNAME'] = 'anthony_dupont@hotmail.com'
# app.config['MAIL_PASSWORD'] = 'Goodbye2012'
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = False

# app.register_blueprint(auth)

#DEV PURPOSE
if not MONGO_URL:
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

    data = request.get_json(force=True)
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
            objToSave.update(obj)
        x = x + 1

    currentDate = { "currentDate" : str(datetime.now())}
    # print(obj['master'])
    objToSave.update(currentDate)
    
    print(objToSave)    
    if safeOrigin:
        collection = 'mongo.db.'+collectionName+'.insert_one('+ str(objToSave) +')'
        print(collection)
            
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
    master = mongo.db.master.find_one({"name": appName})
    print(master)
    # for master in masterSteps:

    # print(m['save_button'])
        
    # master name: TO FIND WHICH STEPS WE NEED
    # master type: WORKFLOW || FORM 

    # if (pbkdf2_sha256.verify(credentials['password'], user['password'])):
    encodedToken = jwt.encode({'key_gen': master['key_gen']}, 'secret', algorithm='HS256')

    Steps = mongo.db.steps.find({"master": appName}).sort("step_id",1)
    # .sort("step_id",1)  {$elemMatch:{$eq:"auto"}}}, {"_id":0})
    logoUrl = ""
    if "logo_url" in master:
        logoUrl = master['logo_url'] 
    

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
    dataCollection = mongo.db.datas
    details = dataCollection.find_one({"_id":ObjectId(objId)})
    # result = mongo.db.datas.find_one({'_id': ObjectId(idRecord)})
    # print(details['import'])
    print('jjjjjjjjjjjj')
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
        print(grid['master'])
        if "master" in grid:
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
        
        if "details" in grid:
            output.append({'config': grid['cols']})
        else:
            output.append({'config': grid['cols']})
        print('startDataCollections')
        course_list = []
        # Pour chaque élement de la collection data
        for s in datas:
            # print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC")
            # print(s)
            # print(str(s["_id"]))
            record = {"step_id": str(s["step_id"])}
            record.update({"_id": str(s["_id"])})
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
                            # print(val)
                            # print("for field_panel_values: ")
                            # print(i)
                            # print(val['data'])
                            # print('***************************************')
                            # tmpFieldValue = ''
                            #  value du champs field (ex value of profile.nom)
                            # print(s[keyName][i][val])
                            # print(val)
                            # print(s[keyName][0][val])
                            # if s[keyName][0][val] != '':
                            #     print('ici')
                        #     # print('169' + val)
                        #     print(s[keyName][0][val])
                            cle = dicCol['field_panel_name'] + '_' + val['data']
                            # print(cle)
                            # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@ avant Val")
                            # # print(s[dicCol['field_panel_name']])
                            # print(val['data'])
                           
                            # # x = s[dicCol['field_panel_name']].index({'data': val['data']})
                            # print('ddddddddddddddddddddddddddddd ' + x)
                            valeur = next((item for item in s[dicCol['field_panel_name']] if item.get(val['data'])), '')
                            if (valeur != ''):
                                valeur = valeur[val['data']]
                            # valeur = next((item for item in s[dicCol['field_panel_name']] if item.get(val['data'])), None)[val['data']]
                            # print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            # print('--------------------------------------------')
                            # print(dicCol)
                            # print('+++++++++++++++++++++++++++++++++++++++++++++++')
                            # # print(s[dicCol['field_panel_name']][i])
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
                    # print('field_panel_name not in dic')
                    # print(dicCol['data'])
                    # print(dicCol['title'])
                    # print(s[dicCol['data']])
                    record.update({dicCol['data']: s[dicCol['data']]})
                    record.update({'title': dicCol['title']})
            
            
            
            if 'details' in grid:
                
                detailContent = []
                # detailContent.append({"activated": True})
                if 'activated' in grid['details']:
                    record.update({"details": {"activated": True}})
                else:
                    record.update({"details": {"activated": False}})
            else:
                record.update({"details": {"activated": False}})
                # output.append(detailContent)
            
            # print(listValuesFieldPanel)
            output.append(record)
            # print("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
            # print(record)
            # print(grid)
            # print(grid['filtered'][0]['by'])
        
        # p rint(output)

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
    output = []
    try:
        for grid in gridList:
            print(grid['name'])
            if "type" in grid:
                output.append({  "name": grid['name'], "listBtn": grid['list'], "display": True })
            else: 
                output.append({"name": grid['name'], "display": True})

    except StopAsyncIteration:
        print("Empty cursor")

    return jsonify(output) 


############### 
#  SEND EMAIL #
###############
@app.route('/send_mail', methods=['POST'])
def send_email():
    mail.init_app(app)

    data = request.get_json(force=True)

    mailId = data['mail_id']
    formId = data['form_id']
    appName = data['app_name']

    mailCollection = mongo.db.mails
    mailInfo = mailCollection.find_one({"mail_id": int(mailId)})


    if appName == 'play':
        app.config['MAIL_SERVER']='smtp.live.com'
        app.config['MAIL_PORT'] = 25
        app.config['MAIL_USERNAME'] = 'bde.play.2018@hotmail.com'
        app.config['MAIL_PASSWORD'] = 'bdeplay2018'
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USE_SSL'] = False
        
        dataCollection = mongo.db.play
        formData = dataCollection.find_one({"_id":ObjectId(formId)})
        
        profile  = formData['profile']
        nom      = profile[0]['nom']
        prenom    = profile[1]['firstname']
        email    = profile[3]['email']
        sender   = mailInfo['sender']

        # PREPARE CONFIRMATION MSG
        html = "Afin de valider votre inscription, merci de bien vouloir payer la somme de 140€ sur le compte suivant: <br><br><table><tr><td>TITULAIRE DU COMPTE: </td><td> Bureau des élèves-ISEB</td></tr><tr><td>IBAN: </td><td>  FR76 1558 9297 1803 0818 3454 079</td></tr><tr><td>COMMUNICATION: </td><td> Bde play "+nom +" "+ prenom + " </td></tr></table>"          
        
        msg = Message( mailInfo['subject'],
        sender=('BDE PLAY', sender),
        html=html,
        recipients=[email])       

    else:
        app.config['MAIL_SERVER']='smtp.1and1.es'
        app.config['MAIL_PORT'] = 587
        app.config['MAIL_USERNAME'] = 'info@russianmastersballet.com'
        app.config['MAIL_PASSWORD'] = 'Rmbc2015'
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USE_SSL'] = False
        
        dataCollection = mongo.db.ballet
        formData = dataCollection.find_one({"_id":ObjectId(formId)})
        # GET INFO TO PUT IN TEMPLATE
        profile  = formData['profile']
        prenom   = profile[0]['firstname']
        email    = profile[3]['email']

        # html = "Dear "+ prenom + ",<br><br> We have received your registration form and will contact you in a short time. <br><br> Yours sincerely,<br><br>Yulia Mahilinskaya <br>Mobile: + 34 609816395<br> Skype: russianmastersballet<br> <img src='http://res.cloudinary.com/hk5fms7st/image/upload/v1507205982/E05815277543397E4D847EA6EE17412C33E7A8D4753B01084D_pimgpsh_fullsize_distr_frivwn.png'>"
        html = "Dear "+ prenom + ",<br><br> We have received your registration form and will contact you in a short time. <br><br> Yours sincerely,<br><br>Yulia Mahilinskaya <br>Mobile: + 34 609816395<br> Skype: russianmastersballet<br>"
        sender   = mailInfo['sender']

        msg = Message( mailInfo['subject'],
        sender=sender,
        html=html,
        recipients=[email])
   
    
    try:
        


        mail.send(msg)

    except StopAsyncIteration:
        print("Empty cursor")

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
    jsonGroups = {}
    jsonGroupsArray= []
    wk1List  = list(week1)
    print(wk1List)
    wk2List  = list(week2)
    print(wk2List)
    print(len(wk1List))
    print(len(wk2List))
    
    # if len(wk1List) == 0:
    try:
        for group in groups:
            # jsonGroups = { "group" : group, "lst": [{"week": "1", "people": 0 }, {"week": "2", "people": 0 },{"week": "3", "people": 0 }] }
            jsonGroups = { "group" : group, "lst": []}
            jsonGroupsArray.append(jsonGroups)
    except StopAsyncIteration:
        print("Empty cursor")
    # else:
    # try:
    #     # for wk1 in wk1List:
    #     #     jsonGroups = { "group" : wk1['_id']['group'], "lst": [{"week": wk1['_id']["week"], "people": wk1['count'] }] }
    #     #     jsonGroupsArray.append(jsonGroups)
    # except StopAsyncIteration:
    #     print("Empty cursor")


    # if len(wk2List) == 0:
    # try:
    #     for group in groups:
    #         jsonGroups = { "group" : group, "lst": [{"week": "2", "people": 0 }] }
    #         jsonGroupsArray.append(jsonGroups)
    #         # jsonGroups = { "group" : group, "lst": [{"week": "3", "people": 0 }] }
    #         # jsonGroupsArray.append(jsonGroups)
    # except StopAsyncIteration:
    #     print("Empty cursor")
    # else:
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



@app.route('/auth_signin', methods=['POST'])
@cross_origin()
def signin():
    credentials = request.get_json()
    # Add creation date 
    # user.update({ "date_creation" : datetime.now()})
    # output = {}
    print(credentials)
    user = mongo.db.users.find_one({"email": credentials['email']})
    print(user)
    # print(user['password'])
    if (user != None):
        if (pbkdf2_sha256.verify(credentials['password'], user['password'])):
            encoded = jwt.encode({'user': user['email']}, 'secret', algorithm='HS256')
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
    
    # print(formValues)
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
                'notes': formValues['notes']
            }
        }, upsert=False)
    return str(new_id)

@app.route('/export_excel', methods=['POST'])
@cross_origin()
def exportExcel():
    formValues = request.get_json()
    print(formValues)
    print('export')
    return 'ok'
    # return excel.make_response_from_array([[1,2], [3, 4]], "csv")
#     # si = StringIO()
#     # cw = csv.writer(si)
#     # csvList = []
#     # csvList.append(['all','my','data','goes','here'])
#     # cw.writerows(csvList)
    
#     # elf.send_header("Access-Control-Expose-Headers", "Access-Control-Allow-Origin")
#     # self.send_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")


#     data = StringIO()
#     w = csv.writer()  writer(data)

#     w.writerow((
#             "xxx",
#             "zzz"  # format datetime as string
#         ))

#     # write each log item
#     # for item in log:
#     #     w.writerow((
#     #         item[0],
#     #         item[1].isoformat()  # format datetime as string
#     #     ))
#     #     yield data.getvalue()
#     #     data.seek(0)
#     #     data.truncate(0)


    
#     # output.headers["Access-Control-Allow-Origin"]
#     headers = Headers()
#     headers.set('Content-Disposition', 'attachment', filename='log.csv')
#     # output.headers["Content-Disposition"] = "attachment, filename=sample.csv"
#     # output.headers["Content-type"] = "text/csv"

#     return Response(
#         w,mimetype='text/csv', headers=headers
#     )


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