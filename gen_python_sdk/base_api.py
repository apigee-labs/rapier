import requests
from base_entity import BaseEntity
from urlparse import urlparse, urlunparse

class API(object):

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
        
    def resource_class_name(self, type_name):
        return type_name
                            
    def resource_class(self, type_name):
        api_class = self.api_class()
        return api_class.resource_classes[type_name] \
            if type_name in api_class.resource_classes else BaseEntity
            
    def api_class(self):
        raise Exception('api_class methos must be overidden in subclass')
            
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
        return self.process_entity_result(url, r, entity)

    def retrieve_well_known_resource(self, url):
        url_parts = list(urlparse(url))
        url_parts[0] = url_parts[1] = None
        
        if urlunparse(url_parts) in self.api_class().well_known_URLs:
            return self.retrieve(url)
            
    def process_entity_result(self, url, r, entity=None):
        if r.status_code == 200:
            if 'Content-Location' in r.headers:
                content_location = r.headers['Content-Location']
                if 'ETag' in r.headers:
                    etag = r.headers['ETag']
                    if 'Content-Type' in r.headers:
                        content_type = r.headers['Content-Type'].split(';')[0]
                        if content_type == 'application/json':
                            json = r.json()
                            type_name = json.get(self.type_property())
                            if type_name:
                                if entity:
                                    if entity.type == type_name:
                                        entity.update_attrs(content_location, json, etag)
                                        return entity
                                    else:
                                        return Exception('SDK cannot handle change of type from %s to %s' % (entity.type, type_name)) 
                                else:
                                    resource_class = self.resource_class(type_name)
                                    if resource_class:
                                        return resource_class(content_location, json, etag)
                                    else:
                                        return Exception('no resource_class for type %s') % r_type                        
                            else:
                                if entity:
                                    entity.update_attrs(content_location, json, etag)
                                    return entity
                                else:
                                    return Exception('no type property %s in json %s') % (self.type_property(), json.dumps())                        
                        else:
                            return Exception('non-json content type %s' %  r.headers['Content-Type'])
                    else:
                        return Exception('server did not declare content_type')
                else:
                    return Exception('server did not provide etag')
            else:
                return Exception('server failed to provide Content-Location header for url %s' % url)
        else:
            return Exception('unexpected HTTP status_code code: %s url: %s text: %s' % (r.status_code, url, r.text))