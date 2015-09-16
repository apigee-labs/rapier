
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

class PropertyTracker(BaseEntity, APIClass):            
    pass

class Bicycle(BaseEntity, APIClass):            
    pass

class Dog(BaseEntity, APIClass):            
    pass

class Institution(BaseEntity, APIClass):            
    pass

class Collection(BaseCollection, APIClass):            
    pass

classToKindMap = {
    'Person': Person,
    'PropertyTracker': PropertyTracker,
    'Bicycle': Bicycle,
    'Dog': Dog,
    'Institution': Institution,
    'Collection': Collection
    }
