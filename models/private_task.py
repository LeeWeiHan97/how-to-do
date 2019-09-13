from models.base_model import BaseModel
import peewee as pw
from models.user import User
import datetime

class PrivateTask(BaseModel):
    user = pw.ForeignKeyField(User, backref='user_tasks', on_delete="CASCADE")
    description = pw.CharField(null=True, unique=False)
    name = pw.CharField(null=False, unique=False)
    completed_by = pw.DateTimeField(null=False, unique=False)
    is_completed = pw.BooleanField(default=False)

    def validate(self):
        if len(self.name) == 0:
            self.errors.append('Task is empty')
        
        datetime_string = self.completed_by
        datetime_format = '%Y-%m-%d %H:%M:%S'
        try:
            date_obj = datetime.datetime.strptime(datetime_string, datetime_format)
        except ValueError:
            self.errors.append('Wrong format for datetime input')
