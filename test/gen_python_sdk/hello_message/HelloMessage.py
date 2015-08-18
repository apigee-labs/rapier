import rapier.gen_python_sdk.base_entity as base_entity
import hello_world_api

class HelloMessage(base_entity.BaseEntity):
    
    def update_attrs(self, url, json_representation, etag):
        super(HelloMessage, self).update_attrs(url, json_representation, etag)
        if 'text' in json_representation:
            self.text = json_representation['text']

    def api(self):
        return hello_world_api.api
        