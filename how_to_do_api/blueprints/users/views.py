from app import app
from flask import jsonify, request, Blueprint
from flask_jwt_extended import (jwt_required, create_access_token, get_jwt_identity)
from models.user import User
from models.room import Room
import string
import random
from models.private_task import PrivateTask
from models.public_category import PublicCategory
from models.task import Task


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
            }
        else:
            response = {
                "status": "failed",
                "errors": ', '.join(user_create.errors)
            }
        return jsonify (response)
    else:
        response = {
            "status": "failed",
            "errors": ', '.join(user_create.errors)
        }
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

            return jsonify (response)

    response = {
        "status": "failed",
        "error": "Username or password incorrect"
    }
    return jsonify (response)



@users_api_blueprint.route('/', methods=['GET'])
def users():
    users = User.select()
    response = {
        "status": "success",
        "users": [user.id for user in users]
    }

    return jsonify (response)


@users_api_blueprint.route('/housemates', methods=['GET'])
def housemates():
    roomID = request.json.get('room_id')
    users = User.select().where(User.room_id == roomID)
    response = {
        "status": "success",
        "users": [user.id for user in users],
    }

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
        }
    
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
        }
    else:
        response = {
            "status": "failed",
            "error": "User not found"
        }
    
    return jsonify (response)


@users_api_blueprint.route('/join', methods=['POST'])
@jwt_required
def join():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    roomID = request.json.get('room_id')
    rooms = Room.select()
    for room in rooms:
        if roomID == room.id:
            user.room_id = room.id
            user.save()
            response = {
                "status": "success"
            }
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


@users_api_blueprint.route('/deleteroom', methods=['POST'])
@jwt_required
def delete_room():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    roomId = request.json.get('room_id')
    room = Room.get_or_none(Room.id == roomId)
    if room and user.room.id == roomId:
        if user.is_admin == True:
            room_to_delete = Room.delete().where(Room.id == roomId).execute()
            response = {
                "status": "success"
            }
        else:
            response = {
                "status": "failed",
                "error": "You are not the admin!"
            }
        
        return jsonify (response)
    else:
        response = {
            "status": "failed",
            "error": "Either room id mismatch or room does not exist!"
        }

        return jsonify (response)


@users_api_blueprint.route('/newprivatetask', methods=['POST'])
@jwt_required
def new_private_task():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    name = request.json.get('name')
    description = request.json.get('description')
    completed_by = request.json.get('completed_by')
    private_task_create = PrivateTask(user_id=user.id, name=name, description=description, completed_by=completed_by)
    if private_task_create.save():
        response = {
            "status": "success"
        }
    else:
        response = {
            "status": "failed",
            "errors": ', '.join(private_task_create.errors)
        }

    return jsonify (response)
    

@users_api_blueprint.route('/deleteprivatetask', methods=['POST'])
@jwt_required
def delete_private_task():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    task_id = request.json.get('task_id')
    task = PrivateTask.get_by_id(task_id)
    if task.user_id == current_user_id:
        task_to_delete = PrivateTask.delete().where(PrivateTask.id == task_id).execute()
        response = {
            "status": "successfully deleted"
        }
    else:
        response = {
            "status": "failed",
            "error": "Do not try to delete other's personnal tasks!"
        }

    return jsonify (response)


@users_api_blueprint.route('/completeprivatetask', methods=['POST'])
@jwt_required
def complete_private_task():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    task_id = request.json.get('task_id')
    task = PrivateTask.get_by_id(task_id)
    if task.user_id == current_user_id:
        task.is_completed = True
        task.save()
        response = {
            "status": "success"
        }
    else:
        response = {
            "status": "failed",
            "error": "Do not try to edit other's personnal tasks!"
        }

    return jsonify (response)


@users_api_blueprint.route('/newpubliccategory', methods=['POST'])
@jwt_required
def new_public_category():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    name = request.json.get('category')
    description = request.json.get('description')
    completed_by = request.json.get('completed_by')
    roomID = user.room_id
    public_category_create = PublicCategory(name=name, description=description, completed_by=completed_by, created_by_id=current_user_id, room_id= roomID)
    if public_category_create.save():
        response = {
            "status": "success"
        }
    else:
        response = {
            "status": "failed",
            "errors": ', '.join(public_category_create.errors)
        }
    
    return jsonify (response)


@users_api_blueprint.route('/newpublictask', methods=['POST'])
@jwt_required
def new_public_task():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    name = request.json.get('task')
    category_id = request.json.get('category_id')
    public_task_create = Task(name=name, created_by=current_user_id, public_category=category_id)
    if public_task_create.save():
        response = {
            "status": "success"
        }
    else:
        response = {
            "status": "failed",
            "errors": ', '.join(public_category_create.errors)
        }
    
    return jsonify (response)


@users_api_blueprint.route('/completepublictask', methods=['POST'])
@jwt_required
def complete_public_task():
    task_id = request.json.get('task_id')
    task = Task.get_by_id(task_id)
    task.is_completed = True
    task.save()
    response = {
        "status": "success"
    }

    return jsonify (response)


@users_api_blueprint.route('/completepubliccategory', methods=['POST'])
@jwt_required
def complete_public_category():
    category_id = request.json.get('category_id')
    PublicCategory.update(is_completed = True).where(PublicCategory.id == category_id).execute()
    response = {
        "status": "success"
    }

    return jsonify (response)


@users_api_blueprint.route('/kick', methods=['POST'])
@jwt_required
def kick():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    kick_id = request.json.get('kicked_id')
    if user.is_admin == True:
        user_to_remove = User.get_by_id(kick_id)
        user_to_remove.room_id = None
        user_to_remove.save()
        response = {
            "status": "success"
        }
    else:
        response = {
            "status": "failed",
            "error": "You are not the admin!"
        }

    return jsonify (response)


@users_api_blueprint.route('/add', methods=['POST'])
@jwt_required
def add():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    add_id = request.json.get('add_id')
    current_room_id = user.room_id
    if user.is_admin == True:
        user_to_add = User.get_by_id(add_id)
        user_to_add.room_id = current_room_id
        user_to_add.save()
        response = {
            "status": "success"
        }
    else:
          response = {
            "status": "failed",
            "error": "You are not the admin!"
        }

    return jsonify (response)  


# @users_api_blueprint.route('/new_scheduled', methods=['POST'])
# @jwt_required
# def new_scheduled():
