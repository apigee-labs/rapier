from rapier.test.python_sdk.todo_list.todo_list_api import api, Item, Collection, TodoList

def test_objects():
    todo_list = api.retrieve_well_known_resource('http://localhost:3001/to-dos')
    items = todo_list.retrieve('items')
    assert(isinstance(items, Collection))
    new_item = Item()
    new_item.description = 'buy milk'
    items.create(new_item)
    assert(hasattr(new_item, '_location') and new_item._location)                
    items.refresh()
    assert(new_item._location in items.items)
    new_item.description = 'buy gallon of milk'
    new_item.due = 'tonight'
    new_item.update()
    new_item.refresh()
    assert(new_item.description == 'buy gallon of milk')
    new_item.delete()
    items.refresh()
    assert(new_item._location not in items.items)
    
def test_api():
    todo_list = api.retrieve('http://localhost:3001/to-dos')
    assert(hasattr(todo_list,'items'))
    items = api.retrieve('http://localhost:3001/to-dos/items')
    assert(isinstance(items, Collection))
    body = {
        'kind': 'Item',
        'description':'buy milk'
        }
    new_item = api.create('http://localhost:3001/to-dos/items', body)
    assert(hasattr(new_item, '_location') and new_item._location)                
    items = api.retrieve('http://localhost:3001/to-dos/items')
    assert(new_item._location in items.items)
    changes = {
        'description': 'buy gallon of milk',
        'due': 'tonight'
        }
    new_item2 = api.update(new_item._location, new_item._etag, changes)
    assert(new_item2._etag == str(int(new_item._etag) + 1))
    assert(new_item2.description == 'buy gallon of milk')
    new_item3 = api.delete(new_item._location)
    assert(new_item3._etag == new_item2._etag)
    items = api.retrieve('http://localhost:3001/to-dos/items')
    assert(new_item3._location not in items.items)
    
def main():
    test_objects()
    test_api()

if __name__ == '__main__':
    main()