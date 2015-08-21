import requests
from urlparse import urlparse, urlunparse
import json

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
        return self.process_entity_result(url, r, entity, location_header = 'Location')

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
                            jso = r.json()
                            return self.build_entity_from_json(jso, entity, location, etag)
                        else:
                            raise Exception('non-json content_type %s' %  r.headers['Content-Type'])
                    else:
                        raise Exception('server did not declare content_type')
                else:
                    raise Exception('server did not provide etag')
            else:
                raise Exception('server failed to provide %s header for url %s' % (location_header, url))
        else:
            raise Exception('unexpected HTTP status_code code: %s url: %s text: %s' % (r.status_code, url, r.text))
            
    def build_entity_from_json(self, jso, entity=None, location=None, etag=None):
        kind = jso.get('kind')
        if kind:
            if entity:
                if entity.kind == kind:
                    entity.update_attrs(jso, location, etag)
                    return entity
                else:
                    raise Exception('SDK cannot handle change of kind from %s to %s' % (entity.kind, kind)) 
            else:
                resource_class = self.resource_class(kind)
                if resource_class:
                    return resource_class(jso, location, etag)
                else:
                    raise Exception('no resource_class for kind %s') % kind                        
        else:
            if entity:
                entity.update_attrs(location, jso, etag)
                return entity
            else:
                raise Exception('no kind property %s in json %s' % ('kind', json.dumps(jso)))               

class BaseResource(object):
    
    def __init__(self, json_representation = None, location = None, etag = None):
        self.update_attrs(json_representation, location, etag)

    def update_attrs(self, json_representation = None, location = None, etag = None):
        if json_representation:
            for key, value in json_representation.iteritems():
                setattr(self, key, value)
            json_self = json_representation.get('_self')
            if json_self:
                self._location = json_self
            self._json_representation = json_representation
        else:
            self._json_representation = dict()
        if location:
            self._location = location
        if etag:
            self._etag = etag

    def retrieve(self):
        # issue a GET to refresh this object from API
        if not self._location:
            raise Exception('self location not set')
        return self.api().retrieve(self._location, self)
        
class BaseEntity(BaseResource):
    
    def __init__(self, json_representation = None, location = None, etag = None):
        self._retrieved = dict()
        self.kind = type(self).__name__
        super(BaseEntity, self).__init__(json_representation, location, etag)
        
    def get_update_representation(self):
        json_representation = self._json_representation
        return {key: value for key, value in self.__dict__.iteritems() if not (key.startswith('_') or (key in json_representation and json_representation[key] == value))}

    def update(self, changes=None):
        # issue a PATCH or PUT to update this object from API
        if changes == None:
            changes = self.get_update_representation()
        if not self._location:
            raise Exception('self location not set')
        if not self._etag:
            raise Exception('ETag not set')
        return self.api().update(self._location, self._etag, changes, self)
            
    def delete(self):
        # issue a DELETE to remove this object from API
        if not self._location:
            raise Exception('self location not set')
        else:
            return self.api().delete(self._location, self)
            
    def retrieve(self, relationship=None):
        if relationship:
            if hasattr(self, relationship):
                url = getattr(self, relationship)
                rslt = self.api().retrieve(url)
                if not isinstance(rslt, Exception):
                    self._retrieved[relationship] = rslt
                return rslt
            else:
                raise Exception('no value set for %s URL' % relationship)
        else:
            return super(BaseEntity, self).retrieve()
            
class BaseCollection(BaseResource):

    def update_attrs(self, json_representation, url, etag):
        super(BaseCollection, self).update_attrs(json_representation, url, etag)
        if '_items' in json_representation:
            items = json_representation['_items']
            items_array = [self.api().build_entity_from_json(item) for item in items]
            self._items = {item._location: item for item in items_array}

    def create(self, entity):
        # create a new entity in the API by POSTing
        if self._self:
            if hasattr(entity, '_self') and entity._self:
                raise Exception('entity already exists in API %s' % entity)
            rslt = self.api().create(self._self, entity.get_update_representation(), entity)
            if entity._self in self._items:
                raise Exception('Duplicate location')
            else:
                self._items[entity._self] = entity
                return entity
        else:
            raise Exception('Collection has no _self property')