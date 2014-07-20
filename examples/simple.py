import sys
import os

sys.path.append(os.path.abspath('..'))

from rethinkengine.document import Document
from rethinkengine.fields import *


class User(Document):
    username = StringField()
    password = StringField()


user = User(username='root', password='s3cret')
print user, user.username
