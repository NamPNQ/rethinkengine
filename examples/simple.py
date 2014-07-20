import sys
import os

sys.path.append(os.path.abspath('..'))

from rethinkengine.document import Do

class BlogPost(Document):
    title = StringField(required=True, max_length=200)
    posted = DateTimeField(default=datetime.datetime.now)
    tags = ListField(StringField(max_length=50))
