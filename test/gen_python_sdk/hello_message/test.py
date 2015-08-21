from rapier.test.gen_python_sdk.hello_message.hello_world_api import api

rslt = api.retrieve_well_known_resource('http://localhost:3000/message')
changes = {'text': 'goodbye, world'}
rslt = rslt.update(changes)        
rslt = rslt.delete()