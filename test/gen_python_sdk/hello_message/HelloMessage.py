import rapier.gen_python_sdk.base_entity as base_entity
import hello_world_api

class HelloMessage(base_entity.BaseEntity):
    
    def __init__(self, url, json_representation, etag):
        super(HelloMessage, self).__init__(url, json_representation, etag)
        if 'text' in json_representation:
            self.text = json_representation['text']
        else:
            raise Exception(520, 'server did not provide text property')

    def api_class(self):
        return hello_world_api.api_class