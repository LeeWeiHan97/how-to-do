from models.base_model import BaseModel
import peewee as pw
from models.user import User
from models.room import Room
import datetime

class Scheduled(BaseModel):
    name = pw.CharField(unique=False, null=False) 
    date_time = pw.DateTimeField(null=False, unique=False)
    user_incharge = pw.ForeignKeyField(User, backref="user_scheduled_tasks", null=True, on_delete="CASCADE")
    room = pw.ForeignKeyField(Room, backref="room_scheduled_tasks", null=False, on_delete="CASCADE")
    repeat_by = pw.CharField(unique=False, null=False)
    repeat_on = pw.CharField(unique=False, null=False)
    
    def validate(self):
        if len(self.name) == 0:
            self.errors.append('Task is empty')
        if len(self.repeat_by) == 0:
            self.errors.append('Repeat by is empty')
        if len(self.repeat_on) == 0:
            self.errors.append('Repeat on is empty')

        datetime_string = self.date_time
        datetime_format = '%Y-%m-%d %H:%M:%S'

        try:
            date_obj = datetime.datetime.strptime(datetime_string, datetime_format)
        except ValueError:
            self.errors.append('Wrong format for datetime input')
