#from crypt import methods
import os
from turtle import title
from flask import Flask, redirect, render_template, session, url_for, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from functools import wraps
from jose import jwt
from dotenv import find_dotenv, load_dotenv
from urllib.request import urlopen
from authlib.integrations.flask_client import OAuth
from .database.models import db_drop_and_create_all, setup_db, Drink
from passlib.hash import md5_crypt as md5
from passlib.hash import sha256_crypt as sha256
from passlib.hash import sha512_crypt as sha512
import random


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
setup_db(app)
#CORS(app)
cor= CORS(app, resources={r'/*': {"origins": '*'}}, support_credentials=True)
#OAuth(app)
 
AUTH0_DOMAIN ='dev-augly9fv.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'drinks'
def after_request(response):
        header = response.headers
        header['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        header['Access-Control-Allow-Methods'] = 'OPTIONS, HEAD, GET, POST, DELETE, PUT,PATCH'
        return response


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    parts = auth.split()
    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)

    elif len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    elif len(parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    token = parts[1]
    return token


def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)

def check_permission(permission, payload):
    if "permissions" not in payload:
        abort(400)
    if permission not in payload['permissions']:
        abort(403)
    return True
def requires_auth(permission=""):

    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except:
                abort(401)
            
            check_permission(permission,payload)
            return f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator

@app.route('/headers/')
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

        print(lst)
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
        #print(str(req_recipe))
        
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
        #print(drink)
        #long_recipe = [{"name": r["name"],"color": r["color"], "parts": r["parts"]} for r in json.loads(req_recipe)]
        """
        """
        #drink = Drink.query.filter(Drink.id == rid).one_or_none()
 
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
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404 

'''

'''
@TODO implement error handler for 404
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
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422