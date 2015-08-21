from rapier.gen_python_sdk.base_api import BaseAPI 

class HelloWorldAPI(BaseAPI):

    def well_known_URLs(self):
        return ['/message']
    
    def resource_class(self, type_name):
        cls = globals().get(type_name)
        return cls if cls else BaseEntity
        
api = HelloWorldAPI()