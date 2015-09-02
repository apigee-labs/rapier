var helloMessageAPI = function() {

    var baseAPI = require('./../../../js_sdk/base_api')
    
    function HelloMessageAPI() {}
    
    HelloMessageAPI.prototype = new baseAPI.BaseAPI();
    
    HelloMessageAPI.prototype.well_known_URLs = function() {
        return ['/message']
    }
    
    function HelloMessage(jso, url, etag) {
        baseAPI.BaseEntity.call(this, jso, url, etag)
    }
    
    HelloMessage.prototype = Object.create(baseAPI.BaseEntity.prototype);
    HelloMessage.prototype.constructor = HelloMessage;
    
    var classToKindMap = {HelloMessage: HelloMessage};
        
    HelloMessageAPI.prototype.resourceClass = function(type_name) {
        return  type_name in classToKindMap ? classToKindMap[type_name] : baseAPI.BaseEntity      
    }
    
    var api = new HelloMessageAPI();

    HelloMessage.prototype.api = function() {
        return api        
    }

    return {
        api: api,
        HelloMessage: HelloMessage        
        }
}
    
module.exports = helloMessageAPI()
