import requests

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
        #resource_class_name = self.resource_class_name(type_name)
        #if resource_class_name in globals():
        #    return globals()[resource_class_name]
        #else:
        #    raise Exception('resource class name %s not in scope' % resource_class_name)
        raise Exception('abstract method resource_class must be overridden')
            
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
                                        raise Exception('SDK cannot handle change of type from %s to %s' % (entity.type, type_name)) 
                                else:
                                    resource_class = self.resource_class(type_name)
                                    if resource_class:
                                        return resource_class(content_location, json, etag)
                                    else:
                                        raise Exception('no resource_class for type %s') % r_type                        
                            else:
                                if entity:
                                    entity.update(content_location, json, etag)
                                else:
                                    raise Exception('no type property %s in json %s') % (self.type_property(), json.dumps())                        
                        else:
                            raise Exception('non-json content type %s' %  r.headers['Content-Type'])
                    else:
                        raise Exception('server did not declare content_type')
                else:
                    raise Exception('server did not provide etag')
            else:
                raise Exception('server failed to provide Content-Location header for url %s' % url)
        else:
            raise Exception('unexpected HTTP status_code code: %s url: %s text: %s' % (r.status_code, url, r.text))