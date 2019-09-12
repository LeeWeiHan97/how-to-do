from models.base_model import BaseModel
import peewee as pw
from models.public_category import PublicCategory
from models.user import User

class Task(BaseModel):
    name = pw.CharField(unique=False, null=False) 
    is_completed = pw.BooleanField(default=False)
    public_category = pw.ForeignKeyField(PublicCategory, backref="public_category_tasks", null=False)
    created_by = pw.ForeignKeyField(User, backref="user_created_tasks")
 
    def validate(self):
        if len(self.name) == 0:
            self.errors.append('Name is empty')