from rapier.test.python_sdk.hello_message.hello_world_api import api

def main():
    rslt = api.retrieve_well_known_resource('http://localhost:3000/message')
    rslt.text = 'goodbye, world'
    rslt = rslt.update()
    rslt = api.retrieve_well_known_resource('http://localhost:3000/message')
    assert(rslt.text == 'goodbye, world')    
    try:    
        rslt = rslt.delete()
    except Exception as e:
        if e.args[0].startswith('unexpected HTTP status_code code: 405 url: http://localhost:3000/message'):
            return
        else:
            raise e
    raise Exception('Deleting a well-known URL should have raised an Exception')
    
if __name__ == '__main__':
    main()