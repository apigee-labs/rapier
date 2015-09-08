var baseAPI = require('rapier')

var exports = function() {
            
    function API() {}
    
    API.prototype = Object.create(baseAPI.BaseAPI.prototype);
    API.prototype.well_known_URLs = function() {
        return ['/message']
    }
    API.prototype.resourceClass = function(type_name) {
        return  type_name in classToKindMap ? classToKindMap[type_name] : baseAPI.BaseResource      
    }
    
    var api = new API();

    var api_function = function() {
        return api
    }

    function HelloMessage(jso, url, etag) {
        baseAPI.BaseEntity.call(this, jso, url, etag)
    }
    HelloMessage.prototype = Object.create(baseAPI.BaseEntity.prototype);
    HelloMessage.prototype.constructor = HelloMessage;
    HelloMessage.prototype._className = 'HelloMessage';
    HelloMessage.prototype.api = api_function;

    function Collection(jso, url, etag) {
        baseAPI.BaseEntity.call(this, jso, url, etag)
    }
    Collection.prototype = Object.create(baseAPI.BaseCollection.prototype);
    Collection.prototype.constructor = Collection;
    Collection.prototype._className = 'Collection';
    Collection.prototype.api = api_function;

    var classToKindMap = {
        HelloMessage: HelloMessage,
        Collection: Collection
        }

    return {
        api: api,
        HelloMessage: HelloMessage,
        Collection: Collection
        }
        
}
    
module.exports = exports()
