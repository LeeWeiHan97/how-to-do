from models.base_model import BaseModel
import peewee as pw
from models.room import Room
import re


class User(BaseModel):
    username = pw.CharField(unique=True, null=False)
    password = pw.CharField(null=False)
    email = pw.CharField(unique=True, null=False)
    is_admin = pw.BooleanField(default=False)
    room = pw.ForeignKeyField(Room, backref='room_users', null=True, on_delete="SET NULL")

    def validate(self):
        user = User.get_or_none(User.username == self.username)

        if len(self.email) == 0:
            self.errors.append('Email is empty')
        if len(self.password) == 0:
            self.errors.append('Password is empty')
        if len(self.username) == 0:
            self.errors.append('Username is empty')
        if len(self.password) > 0:
            if not self.id:
                if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$', self.password):
                    self.errors.append('Password does not match requirements')
        if user and not (user.id == self.id):
            self.errors.append('Username already exists')

