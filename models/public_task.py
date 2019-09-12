from models.base_model import BaseModel
import peewee as pw

class PublicTask(BaseModel):
    name = pw.CharField(unique=False, null=False)
    description = pw.CharField(unique=False, null=True)
    completed_by = pw.DateTimeField(null=False, unique=False)
    is_completed = pw.BooleanField(default=False)