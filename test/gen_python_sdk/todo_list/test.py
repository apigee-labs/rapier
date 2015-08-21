from rapier.test.gen_python_sdk.todo_list.todo_list_api import api
from item import Item

def main():
    todo_list = api.retrieve_well_known_resource('http://localhost:3001/to-dos')
    items = todo_list.retrieve('items')
    new_item = Item({'description':'buy milk'})
    items.create(new_item)
    assert(new_item._location)                
    items.retrieve()
    assert(new_item._location in items.items)

if __name__ == '__main__':
    main()