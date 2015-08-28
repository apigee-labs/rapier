var helloMessageAPI = require('./helloMessageAPI')
var api = helloMessageAPI.api
console.log(api.retrieveHeaders())

// rslt = api.retrieve_well_known_resource('http://localhost:3000/message')
rslt = api.retrieve('http://localhost:3000/message', function(error, entity) {
    if (error) {
        console.log(error)
    } else {
        console.log(entity)
    }
})

/*
changes = {'text': 'goodbye, world'}
rslt = rslt.update(changes)    
try:    
    rslt = rslt.delete()
except Exception as e:
    if e.args[0].startswith('unexpected HTTP status_code code: 405 url: http://localhost:3000/message'):
        return
    else:
        raise e
raise Exception('Deleting a well-known URL should have raised an Exception')
*/