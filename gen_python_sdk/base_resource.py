
class BaseResource(object):
    
    def __init__(self, json_representation = None, location = None, etag = None):
        self.update_attrs(json_representation, location, etag)

    def update_attrs(self, json_representation = None, location = None, etag = None):
        if location:
            self.location = location
        else:
            if json_representation and 'location' in json_representation:
                self.location = json_representation['location']
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
            if 'id' in json_representation:
                self.type = json_representation['id']
        
    def api():
        raise Exception('api method must be overridden')