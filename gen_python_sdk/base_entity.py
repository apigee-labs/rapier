from base_resource import BaseResource
from urlparse import urlparse, urlunparse

class BaseEntity(BaseResource):
    
    def __init__(self, json_representation = None, location = None, etag = None):
        self.retrieved = dict()
        return super(BaseEntity, self).__init__(json_representation, location, etag)

    def update_attrs(self, json_representation, location=None, etag=None):
        super(BaseEntity, self).update_attrs(json_representation, location, etag)
        id_name = self.id_property_name()
        if id_name in json_representation:
            setattr(self, id_name, json_representation['id'])

    def id_property_name(self):
        return 'id'
        
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
            elif relationship in self.json_representation:
                url = self.json_representation[relationship]
            if url:
                rslt = self.api().retrieve(url)
                if isinstance(rslt, Exception):
                    return rslt
                else:
                    self.retrieved[relationship] = rslt
                    return rslt
            else:
                return Exception('no value set for items URL')
        else:
            return super(BaseEntity, self).retrieve()