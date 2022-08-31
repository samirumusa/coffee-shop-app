#from crypt import methods
import os
from turtle import title
from flask import Flask, redirect, render_template, session, url_for, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from functools import wraps
from dotenv import find_dotenv, load_dotenv
from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import requires_auth, get_token_auth_header, check_permission, verify_decode_jwt
import random
from passlib.hash import md5_crypt as md5
from passlib.hash import sha256_crypt as sha256
from passlib.hash import sha512_crypt as sha512
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
setup_db(app)


cor= CORS(app, resources={r'/*': {"origins": '*'}}, support_credentials=True)

 
def after_request(response):
        header = response.headers
        header['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        header['Access-Control-Allow-Methods'] = 'OPTIONS, HEAD, GET, POST, DELETE, PUT,PATCH'
        return response


@app.route('/headers')
@requires_auth("get:drink")
def headers(jwt):
    print(jwt)
    return 'Access Granted'

'''
@DONE uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
#db_drop_and_create_all()

# ROUTES
'''
@DONE implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
@requires_auth("get:drinks")
def get_drinks(jwt):
    try:
        my = Drink.query.all()
        
        return jsonify({
            "success":True,
            "drinks":Drink.short(my[0])
        })
    except:
        abort(404)

'''
@DONE implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail')
@requires_auth("get:drinks-detail")
def detail_drinks(jwt):
    try:
        my = Drink.query.all()
        lst=[]
        for i in range(len(my)):
            #print(my[i].recipe)
            res = Drink.short(my[i])
            #print(res)
            lst.append(res)

        #print(lst)
        return jsonify({
            "success":True,
            "drinks":lst
        })
    except:
        abort(404)

'''
@DONE implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drink', methods=['POST'])
@requires_auth("post:drinks")
def add_drinks(jwt):
    try:
        content = request.get_json()
        req_recipe = content.get('recipe', None)
        req_title = content.get('title', None)
        idi = random.randint(0,999)
        drink = Drink(
                      title=req_title, 
                      recipe=json.dumps(req_recipe))
        drink.insert()

        return jsonify([{
            "success":True,
            "drinks":{
                'id':idi,
                'title':req_title,
                'recipe':req_recipe
            }
        }])
    except:
        abort(422)
    
'''
@DONE implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/update_drinks/<int:id>', methods=['PATCH'])
@requires_auth("patch:drinks")
def update_drinks(jwt,id):
   
        content = request.get_json()
        rid = content.get('id', None)
        req_recipe = str(content.get('recipe', None))
        req_title = content.get('title', None)
        drink = Drink.query.filter(Drink.id == rid).one_or_none()
        drink.title = req_title
        drink.recipe= req_recipe
        drink.update()
        return jsonify({
           'success':True,
            'id': drink.id,
            'title': drink.title,
            'drinks':[req_recipe]
        })
'''
@DONE implement endpoint
    DELETE /drinks/<id>
    
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth("delete:drinks")
def delete_drink(jwt,id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        drink.delete()
        return jsonify({
           'success':True,
            'delete':id,
        })
    except:
        abort(422)
# Error Handling
'''
@DONE implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404 

'''

'''
@DONE implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404

'''
@DONE implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422