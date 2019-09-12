from app import app
from flask import jsonify, request, Blueprint
from flask_jwt_extended import (jwt_required, create_access_token, get_jwt_identity)
from models.user import User
from models.room import Room
import string
import random

users_api_blueprint = Blueprint('users_api',
                             __name__,
                             template_folder='templates')


@users_api_blueprint.route('/signup', methods=['POST'])
def create():
    name = request.json.get('name')
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')
    confirmed_password = request.json.get('confirmed_password')
    if password == confirmed_password:
        user_create = User(name=name, username=username, email=email, password=password)
        if user_create.save():
            response = {
                "status": "success",
            }, 200
        else:
            response = {
                "status": "failed",
                "errors": ', '.join(user_create.errors)
            }, 400
        return jsonify (response)
    else:
        response = {
            "status": "failed",
            "errors": ', '.join(user_create.errors)
        }, 400
        return jsonify (response)


@users_api_blueprint.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    users = User.select()
    for user in users:
        if username == user.username and password == user.password:
            jwt_token = create_access_token(identity=user.id)
            response = {
                "status": "success",
                "user_id": user.id,
                "jwt_token": jwt_token
            }, 200
        else:
            response = {
                "status": "failed",
                "error": "Username or password incorrect"
            }, 400
        return jsonify (response)
    response = {
        "status": "failed",
        "error": "User does not exist"
    }
    return (response)


@users_api_blueprint.route('/', methods=['GET'])
def users():
    users = User.select()
    response = {
        "status": "success",
        "users": [user.id for user in users]
    }, 200

    return jsonify (response)


@users_api_blueprint.route('/<user_id>', methods=['GET'])
def user(user_id):
    user = User.get_or_none(User.id == user_id)

    if user:
        response = {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "email": user.email,
        }, 200
    else:
        response = {
            "status": "failed",
            "error": "User not found"
        }, 400
    
    return jsonify (response)


@users_api_blueprint.route('/me', methods=['GET'])
@jwt_required
def me():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    response = {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "email": user.email,
        }, 200
    
    return jsonify (response)


@users_api_blueprint.route('/join', methods=['POST'])
@jwt_required
def join():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    room_id = request.json.get('room_id')
    rooms = Room.select()
    for room in rooms:
        if room_id == room.name:
            User.update(room_id=room_id).where(User.id == user.id).execute()
            response = {
                "status": "success"
            }, 200
            return jsonify (response)

    response = {
        "status": "failed",
        "error": "Room does not exist"
    }

    return jsonify (response)


@users_api_blueprint.route('/create', methods=['POST'])
@jwt_required
def new_room():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    room_create = Room(name=f"{user.username}'s room").save()
    room = Room.get_or_none(Room.name==f"{user.username}'s room")
    user.is_admin = True
    user.room_id = room.id
    user.save()

    response = {
        "status": "success",
        "room_id": room.id,
        "room_name": room.name
    }

    return jsonify (response)

        
        
        

