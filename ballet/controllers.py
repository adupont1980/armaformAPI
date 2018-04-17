from flask import Blueprint


group = Blueprint('group', __name__)



##################################
# SET GROUP TO USER 
###################################
@group.route('/set_group_to_user', methods=['POST'])
@cross_origin()
def index():
    data = request.get_json(force=True)
    idRecord = data['_id']
    newVal = data['groupName']
    new_id = mongo.db.ballet.update({'_id':  ObjectId(idRecord)}, { '$set':{'group': newVal}}, upsert=False)
    print(new_id)
    print(idRecord)

    # return jsonify({"Changed": True, "new_id": new_id})
    return json.dumps({'message': 'Group updated'}, default=json_util.default)
