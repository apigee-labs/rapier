import requests
from base_resource import BaseBase

class BaseCollection(BaseBase):

    def update_attrs(self, json_representation, url, etag):
        super(Base_entity, self).update_attrs(json_representation, url, etag)
        if self.items_name() in json_representation:
            items_array = [self.api().build_entity_from_json(item) for item in items]
            self.items = {item.location: item for item in items_array}

    def items_name(self):
        return 'items'
        
    def create(entity):
        # create a new entity in the API by POSTing
        if self.self:
            if entity.self:
                return Error('entity already exists in API %s' % entity)
            r = requests.post(self.self, json=entity.get_property_dict())
            if r.status_code == 201:
                if 'Location' in r.headers:
                    if 'ETag' in r.headers:
                        rslt = self.build_entity_from_json(r.body, entity, r.headers['Location'], r.headers['ETag'])
                        if not isinstance(rslt, Exception):
                            if not hasattr(self, 'items'): 
                                self.items = {}
                            else:
                                if rslt.location in self.items:
                                    return Exception('Duplicate location')
                            self.items[rslt.location] = rslt
                        return rslt
                    else:
                        return Error('server failed to return ETag on POST. URL: %s entity: %s' % (self.self, entity))
                else:
                    return Error('server failed to return Location header on POST. URL: %s entity: %s' % (self.self, entity))
            else:
                return Error('Unable to create entity in API. status_code: %s error-text: %s entity: %s' % (r.status_code, r.text, entity)) 
        else:
            return Error('Collection has no self Content-Location')