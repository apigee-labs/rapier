from rapier.gen_python_sdk.base_api import BaseAPI 
from hello_message import HelloMessage

class HelloWorldAPI(BaseAPI):

    well_known_URLs = ['/message']
    resource_classes = {'HelloMessage': HelloMessage}
    
    def api_class(self):
        return HelloWorldAPI
        
api = HelloWorldAPI()