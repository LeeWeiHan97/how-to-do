from models.base_model import BaseModel
import peewee as pw
from models.user import User
from models.public_task import PublicTask

class UserPublicTask(BaseModel):
    user = pw.ForeignKeyField(User, backref='user_userpublictasks')
    public_task = pw.ForeignKeyField(PublicTask, backref='publictask_userpublictasks')