
class Base_base(object):
    
    __init__(self, url = None, json_representation = None, etag = None):
        if url:
            self.url = url
        if json_representation:
            if 'self' in json_representation:
                self.self = json_representation['self']
            if 'type' in json_representation:
                self.type = json_representation['type']
            if 'id' in json_representation:
                self.type = json_representation['id']
        if etag:
            self.etag = etag