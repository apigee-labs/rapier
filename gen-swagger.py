import yaml, sys

class Swagger_generator(object):

    swagger = dict()
    interfaces = dict()
    paths = dict()
    definitions = dict()
    
    def swagger_from_chutzpah(self, filename):
        with open(filename) as f:
           spec = yaml.load(f.read())
           patterns = spec.get('patterns')
    
           if 'entities' in spec:
               entities = spec['entities']
               self.swagger['definitions'] = self.definitions
               self.definitions['ErrorResponse'] = self.build_error_definition()
               self.definitions['Collection'] = self.build_collection_definition()
               for entity_name, entity_spec in entities.iteritems():
                   definition = {}
                   self.definitions[entity_name] = definition
                   if 'properties' in entity_spec:
                       definition['properties'] = entity_spec['properties'].copy()
               for entity_name, entity_spec in entities.iteritems():
                   if 'query_paths' in entity_spec:
                       query_paths = entity_spec['query_paths'][:]
                       if 'relationships' in entity_spec:
                           definition = self.definitions[entity_name]
                           properties = definition.setdefault('properties',dict())
                           for rel_name, rel_spec in entity_spec['relationships'].iteritems():
                               rel_def = {}
                               properties[rel_name] = rel_def
                               rel_def['type'] = 'string'
                               if 'well_known_URL' in entity_spec:
                                   paths = self.swagger.setdefault('paths', self.paths)
                                   paths[entity_spec['well_known_URL']] = self.get_entity_interface(entity_name)
                                   self.add_query_paths(entity_spec['well_known_URL'], query_paths, spec, [[rel_name, rel_spec, None, None]])
                       if len(query_paths) > 0:
                           for query_path in query_paths:
                               print 'query path not valid or listed more than once: %s' % query_path
                           return 'Error'
                                       
           return self.swagger
           
    def build_error_definition(self):
        return {'required': ['message'], 'properties': {'message': {'type': 'string'}}}
    
    def build_collection_definition(self):
        return {'required': ['selfLink', 'id', 'type'], 'properties': {'selfLink': {'type': 'string'}, 'id': {'type': 'string'}, 'type': {'type': 'string'}}}
        
    def add_query_paths(self, well_known_URL, query_paths, chutzpah_spec, rel_tuples):
        rel_tuple = rel_tuples[-1]
        rel_spec = rel_tuple[1]
        type_refs = rel_spec['type'] if isinstance(rel_spec['type'], list) else [rel_spec['type']]
        for type_ref in type_refs:
            ref_parts = type_ref.split('/')
            entity = chutzpah_spec
            for ref_part in ref_parts[1:]:
                entity = entity[ref_part]
            rel_tuple[2] = ref_part
            rel_tuple[3] = entity
            if 'relationships' in entity:
                for rel_name, rel_spec in entity['relationships'].iteritems():
                    if len([rel_tuple for rel_tuple in rel_tuples if rel_tuple[1] is rel_spec]) == 0:
                        rel_tuples.append([rel_name, rel_spec, None, None])
                        self.add_query_paths(well_known_URL, query_paths, chutzpah_spec, rel_tuples)
            rel_path = '/'.join([rel_tuple[0] for rel_tuple in rel_tuples])
            if rel_path in query_paths:
                self.emit_query_path(well_known_URL, rel_tuples)
                query_paths.remove(rel_path)
        rel_tuples.pop()
        
    def emit_query_path(self, well_known_URL, rel_tuples):
        rel_tuple = rel_tuples[-1]
        rel_spec = rel_tuple[1]
        multiplicity = rel_spec.get('multiplicity')
        multivalued = multiplicity and multiplicity.split(':')[-1] == 'n'
    
        path = '/'.join([self.path_segment(rel_tuple) for rel_tuple in rel_tuples])
        sep = '' if well_known_URL.endswith('/') else '/'
        abs_path = sep.join((well_known_URL, path))
        path_spec = self.get_entity_interface(rel_tuples[-1][2])
        self.paths[abs_path] = path_spec
        if multivalued:
            path = '/'.join([self.path_segment(rel_tuple, inx==len(rel_tuples)-1) for inx, rel_tuple in enumerate(rel_tuples)])
            sep = '' if well_known_URL.endswith('/') else '/'
            abs_path = sep.join((well_known_URL, path))
            path_spec = self.get_relationship_interface(rel_tuples[-1][0])
            self.paths[abs_path] = path_spec
            
    def get_entity_interface(self, entity_name):
        if entity_name in self.interfaces:
            return self.interfaces[entity_name]
        else:
            self.interfaces[entity_name] = self.build_entity_interface(entity_name)
            return self.interfaces[entity_name]

    def build_entity_interface(self, entity_name):
        path_spec = {'get': {'responses': {'200': {'schema': self.definitions[entity_name]}, 
                                       'default': {'schema': self.definitions['ErrorResponse']}}}}
        return path_spec
    
    def get_relationship_interface(self, relationship_name):
        relationship_name = 'Collection'
        if relationship_name in self.interfaces:
            return self.interfaces[relationship_name]
        else:
            self.interfaces[relationship_name] = self.build_relationship_interface(relationship_name)
            return self.interfaces[relationship_name]

    def build_relationship_interface(self, relationship_name):
        path_spec = {'get': {'responses': {'200': {'schema': self.definitions['Collection']}, 
                                       'default': {'schema': self.definitions['ErrorResponse']}}}}
        return path_spec
    
    def path_segment(self, rel_tuple, allow_multivalued = False):
        rel_name = rel_tuple[0]
        rel_spec = rel_tuple[1]
        entity_name = rel_tuple[2]
        if allow_multivalued:
            dereference_multivalued = False
        else:
            multiplicity = rel_spec.get('multiplicity')
            dereference_multivalued = multiplicity and multiplicity.split(':')[-1] == 'n'
        return '%s;{%s_id}' % (rel_name, entity_name) if dereference_multivalued else rel_name

def main(args):
    generator = Swagger_generator()
    print yaml.dump(generator.swagger_from_chutzpah(*args[1:]))
        
if __name__ == "__main__":
    main(sys.argv)