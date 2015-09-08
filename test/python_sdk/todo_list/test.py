from rapier.test.python_sdk.todo_list.todo_list_api import api, Item, Collection, TodoList

def test_objects():
    # retrieve the todo list at the well-known URL http://localhost:3001/to-dos
    todo_list = api.retrieve_well_known_resource('http://localhost:3001/to-dos')
    # retrieve he list of Items for the todo todo list. It will be an instance of Collection
    items = todo_list.retrieve('items')
    # Build a new Item to POST to the Collection
    new_item = Item()
    new_item.description = 'buy milk'
    # POST the new Item
    items.create(new_item)
    # Modify the new Item
    new_item.description = 'buy gallon of milk'
    new_item.due = 'tonight'
    # Push the modifictions to the server. This uses a PATCH method with only the modified properties
    new_item.update()
    # Delete the new item we just created
    new_item.delete()
    
def test_api():
    # retrieve the todo list at the well-known URL http://localhost:3001/to-dos
    todo_list = api.retrieve('http://localhost:3001/to-dos')
    # retrieve the items list at the well-known URL http://localhost:3001/to-dos/items
    items = api.retrieve('http://localhost:3001/to-dos/items')
    # construct a new Item
    body = {
        'kind': 'Item',
        'description':'buy milk'
        }
    # add it to the Collection at the well-known URL http://localhost:3001/to-dos/items
    new_item = api.create('http://localhost:3001/to-dos/items', body)
    # construct a change object
    changes = {
        'description': 'buy gallon of milk',
        'due': 'tonight'
        }
    # Update the object at new_item._location
    new_item2 = api.update(new_item._location, new_item._etag, changes)
    # delete the item
    api.delete(new_item._location)
    
def main():
    test_objects()
    test_api()

if __name__ == '__main__':
    main()