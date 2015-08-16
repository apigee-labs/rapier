from base_resource import BaseResource
from urlparse import urlparse, urlunparse

class BaseEntity(BaseResource):
    
    def update_attrs(self, url, json_representation, etag):
        super(BaseEntity, self).update_attrs(url, json_representation, etag)
        if 'id' in json_representation:
            self.id = json_representation['id']
        
    def is_property_name(self):
        return 'id'
        
    def refresh(self):
        # issue a GET to refresh this object from API
        if not self.url:
            raise ValueError('self URL not set')
        return self.api().retrieve(self.url, self)
            
    def update(self, changes):
        # issue a PATCH or PUT to update this object from API
        if not self.url:
            raise ValueError('self URL not set')
        if not self.etag:
            raise ValueError('ETag not set')
        return self.api().update(self.url, self.etag, changes, self)
            
    def delete(self):
        # issue a DELETE to remove this object from API
        if not self.self:
            raise ValueError('self URL not set')
        self_parts = list(urlparse(self.self))
        self_parts[0] = self_parts[1] = None
        rel_url = urlunparse(self_parts)
        return self.api().delete(self.url, self)    
        
    def api():
        raise Exception('api method must be overridden')
