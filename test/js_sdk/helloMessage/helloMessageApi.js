var helloMessageAPI = function() {

    var baseAPI = require('./../../../js_sdk/base_api')
    
    function HelloMessage(jso, url, etag) {
        baseAPI.BaseEntity.call(this, jso, url, etag)
    }
    
    HelloMessage.prototype = Object.create(baseAPI.BaseEntity.prototype);
    HelloMessage.prototype.constructor = HelloMessage;
    HelloMessage.prototype._className = 'HelloMessage';
    
    var classToKindMap = {HelloMessage: HelloMessage};
        
    function HelloMessageAPI() {}
    
    HelloMessageAPI.prototype = Object.create(baseAPI.BaseAPI.prototype);
    
    HelloMessageAPI.prototype.well_known_URLs = function() {
        return ['/message']
    }

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
