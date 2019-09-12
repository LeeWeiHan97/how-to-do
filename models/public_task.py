from models.base_model import BaseModel
import peewee as pw
from models.user import User
import datetime
from models.room import Room

class PublicTask(BaseModel):
    name = pw.CharField(unique=False, null=False)
    description = pw.CharField(unique=False, null=True)
    completed_by = pw.DateTimeField(null=False, unique=False)
    is_completed = pw.BooleanField(default=False)
    created_by = pw.ForeignKeyField(User, backref="user_created_public_tasks", null=False)
    user_incharge = pw.ForeignKeyField(User, backref="user_taking_on_public_tasks", null=True, on_delete="SET NULL")
    room = pw.ForeignKeyField(Room, backref="room_public_tasks", null=False)

    def validate(self):
        public_task = PublicTask.get_or_none(PublicTask.id == self.id)

        if len(self.name) == 0:
            self.errors.append('Task is empty')

        datetime_string = self.completed_by
        datetime_format = '%Y-%m-%d %H:%M:%S'
        try:
            date_obj = datetime.datetime.strptime(datetime_string, datetime_format)
        except ValueError:
            self.errors.append('Wrong format for datetime input')