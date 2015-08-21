from rapier.test.gen_python_sdk.todo_list.todo_list_api import api, Item

def main():
    todo_list = api.retrieve_well_known_resource('http://localhost:3001/to-dos')
    items = todo_list.retrieve('_items')
    new_item = Item({'description':'buy milk'})
    items.create(new_item)
    assert(hasattr(new_item, '_location') and new_item._location)                
    items.retrieve()
    assert(new_item._location in items._items)
    new_item.description = 'buy more milk'
    new_item.due = 'tonight'
    new_item.update()
    new_item.retrieve()
    assert(new_item.description == 'buy more milk')

if __name__ == '__main__':
    main()