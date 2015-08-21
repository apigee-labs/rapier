
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
            raise ValueError('self location not set')
        return self.api().retrieve(self._location, self)
            
    def api():
        raise Exception('api method must be overridden')