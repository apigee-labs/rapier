var helloMessageAPI = require('./helloMessageAPI')
var api = helloMessageAPI.api

// rslt = api.retrieve_well_known_resource('http://localhost:3000/message')
rslt = api.retrieve('http://localhost:3000/message', function(error, entity) {
    if (error) {
        console.log(error)
    } else {
        if (!(entity instanceof helloMessageAPI.HelloMessage)) throw 'assert'
        console.log(entity);
        entity.text = "It's a JS world";
        entity.update(function(error, entity) {
            if (error) throw error.args[0];
            if (!entity.text == "It's a JS world") throw 'assert'
            entity.delete(function(error, entity) {
                if (!error) {
                    throw 'should not be allowed to delete well-known resource'
                } else {
                    console.log('delete refused as expected: ' + error.args[0])
                }
            }) 
        })
    }
})