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
        
        print '''
from rapier.py.base_api import BaseAPI, BaseResource, BaseEntity, BaseCollection

class API(BaseAPI):
    def well_known_URLs(self):
        return %s
    def resource_class(self, type_name):
        return classToKindMap.get(type_name, BaseResource)

api = API()

class APIClass(object):
    def api(self):
        return api''' % well_known_urls
        
        for entity_name in entities:
            print '''
class %s(BaseEntity, APIClass):            
    pass''' % entity_name

        print '''
class Collection(BaseCollection, APIClass):            
    pass'''
    
        map_values = ["'{0}': {0}".format((entity_name)) for entity_name in entities] + ["'Collection': Collection"]

        print '''
classToKindMap = {
    %s
    }''' % ',\n    '.join(map_values)
    
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