from rapier.gen_python_sdk.base_entity import BaseEntity

class HelloMessage(BaseEntity):

    def api(self):
        import hello_world_api
        return hello_world_api.api