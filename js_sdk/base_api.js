request = require('request')

var base_api = function() {
  function BaseAPI() {
  }

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
    if (!headers) {headers = this.retrieveHeaders()}
    request({
        url: url,
        headers: headers ? headers : self.retrieveHeaders()
        },
      function (error, response, body) {
        this.processResourceResult(error, response, body, url, callback, entity)
      })
   }            

  BaseAPI.prototype.processResourceResult = function(error, response, body, url, callback, entity, location_header) {
    location_header = location_header ? location_header : 'Content-Location';
    if (!error) {
      if (response.statusCode == 200 || response.statusCode == 201) {
        if (location_header in response.headers) {
          location = response.headers[location_header];
          if ('ETag' in response.headers) {
            var etag = response.headers['ETag'];
            if ('Content-Type' in response.headers) {
              var content_type = response.headers['Content-Type'].split(';')[0]
              if (content_type == 'application/json') {
                var jso = JSON.parse(body);
                this.buildResourceFromJson(callback, jso, entity, location, etag)
              } else {
                callback({args: ['non-json content_type ' + response.headers['Content-Type']]})
              }
            } else {
              callback({args: ['server did not declare content_type']})
            }
          } else {
            callback({args: ['server did not provide etag']})
          }
        } else {
          callback({args: ['server failed to provide ' + location_header + ' header for url ' + url]})
        }
      } else {
        callback({args: ['unexpected HTTP statusCode code: ' + response.statusCode + ' url: ' + url + ' text: ' + response.text]})
      }
    } else {
      callback({args: ['http error' + error]})
    }
  }
          
  BaseAPI.prototype.buildResourceFromJson = function(callback, jso, entity, url, etag) {
    if ('kind' in jso) {
      var kind = jso.kind; 
      if (entity) {
        if (!('kind' in entity) || entity.kind == kind) {
          entity.update_attrs(jso, url, etag);
          callback(null, entity)
        } else {
          callback({args: ['SDK cannot handle change of kind from' + entity.kind + ' to ' + kind]})
        } 
      } else {
        var resource_class = self.resource_class(kind);
        if (resource_class) {
          callback(null, resource_class(jso, url, etag))
        } else {
          callback({args: ['no resource_class for kind ' + kind]})
        }
      }
    } else {
      if (!!entity && entity.kind) {
        entity.update_attrs(url, jso, etag);
        callback(null, entity)
      } else {
        callback({args: ['no kind property in json ' + jso]})
      }   
    }            
  }

  return {
    BaseAPI: BaseAPI,    
  }
}

module.exports = base_api()