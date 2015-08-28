var helloMessageAPI = function() {

    var baseApi = require('./../../../js_sdk/base_api')
    
    function HelloMessageAPI() {}
    
    HelloMessageAPI.prototype = new baseApi.BaseAPI()
    
    HelloMessageAPI.prototype.well_known_URLs = function() {
        return ['/message']
    }
    
    function HelloMessage() {}
    
    HelloMessage.prototype = new baseApi.BaseEntity()
    
    var classToKindMap = {HelloMessage: HelloMessage}
        
    HelloMessageAPI.prototype.resourceClass = function(type_name) {
        return  type_name in classToKindMap ? classToKindMap[type_name] : baseApi.BaseEntity      
    }
    
    var api = new HelloMessageAPI()

    HelloMessage.prototype.api = function() {
        return api        
    }

    return {
        api: api,
        HelloMessage: HelloMessage        
        }
}
    
module.exports = helloMessageAPI()
