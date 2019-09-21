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
from models.scheduled_task import Scheduled
from pyfcm import FCMNotification
import os
from datetime import datetime, timedelta, date, time
import calendar
import json, requests


users_api_blueprint = Blueprint('users_api',
                             __name__,
                             template_folder='templates')

push_service = FCMNotification(api_key=os.environ.get("FCM_API_KEY"))

def notification(registrationId, title, body):
    registration_id = registrationId
    message_title = title
    message_body = body
    if type(registrationId) == str:
        result = push_service.notify_single_device(registration_id=registration_id, message_title=message_title, message_body=message_body)
    elif type(registrationId) == list:
        result = push_service.notify_multiple_devices(registration_ids=registration_id, message_title=message_title, message_body=message_body)
    else:
        raise Exception('registration id should be a string or a list of strings')


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    hour = sourcedate.hour
    minute = sourcedate.minute
    second = sourcedate.second
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime(year, month, day, hour, minute, second)


@users_api_blueprint.route('/signup', methods=['POST'])
def create():
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')
    confirmed_password = request.json.get('confirmed_password')
    android_token = request.json.get('android_token')
    if password == confirmed_password:
        user_create = User(username=username, email=email, password=password, android_token=android_token)
        if user_create.save():
            response = {
                "status": "success",
                "user_id": str(user_create.id),
                "username": user_create.username,
                "email": user_create.email
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
            "errors": "password and confirmed password not the same"
        }
        return jsonify (response)


@users_api_blueprint.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    users = User.select()
    for user in users:
        if username == user.username and password == user.password:
            expires = timedelta(days=365)
            jwt_token = create_access_token(identity=user.id, expires_delta=expires)
            android_token = request.json.get('android_token')
            user.android_token = android_token
            if user.save():
                response = {
                    "status": "success",
                    "user_id": str(user.id),
                    "jwt_token": jwt_token,
                    "username": user.username,
                    "email": user.email,
                    "room id": str(user.room_id)
                }
            else:
                response = {
                    "status": "failed",
                    "errors": ", ".join(user.errors)
                }

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
        "users": [user.id for user in users],
        "usernames": [user.username for user in users],
        "emails": [user.email for user in users]
    }

    return jsonify (response)


@users_api_blueprint.route('/housemates/<room_id>', methods=['GET'])
def housemates(room_id):
    roomID = room_id
    users = User.select().where(User.room_id == roomID)
    response = {
        "status": "success",
        "users": [
            {
            "id": str(user.id),
            "name": user.username,
            "is admin": user.is_admin
        } for user in users
        ],
    }

    return jsonify (response)


@users_api_blueprint.route('/me', methods=['GET'])
@jwt_required
def me():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    response = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "room id": str(user.room_id),
            "is_admin": user.is_admin
        }
    
    return jsonify (response)


@users_api_blueprint.route('/get/private_task', methods=['GET'])
@jwt_required
def get_private_task():
    current_user_id = get_jwt_identity()
    private_tasks = PrivateTask.select().where(PrivateTask.user_id == current_user_id)
    response = [
        {
        "id": str(private_task.id),
        "created at": private_task.created_at,
        "task": private_task.description,
        "is completed": private_task.is_completed
        } for private_task in private_tasks
    ]

    return jsonify (response)


@users_api_blueprint.route('/get/public_category/<room_id>', methods=['GET'])
@jwt_required
def get_public_category(room_id):
    roomID = room_id
    room = Room.get_or_none(Room.id == roomID)
    public_categories = PublicCategory.select().where(PublicCategory.room_id == roomID)
    if room:
        response = [
            {
            "id": str(public_category.id),
            "created at": public_category.created_at,
            "category": public_category.task,
            "completed by": public_category.completed_by,
            "is completed": public_category.is_completed,
            "created by": str(public_category.created_by_id)
            } for public_category in public_categories
        ]

    else:
        response = {
            "status": "failed",
            "error": "room does not exist!"
        }

    return jsonify (response)


@users_api_blueprint.route('/get/public_task/<public_category_id>', methods=['GET'])
@jwt_required
def get_public_task(public_category_id):
    public_categoryID = public_category_id
    public_category = PublicCategory.get_or_none(PublicCategory.id == public_categoryID)
    tasks = Task.select().where(Task.public_category_id == public_categoryID)
    if public_category:
        response = [
            {
                "id": str(task.id),
                "created at": task.created_at,
                "task": task.name,
                "created by": str(task.created_by_id),
                "is completed": task.is_completed
            } for task in tasks
        ]
    
    else:
        response = {
            "status": "failed",
            "error": "public category does not exist"
        }

    return jsonify (response)


