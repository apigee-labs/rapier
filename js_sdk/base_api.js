request = require('request')

var base_api = function() {
    function BaseAPI() {}

    BaseAPI.prototype.retrieveHeaders = function() {
        return {
            'Accept': 'application/json'
            }        
        }
  
    BaseAPI.prototype.updateHeaders = function(etag) {
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'If-Match': etag
            }      
        }
  
    BaseAPI.prototype.deleteHeaders = function() {
        return {
            'Accept': 'application/json'
            }        
        }
  
    BaseAPI.prototype.retrieve = function(url, callback, entity, headers) {
        // issue a GET to retrieve a resource from the API and create an object for it
        var self = this; 
        request({
            url: url,
            headers: headers || self.retrieveHeaders()
            },
            function (error, response, body) {
                self.processResourceResult(error, response, body, url, callback, entity)
           })
    }            

    BaseAPI.prototype.update = function(url, etag, changes, callback, entity, headers) {
        var self = this; 
        request.patch({
            url: url,
            headers: headers || self.updateHeaders(),
            body: JSON.stringify(changes)
            },
            function (error, response, body) {
                self.processResourceResult(error, response, body, url, callback, entity)
           })
    }

    BaseAPI.prototype.delete = function(url, callback, entity, headers) {
        var self = this; 
        request.del({
            url: url,
            headers: headers || self.deleteHeaders()
            },
            function (error, response, body) {
                self.processResourceResult(error, response, body, url, callback, entity)
           })
    }
  
    BaseAPI.prototype.processResourceResult = function(error, response, body, url, callback, entity, location_header) {
        location_header = location_header ? location_header : 'content-location';
        if (!error) {
            if (response.statusCode == 200 || response.statusCode == 201) {
                if (location_header in response.headers) {
                    location = response.headers[location_header];
                    if ('etag' in response.headers) {
                        var etag = response.headers['etag'];
                        if ('content-type' in response.headers) {
                            var content_type = response.headers['content-type'].split(';')[0]
                            if (content_type == 'application/json') {
                                var jso = JSON.parse(body);
                                this.buildResourceFromJson(callback, entity, jso, location, etag)
                            } else {
                                callback({args: ['non-json content_type ' + response.headers['content-type']]})
                            }
                        } else {
                            callback({args: ['server did not declare content_type']})
                        }
                    } else {
                        callback({args: ['server did not provide etag']})
                    }
                } else {
                    callback({args: ['server failed to provide ' + location_header + ' header for url ' + url + 'headers' + JSON.stringify(response.headers)]})
                }
            } else {
                callback({args: ['unexpected HTTP statusCode code: ' + response.statusCode + ' url: ' + url + ' text: ' + response.text]})
            }
        } else {
            callback({args: ['http error' + error]})
        }
    }
            
    BaseAPI.prototype.buildResourceFromJson = function(callback, entity, jso, url, etag) {
        if ('kind' in jso) {
            var kind = jso.kind; 
            if (entity) {
                if (!('kind' in entity) || entity.kind == kind) {
                    entity.updateProperties(jso, url, etag);
                    callback(null, entity)
                } else {
                    callback({args: ['SDK cannot handle change of kind from' + entity.kind + ' to ' + kind]})
                } 
            } else {
                var resourceClass = this.resourceClass(kind);
                if (resourceClass) {
                    callback(null, new resourceClass(jso, url, etag))
                } else {
                    callback({args: ['no resourceClass for kind ' + kind]})
                }
            }
        } else {
            if (!!entity && entity.kind) {
                entity.updateProperties(jso, url, etag);
                callback(null, entity)
            } else {
                callback({args: ['no kind property in json ' + jso]})
            }   
        }            
    }
    
    function BaseResource(jso, url, etag) {
        this.updateProperties(jso, url, etag)
    }
    
    BaseResource.prototype.updateProperties = function(jso, url, etag) {
        if (jso) {
            for (var key in jso) {
                this[key] = jso[key]
            }
            if ('_self' in jso) {
                this._location = jso._self
            }
            this._jso = jso
        }
        if (url) {
            this._location = url
        }
        if (etag) {
            this._etag = etag
        }
    }

    BaseResource.prototype.refresh = function(callback) {
        if (!!this._location) {
            callback({args: ['no _location property' + this]})
        }
        this.api().retrieve(this._location, callback, this)

    }
  
    function BaseEntity(jso, url, etag) {
        if (url && (!jso || !etag)) {
            throw {args: ['To load an entity, use api.receive(url). This ensures that the entity class will match the server data.\n\
Creating an Entity first and loading it implies guessing the type at the end of the URL']}
        }
        this._relatedResources = {}
        BaseResource.call(this, jso, url, etag)
    }
    
    BaseEntity.prototype = Object.create(BaseResource.prototype);
    BaseEntity.prototype.constructor = BaseEntity;

    BaseEntity.prototype.getUpdateRepresentation = function() {
        var jso = '_jso' in this ? this._jso : {}
        var rslt = {}
        for (var key in this) {
            if (key.indexOf('_') !== 0 && (!(key in jso) || jso[key] != this[key])) {
                rslt[key] = this[key]
            }
        }
        return rslt
    }

    BaseEntity.prototype.update = function(callback) {
        // issue a PATCH or PUT to update this object from API
        var changes = this.getUpdateRepresentation()
        if (! ('_location' in this) || !this._location) {
            callback({args: ['this _location not set']})
        }
        if (! ('_etag' in this) || !this._location) {
            callback({args: ['self _etag not set']})
        }
        this.api().update(this._location, this._etag, changes, callback, this)
    }

    BaseEntity.prototype.delete = function(callback) {
        // issue a DELETE to remove this object from API
        if (!this._location) {
            callback({args: ['self location not set']})
        } else {
            return this.api().delete(this._location, callback, this)
        }
    }
            
    return {
      BaseAPI: BaseAPI,    
      BaseEntity: BaseEntity
    }
}

module.exports = base_api()