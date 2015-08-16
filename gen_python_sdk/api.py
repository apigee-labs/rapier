import requests

class API(object):
    def accept_header_value(self):
        return 'application/json'
        
    def get_headers(self):
        return {
            'Accept': self.accept_header_value()
            }

    def type_property(self):
        return 'type'
        
    def resource_class_name(self, type_name):
        return type_name
                            
    def resource_class(self, type_name):
        resource_class_name = self.resource_class_name(type_name)
        if resource_class_name in globals():
            return globals()[resource_class_name]
        else:
            raise Exception('resource class name %s not in scope' % resource_class_name)
            
    def retrieve(self, url):
        # issue a GET to retrieve a resource from the API and create an object for it
        r = requests.get(url, headers = self.get_headers())
        if r.status_code == 200:
            if 'Content-Location' in r.headers:
                content_location = r.headers['Content-Location']
            else:
                print 'Warning - server failed to provide Content-Location header for url %s' % url
                content_location = None
            if 'content_type' in r.headers:
                if r.headers['content_type'] == 'json':
                    json = r.json()
                    type_name = json.get(self.type_property())
                    if type_name:
                        resource_class = self.resource_class(type_name)
                        if resource_class:
                            return self.resource_class()(self, json, content_location)
                        else:
                            raise Exception('no resource_class for type %s') % r_type                        
                    else:
                        raise Exception('no type property %s in json %s') % (self.type_property(), json.dumps())                        
                else:
                    raise Exception('non-json content type')
            else:
                raise Exception('server did not declare content_type')
        else:
            raise Exception('unexpected HTTP status_code code %s' % r.status_code)