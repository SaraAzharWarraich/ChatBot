from neomodel import StructuredNode, StringProperty, IntegerProperty,UniqueIdProperty, RelationshipTo, RelationshipFrom,DateProperty,DateTimeProperty,ArrayProperty
from django.conf import settings
from django.db import models
import os

class Register(StructuredNode):
    username = StringProperty(unique_index=False)
    email = StringProperty(unique_index=True)
    password = StringProperty()
    ip = StringProperty()
    gender = StringProperty()
    res = RelationshipTo('User_msg' ,'HAS')
    th = RelationshipTo('Thing' ,'HAS')
    i = RelationshipFrom('Friend' ,'IS_FRIEND_OF') 
    j = RelationshipFrom('Friend' ,'IS_FATHER_OF') 
    k = RelationshipFrom('Friend' ,'IS_MOTHER_OF') 
    l = RelationshipFrom('Friend' ,'KNOWS')
    m = RelationshipFrom('Friend' ,'IS_SISTER_OF')
    n = RelationshipFrom('Friend' ,'IS_BROTHER_OF')

class User_msg(StructuredNode):
    name = StringProperty()
    name_node = StringProperty()
    chat = ArrayProperty(StringProperty())

    def save_message(self, message_content):
        if self.chat is None:
            self.chat = []

        self.chat.append(message_content)
        self.save()


class Thing(StructuredNode):
    username = StringProperty()
    thing_name = StringProperty()


class Friend(StructuredNode):
    name = StringProperty()
    F_name = StringProperty()
    gender = StringProperty()