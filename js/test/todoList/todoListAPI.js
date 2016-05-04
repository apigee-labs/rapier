var baseAPI = require('./../../../js/base_api')

var exports = function() {

    function API() {}
    
    API.prototype = Object.create(baseAPI.BaseAPI.prototype);
    API.prototype.wellKnownURLs = function() {
        return ['/to-dos']
    }
    API.prototype.resourceClass = function(type_name) {
        return  type_name in classToKindMap ? classToKindMap[type_name] : baseAPI.BaseResource      
    }
    
    var api = new API();

    var api_function = function() {
        return api
    }

    function TodoList(url, jso, etag) {
        baseAPI.BaseEntity.call(this, url, jso, etag)
    }
    TodoList.prototype = Object.create(baseAPI.BaseEntity.prototype);
    TodoList.prototype.constructor = TodoList;
    TodoList.prototype._className = 'TodoList';
    TodoList.prototype.api = api_function;
    
    function Item(url, jso, etag) {
        baseAPI.BaseEntity.call(this, url, jso, etag)
    }
    Item.prototype = Object.create(baseAPI.BaseEntity.prototype);
    Item.prototype.constructor = Item;
    Item.prototype._className = 'Item';
    Item.prototype.api = api_function;
        
    function Collection(url, jso, etag) {
        baseAPI.BaseCollection.call(this, url, jso, etag)
    }
    Collection.prototype = Object.create(baseAPI.BaseCollection.prototype);
    Collection.prototype.constructor = Collection;
    Collection.prototype._className = 'Collection';
    Collection.prototype.api = api_function;
            
    var classToKindMap = {
        TodoList: TodoList,
        Item: Item,
        Collection: Collection
        };
        
    return {
        api: api,
        TodoList: TodoList,
        Item: Item,
        Collection: Collection   
        }

}
    
module.exports = exports()