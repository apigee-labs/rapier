from base_resource import BaseResource
from urlparse import urlparse, urlunparse

class BaseEntity(BaseResource):
    
    def __init__(self, url, json_representation, etag):
        super(BaseEntity, self).__init__(url, json_representation, etag)
        if 'id' in json_representation:
            self.id = json_representation['id']
        self.etag = etag
        
    def is_property_name(self):
        return 'id'
        
    def refresh(self):
        # issue a GET to refresh this object from API
        if not self.self:
            raise ValueError('self_link not set')
            
    def update(self):
        # issue a PATCH or PUT to update this object from API
        if not self.self:
            raise ValueError('self_link not set')
            
    def delete(self):
        # issue a DELETE to remove this object from API
        if not self.self:
            raise ValueError('self_link not set')
        self_parts = list(urlparse(self.self))
        self_parts[0] = self_parts[1] = None
        rel_url = urlunparse(self_parts)
        if rel_url in self.api_class().well_known_URLs:
            return Exception('cannot delete well_known URL: %s' % rel_url)
                    
    def create_jso(self):
        return {
            'type': self.type
            } if self.type else {}