from rapier.gen_python_sdk.base_entity import BaseEntity

class TodoList(BaseEntity):
    
    def update_attrs(self, json_representation, location=None, etag=None):
        super(TodoList, self).update_attrs(json_representation, location, etag)
        if 'items' in json_representation:
            self.items = json_representation['items']
        
    def api(self):
        import todo_list_api
        return todo_list_api.api