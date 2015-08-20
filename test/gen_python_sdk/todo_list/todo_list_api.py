from rapier.gen_python_sdk.base_api import BaseAPI 
from todo_list import TodoList
from item import Item
from collection import Collection

class TodoListAPI(BaseAPI):

    well_known_URLs = ['/to-dos']
    resource_classes = {
        'Collection': Collection,
        'Item': Item,
        'TodoList': TodoList
        }
    
    def api_class(self):
        return TodoListAPI
        
api = TodoListAPI()