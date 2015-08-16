from rapier.gen_python_sdk import api 
from urlparse import urlparse, urlunparse

class Hello_World_API(api.API):

    well_known_URLs = ['/message']
        
    def get_well_known_resource(self, url):
        
        url_parts = list(urlparse(url))
        url_parts[0] = url_parts[1] = None
        
        if urlunparse(url_parts) in Hello_World_API.well_known_URLs:
            return self.retrieve(url)
            
api = Hello_World_API()