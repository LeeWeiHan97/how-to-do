from models.scheduled_task import Scheduled
from blueprints.users.views import notification
import datetime

scheduled = Scheduled.select()

scheduled.date_time