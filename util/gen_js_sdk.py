import yaml, sys

class ClientGenerator(object):

    def set_rapier_spec_from_filename(self, filename):
        with open(filename) as f:
            self.rapier_spec = yaml.load(f.read())

    def client_from_rapier(self, filename= None):
        spec = self.rapier_spec
        if filename:
            self.set_rapier_spec_from_filename(filename)
            
        entities = spec.get('entities',{})
        well_known_urls = [as_list(entity.get('wellKnownURLs')) for entity in entities.itervalues() if 'wellKnownURLs' in entity]
        well_known_urls = [url for urls in well_known_urls for url in urls]
        
        print '''var baseAPI = require('rapier')

var exports = function() {
            
    function API() {}
    
    API.prototype = Object.create(baseAPI.BaseAPI.prototype);
    API.prototype.well_known_URLs = function() {
        return %s
    }
    API.prototype.resourceClass = function(type_name) {
        return  type_name in classToKindMap ? classToKindMap[type_name] : baseAPI.BaseResource      
    }
    
    var api = new API();

    var api_function = function() {
        return api
    }''' % well_known_urls
    
        class_template = '''
    function {0}(url, jso, etag) {{
        baseAPI.BaseEntity.call(this, url, jso, etag)
    }}
    {0}.prototype = Object.create(baseAPI.{1}.prototype);
    {0}.prototype.constructor = {0};
    {0}.prototype._className = '{0}';
    {0}.prototype.api = api_function;'''
        
        for entity_name in entities:
            print class_template.format(entity_name, 'BaseEntity')

        print class_template.format('Collection', 'BaseCollection')
        
        map_entries = ["{0}: {0}".format((entity_name)) for entity_name in entities] + ["Collection: Collection"]
        
        print '''
    var classToKindMap = {
        %s
        }''' % ',\n        '.join(map_entries)

        print '''
    return {
        %s
        }
        
}
    
module.exports = exports()''' % ',\n        '.join(["api: api"] + map_entries)
        
def as_list(value, separator = None):
    if isinstance(value, basestring):
        if separator:
            result = [item.strip() for item in value.split(separator)]
        else:
            result = value.split()
    else:
        if isinstance(value, (list, tuple)):
            result = value
        else:
            result = [value]
    return result
    
def main(args):
    generator = ClientGenerator()
    generator.set_rapier_spec_from_filename(args[0])
    generator.client_from_rapier()
        
if __name__ == "__main__":
    main(sys.argv[1:])