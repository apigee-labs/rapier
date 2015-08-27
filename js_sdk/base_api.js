require('request')

var base_api = function() {
  function BaseAPI() {
  }

  BaseAPI.prototype.retrieve_headers = function() {
    return {
      'Accept': 'application/json'
    }        
  }

  BaseAPI.prototype.update_headers = function(etag) {
    return {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'If-Match': etag
    }      
  }

  BaseAPI.prototype.delete_headers = function() {
    return {
      'Accept': 'application/json'
    }        
  }

  return {
    BaseAPI: BaseAPI,    
  }
}

module.exports = base_api()