from base_resource import BaseResource
from urlparse import urlparse, urlunparse

class BaseEntity(BaseResource):
    
    def __init__(self, json_representation = None, location = None, etag = None):
        self._retrieved = dict()
        self.type = type(self).__name__
        super(BaseEntity, self).__init__(json_representation, location, etag)
        
    def get_update_representation(self):
        return {key: value for key, value in self.__dict__.iteritems() if not key.startswith('_')}

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
            
    def retrieve(self, relationship):
        if relationship:
            if hasattr(self, relationship):
                url = getattr(self, relationship)
                rslt = self.api().retrieve(url)
                if not isinstance(rslt, Exception):
                    self._retrieved[relationship] = rslt
                return rslt
            else:
                return Exception('no value set for items URL')
        else:
            return super(BaseEntity, self).retrieve()