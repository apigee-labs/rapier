from rapier.gen_python_sdk.base_api import BaseAPI 
from rapier.gen_python_sdk.base_entity import BaseEntity
from rapier.gen_python_sdk.base_collection import BaseCollection

class TodoListAPI(BaseAPI):

    def well_known_URLs(self):
        return ['/to-dos']
    
    def resource_class(self, type_name):
        cls = globals().get(type_name)
        return cls if cls else BaseEntity
                    
api = TodoListAPI()

class TodoListAPIClass(object):
            
    def api(self):
        return api
        
class TodoList(BaseEntity, TodoListAPIClass):
            
    pass
        
class Item(BaseEntity, TodoListAPIClass):
    
    pass   
        
class Collection(BaseCollection, TodoListAPIClass):
    
    pass