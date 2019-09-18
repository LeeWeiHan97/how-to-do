from models.base_model import BaseModel
import peewee as pw
from models.user import User
import datetime

class PrivateTask(BaseModel):
    user = pw.ForeignKeyField(User, backref='user_tasks', on_delete="CASCADE")
    description = pw.CharField(null=False, unique=False)
    is_completed = pw.BooleanField(default=False)

    def validate(self):
        if len(self.description) == 0:
            self.errors.append('Task is empty')
        

