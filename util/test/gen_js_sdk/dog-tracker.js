var baseAPI = require('rapier')

var exports = function() {
            
    function API() {}
    
    API.prototype = Object.create(baseAPI.BaseAPI.prototype);
    API.prototype.wellKnownURLs = function() {
        return ['/']
    }
    API.prototype.resourceClass = function(type_name) {
        return  type_name in classToKindMap ? classToKindMap[type_name] : baseAPI.BaseResource      
    }
    
    var api = new API();

    var api_function = function() {
        return api
    }

    function Person(url, jso, etag) {
        baseAPI.BaseEntity.call(this, url, jso, etag)
    }
    Person.prototype = Object.create(baseAPI.BaseEntity.prototype);
    Person.prototype.constructor = Person;
    Person.prototype._className = 'Person';
    Person.prototype.api = api_function;

    function DogTracker(url, jso, etag) {
        baseAPI.BaseEntity.call(this, url, jso, etag)
    }
    DogTracker.prototype = Object.create(baseAPI.BaseEntity.prototype);
    DogTracker.prototype.constructor = DogTracker;
    DogTracker.prototype._className = 'DogTracker';
    DogTracker.prototype.api = api_function;

    function Dog(url, jso, etag) {
        baseAPI.BaseEntity.call(this, url, jso, etag)
    }
    Dog.prototype = Object.create(baseAPI.BaseEntity.prototype);
    Dog.prototype.constructor = Dog;
    Dog.prototype._className = 'Dog';
    Dog.prototype.api = api_function;

    function Resource(url, jso, etag) {
        baseAPI.BaseEntity.call(this, url, jso, etag)
    }
    Resource.prototype = Object.create(baseAPI.BaseEntity.prototype);
    Resource.prototype.constructor = Resource;
    Resource.prototype._className = 'Resource';
    Resource.prototype.api = api_function;

    function PersistentResource(url, jso, etag) {
        baseAPI.BaseEntity.call(this, url, jso, etag)
    }
    PersistentResource.prototype = Object.create(baseAPI.BaseEntity.prototype);
    PersistentResource.prototype.constructor = PersistentResource;
    PersistentResource.prototype._className = 'PersistentResource';
    PersistentResource.prototype.api = api_function;

    function Collection(url, jso, etag) {
        baseAPI.BaseEntity.call(this, url, jso, etag)
    }
    Collection.prototype = Object.create(baseAPI.BaseCollection.prototype);
    Collection.prototype.constructor = Collection;
    Collection.prototype._className = 'Collection';
    Collection.prototype.api = api_function;

    var classToKindMap = {
        Person: Person,
        DogTracker: DogTracker,
        Dog: Dog,
        Resource: Resource,
        PersistentResource: PersistentResource,
        Collection: Collection
        }

    return {
        api: api,
        Person: Person,
        DogTracker: DogTracker,
        Dog: Dog,
        Resource: Resource,
        PersistentResource: PersistentResource,
        Collection: Collection
        }
        
}
    
module.exports = exports()
