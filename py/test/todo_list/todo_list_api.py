from rapier.py.base_api import BaseAPI, BaseResource, BaseEntity, BaseCollection

class API(BaseAPI):
    def well_known_URLs(self):
        return ['/to-dos']
    def resource_class(self, type_name):
        return classToKindMap.get(type_name, BaseResource)
                    
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
    
classToKindMap = {
    'TodoList': TodoList,
    'Item': Item,
    'Collection': Collection
    }