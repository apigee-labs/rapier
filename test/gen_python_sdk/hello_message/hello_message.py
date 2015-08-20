from rapier.gen_python_sdk.base_entity import BaseEntity
import hello_world_api

class HelloMessage(BaseEntity):
    
    def update_attrs(self, json_representation, url, etag):
        super(HelloMessage, self).update_attrs(json_representation, url, etag)
        if 'text' in json_representation:
            self.text = json_representation['text']

    def get_update_representation(self):
        get_update_representation = super(HelloMessage, self).get_update_representation()
        if hasattr('text'):
            get_update_representation['text'] = self.text
        return get_update_representation
                
    def api(self):
        return hello_world_api.api