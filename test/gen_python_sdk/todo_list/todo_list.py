from rapier.gen_python_sdk.base_entity import BaseEntity

class TodoList(BaseEntity):
            
    def api(self):
        import todo_list_api
        return todo_list_api.api