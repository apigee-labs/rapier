import requests
from base_entity import BaseEntity
from urlparse import urlparse, urlunparse

class BaseAPI(object):

    def retrieve_headers(self):
        return {
            'Accept': 'application/json'
            }

    def update_headers(self, etag):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'If-Match': etag
            }

    def delete_headers(self):
        return {
            'Accept': 'application/json'
            }

    def type_property(self):
        return 'type'
        
    def retrieve(self, url, entity=None, headers=None):
        # issue a GET to retrieve a resource from the API and create an object for it
        r = requests.get(url, headers = headers if headers else self.retrieve_headers())
        return self.process_entity_result(url, r, entity)
        
    def update(self, url, etag, changes, entity=None, headers=None):
        r = requests.patch(url, json=changes, headers = headers if headers else self.update_headers(etag))
        return self.process_entity_result(url, r, entity)
            
    def delete(self, url, entity=None, headers=None):
        r = requests.delete(url, headers = headers if headers else self.delete_headers())
        return self.process_entity_result(url, r, entity)
            
    def create(self, url, body, entity=None, headers=None):
        r = requests.post(url, json=body, headers = headers if headers else self.delete_headers())
        return self.process_entity_result(url, r, entity, 'Location')

    def retrieve_well_known_resource(self, url):
        url_parts = list(urlparse(url))
        url_parts[0] = url_parts[1] = None
        
        if urlunparse(url_parts) in self.well_known_URLs():
            return self.retrieve(url)
        else:
            raise Exception('no such well-known resource %s. Valid urls are: %s' % (urlunparse(url_parts)), self.api_class().well_known_URLs)
            
    def process_entity_result(self, url, r, entity=None, location_header = 'Content-Location'):
        if r.status_code == 200 or r.status_code == 201:
            if location_header in r.headers:
                location = r.headers[location_header]
                if 'ETag' in r.headers:
                    etag = r.headers['ETag']
                    if 'Content-Type' in r.headers:
                        content_type = r.headers['Content-Type'].split(';')[0]
                        if content_type == 'application/json':
                            json = r.json()
                            return self.build_entity_from_json(json, entity, location, etag)
                        else:
                            raise Exception('non-json content type %s' %  r.headers['Content-Type'])
                    else:
                        raise Exception('server did not declare content_type')
                else:
                    raise Exception('server did not provide etag')
            else:
                raise Exception('server failed to provide %s header for url %s' % (location_header, url))
        else:
            raise Exception('unexpected HTTP status_code code: %s url: %s text: %s' % (r.status_code, url, r.text))
            
    def build_entity_from_json(self, json, entity=None, location=None, etag=None):
        type_name = json.get(self.type_property())
        if type_name:
            if entity:
                if entity.type == type_name:
                    entity.update_attrs(json, location, etag)
                    return entity
                else:
                    raise Exception('SDK cannot handle change of type from %s to %s' % (entity.type, type_name)) 
            else:
                resource_class = self.resource_class(type_name)
                if resource_class:
                    return resource_class(json, location, etag)
                else:
                    raise Exception('no resource_class for type %s') % r_type                        
        else:
            if entity:
                entity.update_attrs(location, json, etag)
                return entity
            else:
                raise Exception('no type property %s in json %s') % (self.type_property(), json.dumps())               

class BaseResource(object):
    
    def __init__(self, json_representation = None, location = None, etag = None):
        self.update_attrs(json_representation, location, etag)

    def update_attrs(self, json_representation = None, location = None, etag = None):
        if json_representation:
            for key, value in json_representation.iteritems():
                setattr(self, key, value)
            json_self = json_representation.get('self')
            if json_self:
                self._location = json_self
        if location:
            self._location = location
        if etag:
            self.etag = etag

    def retrieve(self):
        # issue a GET to refresh this object from API
        if not self._location:
            raise Exception('self location not set')
        return self.api().retrieve(self._location, self)
        
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
            raise Exception('self location not set')
        if not self.etag:
            raise Exception('ETag not set')
        return self.api().update(self.location, self.etag, changes, self)
            
    def delete(self):
        # issue a DELETE to remove this object from API
        if not self.location:
            raise Exception('self location not set')
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
                raise Exception('no value set for items URL')
        else:
            return super(BaseEntity, self).retrieve()
            
class BaseCollection(BaseResource):

    def update_attrs(self, json_representation, url, etag):
        super(BaseCollection, self).update_attrs(json_representation, url, etag)
        if 'items' in json_representation:
            items = json_representation['items']
            items_array = [self.api().build_entity_from_json(item) for item in items]
            self.items = {item._location: item for item in items_array}

    def create(self, entity):
        # create a new entity in the API by POSTing
        if self.self:
            if hasattr(entity, 'self') and entity.self:
                raise Exception('entity already exists in API %s' % entity)
            rslt = self.api().create(self.self, entity.get_update_representation(), entity)
            if entity._location in self.items:
                raise Exception('Duplicate location')
            else:
                self.items[entity._location] = entity
                return entity
        else:
            raise Exception('Collection has no self property')