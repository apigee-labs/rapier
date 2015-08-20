from rapier.test.gen_python_sdk.todo_list.todo_list_api import api
from item import Item

def main():
    todo_list = api.retrieve_well_known_resource('http://localhost:3001/to-dos')
    
    assert(not isinstance(todo_list, Exception))
    
    items = todo_list.retrieve('items')
    
    assert(not isinstance(items, Exception))
    
    item = items.create(Item({'description':'buy milk'}))
    
    assert(not isinstance(item, Exception))
    
    assert(item.location)
                
    items.retrieve()
    
    assert(item.location in items.items)

if __name__ == '__main__':
    main()