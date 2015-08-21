from rapier.gen_python_sdk.base_entity import BaseEntity

class HelloMessage(BaseEntity):

    def __init__(self, json_representation = None, location = None, etag = None):
        self.type = 'HelloMessage'
        return super(Item, self).__init__(json_representation, location, etag)
    
    def api(self):
        import hello_world_api
        return hello_world_api.api