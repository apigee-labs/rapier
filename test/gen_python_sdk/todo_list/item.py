from rapier.gen_python_sdk.base_entity import BaseEntity

class Item(BaseEntity):
    
    def __init__(self, json_representation = None, location = None, etag = None):
        self.type = 'Item'
        return super(Item, self).__init__(json_representation, location, etag)
    
    def update_attrs(self, json_representation, url, etag):
        super(Item, self).update_attrs(json_representation, url, etag)
        if 'description' in json_representation:
            self.description = json_representation['description']
        if 'due' in json_representation:
            self.due = json_representation['due']
            
    def get_update_representation(self):
        update_representation = super(Item, self).get_update_representation()
        if hasattr(self, 'due'):
            update_representation['due'] = self.due
        if hasattr(self, 'description'):
            update_representation['description'] = self.description
        return update_representation
                
    def api(self):
        import todo_list_api
        return todo_list_api.api