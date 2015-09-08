var baseAPI = require('rapier')

var exports = function() {
            
    function API() {}
    
    API.prototype = Object.create(baseAPI.BaseAPI.prototype);
    API.prototype.well_known_URLs = function() {
        return ['/dog-tracker']
    }
    API.prototype.resourceClass = function(type_name) {
        return  type_name in classToKindMap ? classToKindMap[type_name] : baseAPI.BaseResource      
    }
    
    var api = new API();

    var api_function = function() {
        return api
    }

    function Person(jso, url, etag) {
        baseAPI.BaseEntity.call(this, jso, url, etag)
    }
    Person.prototype = Object.create(baseAPI.BaseEntity.prototype);
    Person.prototype.constructor = Person;
    Person.prototype._className = 'Person';
    Person.prototype.api = api_function;

    function DogTracker(jso, url, etag) {
        baseAPI.BaseEntity.call(this, jso, url, etag)
    }
    DogTracker.prototype = Object.create(baseAPI.BaseEntity.prototype);
    DogTracker.prototype.constructor = DogTracker;
    DogTracker.prototype._className = 'DogTracker';
    DogTracker.prototype.api = api_function;

    function Dog(jso, url, etag) {
        baseAPI.BaseEntity.call(this, jso, url, etag)
    }
    Dog.prototype = Object.create(baseAPI.BaseEntity.prototype);
    Dog.prototype.constructor = Dog;
    Dog.prototype._className = 'Dog';
    Dog.prototype.api = api_function;

    function Collection(jso, url, etag) {
        baseAPI.BaseEntity.call(this, jso, url, etag)
    }
    Collection.prototype = Object.create(baseAPI.BaseCollection.prototype);
    Collection.prototype.constructor = Collection;
    Collection.prototype._className = 'Collection';
    Collection.prototype.api = api_function;

    var classToKindMap = {
        Person: Person,
        DogTracker: DogTracker,
        Dog: Dog,
        Collection: Collection
        }

    return {
        api: api,
        Person: Person,
        DogTracker: DogTracker,
        Dog: Dog,
        Collection: Collection
        }
        
}
    
module.exports = exports()
