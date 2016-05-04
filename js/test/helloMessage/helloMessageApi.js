var baseAPI = require('./../../../js/base_api')

var exports = function() {
    
    function API() {}
    
    API.prototype = Object.create(baseAPI.BaseAPI.prototype);
    API.prototype.wellKnownURLs = function() {
        return ['/message']
    }
    API.prototype.resourceClass = function(type_name) {
        return  type_name in classToKindMap ? classToKindMap[type_name] : baseAPI.BaseEntity      
    }
        
    var api = new API();

    var api_function = function() {
        return api
    }

    function HelloMessage(url, jso, etag) {
        baseAPI.BaseEntity.call(this, url, jso, etag)
    }
    HelloMessage.prototype = Object.create(baseAPI.BaseEntity.prototype);
    HelloMessage.prototype.constructor = HelloMessage;
    HelloMessage.prototype._className = 'HelloMessage';
    HelloMessage.prototype.api = api_function;
    
    var classToKindMap = {
        HelloMessage: HelloMessage
        };
        
    return {
        api: api,
        HelloMessage: HelloMessage        
        }
}
    
module.exports = exports()
