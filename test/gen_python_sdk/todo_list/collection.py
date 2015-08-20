from rapier.gen_python_sdk.base_collection import BaseCollection
import todo_list_api

class Collection(BaseCollection):
    def api(self):
        return todo_list_api.api