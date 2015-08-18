from rapier.test.gen_python_sdk.hello_message.hello_world_api import api

rslt = api.retrieve_well_known_resource('http://localhost:3000/message')
if isinstance(rslt, Exception):
    print rslt
else:
    print rslt, rslt.__dict__

    changes = {'text': 'goodbye, world'}
    rslt = rslt.update(changes)
    
    if isinstance(rslt, Exception):
        print rslt
    else:
        print rslt, rslt.__dict__
            
        rslt = rslt.delete()
        
        if isinstance(rslt, Exception):
            print rslt
        else:
            print rslt, rslt.__dict__
