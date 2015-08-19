from base_resource import BaseResource
from urlparse import urlparse, urlunparse

class BaseEntity(BaseResource):
    
    def update_attrs(self, json_representation, location=None, etag=None):
        super(BaseEntity, self).update_attrs(json_representation, location, etag)
        if 'id' in json_representation:
            self.id = json_representation['id']
        
    def is_property_name(self):
        return 'id'
        
    def refresh(self):
        # issue a GET to refresh this object from API
        if not self.location:
            raise ValueError('self location not set')
        return self.api().retrieve(self.location, self)
            
    def update(self, changes):
        # issue a PATCH or PUT to update this object from API
        if not self.location:
            raise ValueError('self location not set')
        if not self.etag:
            raise ValueError('ETag not set')
        return self.api().update(self.location, self.etag, changes, self)
            
    def delete(self):
        # issue a DELETE to remove this object from API
        if not self.location:
            return ValueError('self location not set')
        else:
            return self.api().delete(self.location, self)