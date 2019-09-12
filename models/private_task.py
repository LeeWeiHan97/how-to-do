from models.base_model import BaseModel
import peewee as pw
from models.user import User

class PrivateTask(BaseModel):
    user = pw.ForeignKeyField(User, backref='user_tasks')
    description = pw.CharField(null=True, unique=False)
    name = pw.CharField(null=False, unique=False)
    completed_by = pw.DateTimeField(null=False, unique=False)
    is_completed = pw.BooleanField(default=False)