var helloMessageAPI = require('./helloMessageAPI')
var api = helloMessageAPI.api

// rslt = api.retrieve_well_known_resource('http://localhost:3000/message')
rslt = api.retrieve('http://localhost:3000/message', function(error, message) {
    if (error) {
        console.log(error)
    } else {
        if (!(message instanceof helloMessageAPI.HelloMessage)) throw 'assert'
        message.text = "It's a JS world";
        message.update(function(error) {
            if (error) throw error.args[0];
            if (!message.text == "It's a JS world") throw 'assert'
            message.delete(function(error) {
                if (!error) {
                    throw 'should not be allowed to delete well-known resource'
                }
            }) 
        })
    }
})