@users_api_blueprint.route('get/scheduled/all', methods=['GET'])
@jwt_required
def get_all_scheduled():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    room = Room.get_or_none(Room.id == user.room_id)
    if room:
        tasks = Scheduled.select().where(Scheduled.room_id == room.id).prefetch(Room)
        if len(tasks) == 0:
            response = {
                "status": "failed",
                "error": "no such scheduled task at specified time and day!"
            }
        else:
            response = [
                {
                    "task_id": str(task.id),
                    "task": task.name,
                    "user_id_incharge": task.user_incharge_id,
                    "created_at": task.created_at,
                    "date": task.date_time.strftime('%Y-%m-%d'),
                    "time": task.date_time.strftime('%H:%M:%S'),
                    "repeat_by": task.repeat_by,
                    "repeat_on": task.repeat_on
                } for task in tasks
            ]

        return jsonify (response)

    else:
        response = {
            "status": "failed",
            "error": "room does not exist!"
        }

@users_api_blueprint.route('get/scheduled/<roomID>/<repeat_by>/<day>', methods=['GET'])
@jwt_required
def get_scheduled(roomID, repeat_by, day):
    room = Room.get_or_none(Room.id == roomID)
    if room:
        tasks = Scheduled.select().where((Scheduled.repeat_by == repeat_by) & (Scheduled.repeat_on == day) &(Scheduled.room_id == room.id))
        if len(tasks) == 0:
            response = {
                "status": "failed",
                "error": "no such scheduled task at specified time and day!"
            }
        
        else:
            response = [
                {
                    "task_id": str(task.id),
                    "task": task.name,
                    "user_id_incharge": task.user_incharge_id,
                    "created_at": task.created_at,
                    "date": task.date_time.strftime('%Y-%m-%d'),
                    "time": task.date_time.strftime('%H:%M:%S'),
                    "repeat_by": task.repeat_by,
                    "repeat_on": task.repeat_on
                } for task in tasks
            ]
        
        return jsonify (response)
    
    else:
        response = {
            "status": "failed",
            "error": "room does not exist!"
        }

    return jsonify (response)


@users_api_blueprint.route('/<user_id>', methods=['GET'])
def user(user_id):
    user = User.get_or_none(User.id == user_id)

    if user:
        response = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
        }
    else:
        response = {
            "status": "failed",
            "error": "User not found"
        }
    
    return jsonify (response)


@users_api_blueprint.route('/edit', methods=['POST'])
@jwt_required
def edit():  
    username = request.json.get('username')
    email = request.json.get('email')
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    user.username = username
    user.email = email
    if user.save():
        response = {
            "status": "success",
            "new_username": username,
            "new_email": email,
        }
    
    else:
        response = {
            "status": "failed",
            "errors": ", ".join(user.errors)
        }

    return jsonify (response)


@users_api_blueprint.route('/join', methods=['POST'])
@jwt_required
def join():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    roomID = int(request.json.get('room_id'))
    rooms = Room.select()

    if user.room_id != roomID:
        for room in rooms:
            if roomID == room.id:
                users_in_room = User.select().where(User.room_id == roomID)
                registration_id = [user.android_token for user in users_in_room]
                title = f"{user.username} has joined your group!"
                body="Gang gang gang!"
                notification(registration_id, title, body)

                user.room_id = room.id
                user.save()

                response = {
                "status": "success",
                "room_id": str(room.id),
                "room_name": room.name
                }
                
                return jsonify (response)

        response = {
            "status": "failed",
            "error": "Room does not exist"
        }

        return jsonify (response)
    else:
        response = {
            "status": "failed",
            "error": "user already in the room!"
        }

        return jsonify (response)


@users_api_blueprint.route('/create', methods=['POST'])
@jwt_required
def new_room():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)

    if user.is_admin == False:
        room_create = Room(name=f"{user.username}'s room").save()
        room = Room.get_or_none(Room.name==f"{user.username}'s room")
        user.is_admin = True
        user.room_id = room.id

        if user.save():
            response = {
                "status": "success",
                "room_id": str(room.id),
                "room_name": room.name
            }
        else:
            response = {
                "status": "failed",
                "error": ", ".join(user.errors)
            }

        return jsonify (response)
        
    else:
        response = {
            "status": "failed",
            "error": "user has already created a room, please leave the room before creating a new one!"
        }

    return jsonify (response)


