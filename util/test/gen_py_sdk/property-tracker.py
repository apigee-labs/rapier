
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

class Bicycle(BaseEntity, APIClass):            
    pass

class Dog(BaseEntity, APIClass):            
    pass

class Collection(BaseEntity, APIClass):            
    pass

class Person(BaseEntity, APIClass):            
    pass

class PropertyTracker(BaseEntity, APIClass):            
    pass

class PersistentResource(BaseEntity, APIClass):            
    pass

class Resource(BaseEntity, APIClass):            
    pass

class Institution(BaseEntity, APIClass):            
    pass

class Collection(BaseCollection, APIClass):            
    pass

classToKindMap = {
    'Bicycle': Bicycle,
    'Dog': Dog,
    'Collection': Collection,
    'Person': Person,
    'PropertyTracker': PropertyTracker,
    'PersistentResource': PersistentResource,
    'Resource': Resource,
    'Institution': Institution,
    'Collection': Collection
    }
