import requests
from base_resource import BaseResource

class BaseCollection(BaseResource):

    def update_attrs(self, json_representation, url, etag):
        super(BaseCollection, self).update_attrs(json_representation, url, etag)
        if 'items' in json_representation:
            items = json_representation['items']
            items_array = [self.api().build_entity_from_json(item) for item in items]
            self.items = {item._location: item for item in items_array}

    def create(self, entity):
        # create a new entity in the API by POSTing
        if self.self:
            if hasattr(entity, 'self') and entity.self:
                return Exception('entity already exists in API %s' % entity)
            r = requests.post(self.self, json=entity.get_update_representation())
            if r.status_code == 201:
                if 'Location' in r.headers:
                    if 'ETag' in r.headers:
                        entity.update_attrs(r.json(), r.headers['Location'], r.headers['ETag'])
                        if entity._location in self.items:
                            return Exception('Duplicate location')
                        else:
                            self.items[entity._location] = entity
                            return entity
                    else:
                        return Exception('server failed to return ETag on POST. URL: %s entity: %s' % (self.self, entity))
                else:
                    return Exception('server failed to return Location header on POST. URL: %s entity: %s' % (self.self, entity))
            else:
                return Exception('Unable to create entity in API. status_code: %s Exception-text: %s entity: %s' % (r.status_code, r.text, entity)) 
        else:
            return Exception('Collection has no self Content-Location')