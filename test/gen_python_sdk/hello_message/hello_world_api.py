from rapier.gen_python_sdk.base_api import API 
from urlparse import urlparse, urlunparse
from HelloMessage import HelloMessage
import rapier.gen_python_sdk.base_entity as base_entity

class HelloWorldAPI(API):

    well_known_URLs = ['/message']
    resource_classes = {'HelloMessage': HelloMessage}
    
    def api_class(self):
        return HelloWorldAPI
        
api = HelloWorldAPI()