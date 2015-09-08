var baseAPI = require('rapier')

var exports = function() {
            
    function API() {}
    
    API.prototype = Object.create(baseAPI.BaseAPI.prototype);
    API.prototype.well_known_URLs = function() {
        return ['/to-dos']
    }
    API.prototype.resourceClass = function(type_name) {
        return  type_name in classToKindMap ? classToKindMap[type_name] : baseAPI.BaseResource      
    }
    
    var api = new API();

    var api_function = function() {
        return api
    }

    function TodoList(jso, url, etag) {
        baseAPI.BaseEntity.call(this, jso, url, etag)
    }
    TodoList.prototype = Object.create(baseAPI.BaseEntity.prototype);
    TodoList.prototype.constructor = TodoList;
    TodoList.prototype._className = 'TodoList';
    TodoList.prototype.api = api_function;

    function Item(jso, url, etag) {
        baseAPI.BaseEntity.call(this, jso, url, etag)
    }
    Item.prototype = Object.create(baseAPI.BaseEntity.prototype);
    Item.prototype.constructor = Item;
    Item.prototype._className = 'Item';
    Item.prototype.api = api_function;

    function Collection(jso, url, etag) {
        baseAPI.BaseEntity.call(this, jso, url, etag)
    }
    Collection.prototype = Object.create(baseAPI.BaseCollection.prototype);
    Collection.prototype.constructor = Collection;
    Collection.prototype._className = 'Collection';
    Collection.prototype.api = api_function;

    var classToKindMap = {
        TodoList: TodoList,
        Item: Item,
        Collection: Collection
        }

    return {
        api: api,
        TodoList: TodoList,
        Item: Item,
        Collection: Collection
        }
        
}
    
module.exports = exports()
