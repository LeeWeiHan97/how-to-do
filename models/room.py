from models.base_model import BaseModel
import peewee as pw

class Room(BaseModel):
    name = pw.CharField(null=False, unique=False)