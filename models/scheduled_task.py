from models.base_model import BaseModel
import peewee as pw
from models.user import User
from models.room import Room

class Scheduled(BaseModel):
    name = pw.CharField(unique=False, null=False) 
    is_completed = pw.BooleanField(default=False)
    datetime = pw.DateTimeField(null=False, unique=False)
    user_incharge = pw.ForeignKeyField(User, backref="user_scheduled_tasks")
    room = pw.ForeignKeyField(Room, backref="room_scheduled_tasks")
    