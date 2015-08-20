
class BaseResource(object):
    
    def __init__(self, json_representation = None, location = None, etag = None):
        self.update_attrs(json_representation, location, etag)

    def update_attrs(self, json_representation = None, location = None, etag = None):
        if location:
            self.location = location
        else:
            if json_representation:
                if 'location' in json_representation:
                    self.location = json_representation['location']
                else:
                    if 'self' in json_representation:
                        self.location = json_representation['self']                    
        if etag:
            self.etag = etag
        else:
            if json_representation and 'etag' in json_representation:
                self.etag = json_representation['etag']
        if json_representation:
            self.json_representation = json_representation
            if 'self' in json_representation:
                self.self = json_representation['self']
            if 'type' in json_representation:
                self.type = json_representation['type']

    def retrieve(self):
        # issue a GET to refresh this object from API
        if not self.location:
            raise ValueError('self location not set')
        return self.api().retrieve(self.location, self)
            
    def get_update_representation(self):
        update_representation = dict()
        if hasattr(self, 'type'):
            if hasattr(self, 'json_representation') and 'type' in self.json_representation and self.type == self.json_representation['type']:
                pass
            else:
                update_representation['type'] = self.type
        return update_representation
        
    def api():
        raise Exception('api method must be overridden')