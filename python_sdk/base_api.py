import requests
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

    def retrieve(self, url, entity=None, headers=None):
        # issue a GET to retrieve a resource from the API and create an object for it
        r = requests.get(url, headers = headers if headers is not None else self.retrieve_headers())
        return self.process_resource_result(url, r, entity)
        
    def update(self, url, etag, changes, entity=None, headers=None):
        r = requests.patch(url, json=changes, headers = headers if headers is not None else self.update_headers(etag))
        return self.process_resource_result(url, r, entity)
            
    def delete(self, url, entity=None, headers=None):
        r = requests.delete(url, headers = headers if headers is not None else self.delete_headers())
        return self.process_resource_result(url, r, entity)
            
    def create(self, url, body, entity=None, headers=None):
        r = requests.post(url, json=body, headers = headers if headers is not None else self.delete_headers())
        return self.process_resource_result(url, r, entity, location_header = 'Location')

    def retrieve_well_known_resource(self, url, entity=None, headers=None):
        url_parts = list(urlparse(url))
        url_parts[0] = url_parts[1] = None
        
        if urlunparse(url_parts) in self.well_known_URLs():
            return self.retrieve(url, entity, headers)
        else:
            raise Exception('no such well-known resource %s. Valid urls are: %s' % (urlunparse(url_parts)), self.api_class().well_known_URLs)
            
    def process_resource_result(self, url, r, entity=None, location_header = 'Content-Location'):
        if r.status_code == 200 or r.status_code == 201:
            if location_header in r.headers:
                location = r.headers[location_header]
                if 'ETag' in r.headers:
                    etag = r.headers['ETag']
                    if 'Content-Type' in r.headers:
                        content_type = r.headers['Content-Type'].split(';')[0]
                        if content_type == 'application/json':
                            jso = r.json()
                            return self.build_resource_from_json(jso, entity, location, etag)
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
            
    def build_resource_from_json(self, jso, entity=None, url=None, etag=None):
        kind = jso.get('kind')
        if kind:
            if entity:
                if not hasattr(entity, 'kind') or entity.kind == kind:
                    entity.update_attrs(jso, url, etag)
                    return entity
                else:
                    raise Exception('SDK cannot handle change of kind from %s to %s' % (entity.kind, kind)) 
            else:
                resource_class = self.resource_class(kind)
                if resource_class:
                    return resource_class(jso, url, etag)
                else:
                    raise Exception('no resource_class for kind %s') % kind                        
        else:
            if entity and entity.kind:
                entity.update_attrs(url, jso, etag)
                return entity
            else:
                raise Exception('no kind property in json %s' % jso)               

class BaseResource(object):
    
    def __init__(self, jso = None, url = None, etag = None):
        self.update_attrs(jso, url, etag)

    def update_attrs(self, jso = None, url = None, etag = None):
        if jso:
            for key, value in jso.iteritems():
                setattr(self, key, value)
            if '_self' in jso:
                self._location = jso['_self']
            self._jso = jso
        if url:
            self._location = url
        if etag:
            self._etag = etag

    def refresh(self):
        # issue a GET to refresh this object from API
        if not self._location:
            raise Exception('self location not set')
        return self.api().retrieve(self._location, self)
        
class BaseEntity(BaseResource):
    
    def __init__(self, jso = None, url = None, etag = None):
        if url and (not jso or not etag):
            raise Exception('To load an entity, use api.receive(url). This ensures that the entity class will match the server data.\n\
Creating an Entity first and loading it implies guessing the type at the end of the URL')
        self._relatedResources = dict()
        self.kind = type(self).__name__
        super(BaseEntity, self).__init__(jso, url, etag)
        
    def get_update_representation(self):
        jso = self._jso if hasattr(self, '_jso') else None
        return {key: value for key, value in self.__dict__.iteritems() if not (key.startswith('_') or (jso and key in jso and jso[key] == value))}

    def update(self):
        # issue a PATCH or PUT to update this object from API
        changes = self.get_update_representation()
        if not (hasattr(self, '_location') and self._location):
            raise Exception('self _location not set')
        if not hasattr(self, '_etag') or self._etag == None:
            raise Exception('self _etag not set')
        return self.api().update(self._location, self._etag, changes, self)
            
    def delete(self):
        # issue a DELETE to remove this object from API
        if not self._location:
            raise Exception('self location not set')
        else:
            return self.api().delete(self._location, self)
            
    def retrieve(self, relationship):
        # fetch a related resource
        if hasattr(self, relationship):
            url = getattr(self, relationship)
            rslt = self.api().retrieve(url)
            if not isinstance(rslt, Exception):
                self._relatedResources[relationship] = rslt
            return rslt
        else:
            raise Exception('no value set for %s URL' % relationship)

    def get_related(self, relationship, default_value):
        # return a previously-fetched related resource
        return self._relatedResources.get(relationship, default_value)
            
class BaseCollection(BaseResource):

    def update_attrs(self, jso, url, etag):
        super(BaseCollection, self).update_attrs(jso, url, etag)
        if jso and 'items' in jso:
            items = jso['items']
            items_array = [self.api().build_resource_from_json(item) for item in items]
            self.items = {item._location: item for item in items_array}

    def create(self, entity):
        # create a new entity in the API by POSTing
        if self._location:
            if hasattr(entity, '_self') and entity._self:
                raise Exception('entity already exists in API %s' % entity)
            rslt = self.api().create(self._location, entity.get_update_representation(), entity)
            if hasattr(self, 'items'):
                if entity._self in self.items:
                    raise Exception('Duplicate id')
                else:
                    self.items[entity._self] = entity
            return entity
        else:
            raise Exception('Collection has no _self property')