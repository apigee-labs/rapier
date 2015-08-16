from rapier.gen_python_sdk.base_api import API 
from urlparse import urlparse, urlunparse
from HelloMessage import HelloMessage
import rapier.gen_python_sdk.base_entity as base_entity

class HelloWorldAPI(API):

    well_known_URLs = ['/message']
    resource_classes = {'HelloMessage': HelloMessage}
        
    def get_well_known_resource(self, url):
        
        url_parts = list(urlparse(url))
        url_parts[0] = url_parts[1] = None
        
        if urlunparse(url_parts) in HelloWorldAPI.well_known_URLs:
            return self.retrieve(url)
            
    def resource_class(self, type_name):
        return HelloWorldAPI.resource_classes[type_name] if type_name in HelloWorldAPI.resource_classes else base_entity

api_class = HelloWorldAPI
api = HelloWorldAPI()