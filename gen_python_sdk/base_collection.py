import requests
from base_resource import BaseBase

class BaseCollection(BaseBase):

    def update_attrs(self, url, json_representation, etag):
        super(Base_entity, self).update_attrs(url, json_representation, etag)
        if self.items_name() in json_representation:
            items = json_representation[self.items_name]
            for item in items:

    def items_name(self):
        return 'items'
        
    def create(entity):
        # create a new entity in the API by POSTing
        if self.self:
            if entity.self:
                raise Error('entity already exists in API %s' % entity)
            r = requests.post(self.self, json=entity.get_property_dict())
            if r.status_code == 201:
                if 'Location' in r.headers:
                    entity.self = r.headers['Content-Location']
                else:
                    raise Error('server failed to return Location header on POST. URL: %s entity: %s' % (self.self, entity))
            else:
                raise Error('Unable to create entity in API. status_code: %s error-text: %s entity: %s' % (r.status_code, r.text, entity)) 
        else:
            raise Error('Collection has no self URL')