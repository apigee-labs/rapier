from rapier.test.python_sdk.todo_list.todo_list_api import api, Item, Collection, TodoList

def test_objects():
    items = Collection('http://localhost:3001/to-dos/items')
    new_item = Item()
    new_item.description = 'buy milk'
    items.create(new_item)
    items.refresh()
    assert(new_item._self in items.items)
    new_item.description = 'buy gallon of milk'
    new_item.due = 'tonight'
    new_item.update()
    new_item.delete()
    
def test_api():
    body = {'kind': 'Item',
            'description':'buy milk'
           }
    new_item = api.create('http://localhost:3001/to-dos/items', body)
    items = api.retrieve('http://localhost:3001/to-dos/items')
    assert(new_item._self in items.items)
    changes = {'description': 'buy gallon of milk',
               'due': 'tonight'
              }
    api.update('http://localhost:3001/to-dos/items;' + new_item.id, new_item._etag, changes)
    api.delete('http://localhost:3001/to-dos/items;' + new_item.id)

def test_raw():
    import requests
    body = {'kind': 'Item',
            'description':'buy milk'
           }
    headers = {'Content-Type': 'application/json', 
               'Accept': 'application/json'
              }
    r = requests.post('http://localhost:3001/to-dos/items', json = body, headers = headers)
    if r.status_code != 201:
        raise Exception('unexpected HTTP status_code code: %s url: %s text: %s' % (r.status_code, r.url, r.text))
    new_item = r.json()
    etag = r.headers['ETag']
    new_item_url = r.headers['Location']
    r = requests.get('http://localhost:3001/to-dos/items', headers = {'Accept': 'application/json'})
    if r.status_code != 200:
        raise Exception('unexpected HTTP status_code code: %s url: %s text: %s' % (r.status_code, url, r.text))
    items = r.json()
    assert(new_item['_self'] in {item['_self'] for item in items['items']})
    changes = {'description': 'buy gallon of milk',
               'due': 'tonight'
               }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'If-Match': etag
        }
    r = requests.patch(new_item_url, json = changes, headers = headers)    
    if r.status_code != 200:
        raise Exception('unexpected HTTP status_code code: %s url: %s text: %s' % (r.status_code, r.url, r.text))
    r = requests.delete(new_item_url, json = changes, headers = {'Accept': 'application/json'})    
    if r.status_code != 200:
        raise Exception('unexpected HTTP status_code code: %s url: %s text: %s' % (r.status_code, r.url, r.text))
    
def main():
    test_objects()
    test_api()
    test_raw()

if __name__ == '__main__':
    main()