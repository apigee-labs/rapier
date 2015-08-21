from rapier.gen_python_sdk.base_api import BaseAPI 
from rapier.gen_python_sdk.base_entity import BaseEntity
from todo_list import TodoList
from item import Item
from collection import Collection

class TodoListAPI(BaseAPI):

    def well_known_URLs(self):
        return ['/to-dos']
    
    def resource_class(self, type_name):
        cls = globals().get(type_name)
        return cls if cls else BaseEntity
                    
api = TodoListAPI()