@users_api_blueprint.route('/deleteroom', methods=['POST'])
@jwt_required
def delete_room():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    roomId = int(request.json.get('room_id'))
    room = Room.get_or_none(Room.id == roomId)
    if room and user.room.id == roomId:
        if user.is_admin == True:
            user.is_admin = False
            user.save()
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
    description = request.json.get('description')
    private_task_create = PrivateTask(user_id=user.id, description=description)
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
    task_id = int(request.json.get('task_id'))
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
    task_id = int(request.json.get('task_id'))
    task = PrivateTask.get_by_id(task_id)
    if task.user_id == current_user_id:
        if task.is_completed == False:
            task.is_completed = True
            task.save()

        else:
            task.is_completed = False
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
    completed_by = request.json.get('completed_by')
    roomID = user.room_id
    public_category_create = PublicCategory(task=name, completed_by=completed_by, created_by_id=current_user_id, room_id= roomID)
    if public_category_create.save():
        users_in_room = User.select().where(User.room_id == roomID)
        registration_id = [user.android_token for user in users_in_room]
        title = f"{user.username} has added {name} to the group!"
        body = ""

        notification(registration_id, title, body)

        response = {
            "status": "success",
            "created_by_id": public_category_create.created_by_id,
            "room_id": public_category_create.room_id,
            "category": public_category_create.task
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
    task_id = int(request.json.get('task_id'))
    task = Task.get_by_id(task_id)
    if task.is_completed == True:
        task.is_completed = False
        task.save()
    else:
        task.is_completed = True
        task.save()

    task.save()
    response = {
        "status": "success"
    }

    return jsonify (response)


@users_api_blueprint.route('/deletepublictask', methods=['POST'])
@jwt_required
def delete_public_task():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    task_id = int(request.json.get('task_id'))
    task = Task.get_by_id(task_id)
    task_to_delete = Task.delete().where(Task.id == task_id).execute()
    response = {
        "status": "successfully deleted"
    }
    
    return jsonify (response)


@users_api_blueprint.route('/completepubliccategory', methods=['POST'])
@jwt_required
def complete_public_category():
    category_id = int(request.json.get('category_id'))
    category = PublicCategory.get_by_id(category_id)
    if category.is_completed == False:
        PublicCategory.update(is_completed = True).where(PublicCategory.id == category_id).execute()
    else:
        PublicCategory.update(is_completed = False).where(PublicCategory.id == category_id).execute()

    response = {
        "status": "success"
    }

    return jsonify (response)


@users_api_blueprint.route('/deletepubliccategory', methods=['POST'])
@jwt_required
def delete_public_category():
    category_id = int(request.json.get('category_id'))
    category = PublicCategory.get_or_none(PublicCategory.id == category_id)
    if category:
        category_to_delete = PublicCategory.delete().where(PublicCategory.id == category_id).execute()
        response = {
        "status": "successfully deleted"
        }

    else:
        response = {
            "status": "failed",
            "error": "Public category not found"
        }

    return jsonify (response)


@users_api_blueprint.route('/kick', methods=['POST'])
@jwt_required
def kick():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    kick_id = int(request.json.get('kicked_id'))
    if user.is_admin == True:
        user_to_remove = User.get_by_id(kick_id)
        user_to_remove.room_id = None
        registration_id = user_to_remove.android_token
        title = f"You have been kicked from your household group!"
        sad_messages = ["Sucks to be you!", "It really do be like that sometimes!", "Yikes!", "Oof, bummer!"]
        body= random.choice(sad_messages)
        notification(registration_id, title, body)
        if user_to_remove.save():
            response = {
                "status": "success"
            }
        else:
            response = {
                "status": "failed",
                "errors": ", ".join(user_to_remove.errors)
            }

        return jsonify (response)

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
    add_id = int(request.json.get('add_id'))
    current_room_id = user.room_id
    if user.is_admin == True:
        user_to_add = User.get_by_id(add_id)
        if user_to_add.room_id == None:
            user_to_add.room_id = current_room_id
            if user_to_add.save():
                users_in_room = User.select().where(User.room_id == current_room_id)
                registration_id = user_to_add.android_token
                title = f"{user.username} has added you to their household group!"
                body="(ᗒᗨᗕ)"
                notification(registration_id, title, body)

                response = {
                    "status": "success",
                    "users in room": users_in_room
                }
            
            else:
                response = {
                    "status": "failed",
                    "errors": ", ".join(user_to_add.errors)
                }

            return jsonify (response)
        
        else:
            response = {
                "status": "failed",
                "error": "user already in another room, please ask the user to exit their room first"
            }

        return jsonify (response)

    else:
          response = {
            "status": "failed",
            "error": "You are not the admin!"
        }

    return jsonify (response)  


@users_api_blueprint.route('/new_scheduled', methods=['POST'])
@jwt_required
def new_scheduled():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    name = request.json.get('task')
    date_time = datetime.strptime(request.json['date_time'], '%Y-%m-%d %H:%M:%S')
    repeat_by = request.json.get('repeat_by')
    repeat_on = request.json.get('repeat_on')
    repeat_for = int(request.json.get('repeat_for'))
    roomID = user.room_id

    if repeat_by == "weekly":
        data_source = []
        i = 0
        while i < repeat_for:
            add_data = {"name": name, "date_time": date_time, "room_id": roomID, "repeat_by": repeat_by, "repeat_on": repeat_on}
            data_source.append(add_data)
            date_time += timedelta(days = 7)
            i = i + 1

        Scheduled.insert_many(data_source).execute()

        tasks = Scheduled.select().where((Scheduled.repeat_by == repeat_by) & (Scheduled.repeat_on == repeat_on) &(Scheduled.room_id == roomID))

    elif repeat_by == "monthly":
        data_source = []
        i = 0
        while i < repeat_for:
            add_data = {"name": name, "date_time": date_time, "room_id": roomID, "repeat_by": repeat_by, "repeat_on": repeat_on}
            data_source.append(add_data)
            date_time = add_months(date_time,1)
            i = i + 1

        Scheduled.insert_many(data_source).execute()

        tasks = Scheduled.select().where((Scheduled.repeat_by == repeat_by) & (Scheduled.repeat_on == repeat_on) &(Scheduled.room_id == roomID))

    else:
        response = {
            "status": "failed",
            "error": "repeat_by can only be 'weekly' or 'monthly', please check spelling!"
        }

        return jsonify (response)
    
    response = [
        {
            "task_id": str(task.id),
            "task": task.name,
            "user_id_incharge": task.user_incharge_id,
            "created_at": task.created_at,
            "date": task.date_time.strftime('%Y-%m-%d'),
            "time": task.date_time.strftime('%H:%M:%S'),
            "repeat_by": task.repeat_by
        } for task in tasks
    ]
    return jsonify (response)

@users_api_blueprint.route('/deletescheduledtask', methods=['POST'])
@jwt_required
def delete_scheduled_task():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    task_id = int(request.json.get('task_id'))
    task = Scheduled.get_by_id(task_id)
    if task.room_id == user.room_id:
        task_to_delete = Scheduled.delete().where(Scheduled.id == task_id).execute()
        response = {
            "status": "successfully deleted"
        }
    else:
        response = {
            "status": "failed",
            "error": "Do not try to delete other's personnal tasks!"
        }

    return jsonify (response)


@users_api_blueprint.route('/notification', methods=['POST'])
def notifications():
    notification("cD0tlSBK1OQ:APA91bGDbKWOa8nlwjZcsf4ATA8e3iWBB7bda5HOGhU6pqlqgGGmb9-DA00gNNV8TzIRQrFbrnSATsqFN4xpQa2dzTTp5IqQ02BpitqJTbbHW6WESEpm45xJobDhJ_Girw0Z7a_PAo_8", "test title", "test body")
    response = {
        "status": "success"
    }

    return jsonify (response)


@users_api_blueprint.route('/geolocation', methods=['POST'])
@jwt_required
def geolocation():
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    public_categories = PublicCategory.select()
    
    for category in public_categories:
        if category.task == "Grocery":
            url = 'https://api.foursquare.com/v2/venues/search'

            params = dict(
            client_id=os.environ.get('FOURSQUARE_CLIENT_ID'),
            client_secret=os.environ.get('FOURSQUARE_CLIENT_SECRET'),
            v='20180323',
            ll=f'{latitude},{longitude}',
            query='grocery',
            limit=5,
            radius=200
            )
            resp = requests.get(url=url, params=params)
            data = json.loads(resp.text)

            if len(data) > 0:
                registration_id = user.android_token
                title = f"There's a grocery shop nearby! Do your work!"
                body="(ᗒᗨᗕ)"
                notification(registration_id, title, body)

            return jsonify (data)
            # change the data returned accordingly using postman!
        
    response = {
        "status": "no public category with task grocery found"
    }

    return jsonify (response)


@users_api_blueprint.route('/assign', methods=['POST'])
@jwt_required
def assign():
    user_incharge_id = int(request.json.get('user_incharge_id'))
    task_id = int(request.json.get('task_id'))
    task = Scheduled.get_or_none(Scheduled.id == task_id)

    if task:
        task.user_incharge_id = user_incharge_id
        if task.save():
            response = {
                "status": "success",
                "task_id": str(task.id),
                "updated_at": task.updated_at,
                "user_incharge_id": str(task.user_incharge_id)
            }

        else:
            response = {
                "status": "failed",
                "errors": ", ".join(task.errors)
            }

        return jsonify (response)
    
    else:
        response = {
            "status": "failed",
            "error": "task with task_id given not found"
        }

    return jsonify (response)

