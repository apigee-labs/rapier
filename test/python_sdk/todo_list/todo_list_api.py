from rapier.python_sdk.base_api import BaseAPI, BaseEntity, BaseCollection

class API(BaseAPI):

    def well_known_URLs(self):
        return ['/to-dos']
    
    def resource_class(self, type_name):
        cls = globals().get(type_name)
        return cls if cls else BaseEntity
                    
api = API()

class APIClass(object):
            
    def api(self):
        return api
        
class TodoList(BaseEntity, APIClass):
            
    pass
        
class Item(BaseEntity, APIClass):
    
    pass   
        
class Collection(BaseCollection, APIClass):
    
    pass