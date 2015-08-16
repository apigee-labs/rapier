import rapier.gen_python_sdk.base_entity as base_entity

class HelloMessage(base_entity.BaseEntity):
    
    def __init__(self, url, json_representation, etag):
        super(Base_entity, self).__init__(url, json_representation, etag)
        if 'text' in json_representation:
            self.id = json_representation['text']
        else:
            raise Exception(520, 'server did not provide text property')
