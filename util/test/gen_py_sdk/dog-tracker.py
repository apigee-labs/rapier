
from rapier.py.base_api import BaseAPI, BaseResource, BaseEntity, BaseCollection

class API(BaseAPI):
    def well_known_URLs(self):
        return ['/']
    def resource_class(self, type_name):
        return classToKindMap.get(type_name, BaseResource)

api = API()

class APIClass(object):
    def api(self):
        return api

class Person(BaseEntity, APIClass):            
    pass

class Resource(BaseEntity, APIClass):            
    pass

class PersistentResource(BaseEntity, APIClass):            
    pass

class DogTracker(BaseEntity, APIClass):            
    pass

class Dog(BaseEntity, APIClass):            
    pass

class Collection(BaseEntity, APIClass):            
    pass

class Collection(BaseCollection, APIClass):            
    pass

classToKindMap = {
    'Person': Person,
    'Resource': Resource,
    'PersistentResource': PersistentResource,
    'DogTracker': DogTracker,
    'Dog': Dog,
    'Collection': Collection,
    'Collection': Collection
    }
