import yaml, sys

class Swagger_generator(object):

    def __init__(self):
        self.swagger = {
            'swagger': '2.0'
            }
        self.paths = dict()
        self.definitions = self.build_standard_definitions()
        self.swagger['definitions'] = self.definitions
        self.responses = self.build_standard_responses()
        self.swagger['responses'] = self.responses
        self.collection_get = self.build_collection_get()
    
    def swagger_from_chutzpah(self, filename):
        with open(filename) as f:
           spec = yaml.load(f.read())
           patterns = spec.get('patterns')
           self.swagger['info'] = spec['info'].copy()
    
           if 'entities' in spec:
               entities = spec['entities']
               self.swagger['definitions'] = self.definitions
               for entity_name, entity_spec in entities.iteritems():
                   definition = {}
                   self.definitions[entity_name] = definition
                   if 'properties' in entity_spec:
                       definition['properties'] = entity_spec['properties'].copy()
               for entity_name, entity_spec in entities.iteritems():
                   if 'query_paths' in entity_spec:
                       query_paths = entity_spec['query_paths'][:]
                       if 'well_known_URL' in entity_spec:
                           paths = self.swagger.setdefault('paths', self.paths)
                           paths[entity_spec['well_known_URL']] = self.build_entity_interface([[None, None, entity_name, entity_spec]])
                       if 'relationships' in entity_spec:
                           definition = self.definitions[entity_name]
                           properties = definition.setdefault('properties',dict())
                           for rel_name, rel_spec in entity_spec['relationships'].iteritems():
                               rel_def = {}
                               properties[rel_name] = rel_def
                               rel_def['type'] = 'string'
                               if 'well_known_URL' in entity_spec:
                                   rel_tuples = [[rel_name, rel_spec, None, None]]
                                   self.add_query_paths(entity_spec['well_known_URL'], query_paths, spec, rel_tuples)
                       if len(query_paths) > 0:
                           for query_path in query_paths:
                               print 'query path not valid or listed more than once: %s' % query_path
                           return 'Error'
                                       
           return self.swagger
                
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
        path_spec = self.build_entity_interface(rel_tuples)
        self.paths[abs_path] = path_spec
        if multivalued:
            path = '/'.join([self.path_segment(rel_tuple, inx==len(rel_tuples)-1) for inx, rel_tuple in enumerate(rel_tuples)])
            sep = '' if well_known_URL.endswith('/') else '/'
            abs_path = sep.join((well_known_URL, path))
            path_spec = self.build_relationship_interface(rel_tuples)
            self.paths[abs_path] = path_spec
            
    def build_entity_interface(self, rel_tuples):
        entity_name = rel_tuples[-1][2]
        entity_spec = rel_tuples[-1][3]
        response_200 = {
            'description': 'successful',
            'schema': self.global_definition_ref(entity_name),
            'headers': {
                'Content-Location': {
                    'type': 'string',
                    'description': 'perma-link URL of resource'
                    },
                'ETag': {
                    'description': 'this value must be echoed in the If-Match header of every PATCH',
                    'type': 'string'
                    }
                }
            }
        path_spec = {
            'get': {
                'description': 'Retrieve %s %s' % ('an' if entity_name[0].lower() in 'aeiou' else 'a', entity_name),
                'responses': {
                    '200': response_200, 
                    '401': self.global_response_ref('401'), 
                    '403': self.global_response_ref('403'), 
                    '404': self.global_response_ref('404'), 
                    '406': self.global_response_ref('406'), 
                    'default': self.global_response_ref('default')
                    }
                }
            }
        read_only = 'well_known_URL' in entity_spec
        if not read_only:
            path_spec['patch']= {
                'description': 'Update %s %s' % ('an' if entity_name[0].lower() in 'aeiou' else 'a', entity_name),
                'responses': { 
                    '200': response_200, 
                    '400': self.global_response_ref('400'),
                    '401': self.global_response_ref('401'), 
                    '403': self.global_response_ref('403'), 
                    '404': self.global_response_ref('404'), 
                    '406': self.global_response_ref('406'), 
                    '409': self.global_response_ref('409'),
                    'default': self.global_response_ref('default')
                    }
                }
            path_spec['delete'] = {
                'description': 'Delete %s %s' % ('an' if entity_name[0].lower() in 'aeiou' else 'a', entity_name),
                'responses': {
                    '200': response_200, 
                    '400': self.global_response_ref('400'),
                    '401': self.global_response_ref('401'), 
                    '403': self.global_response_ref('403'), 
                    '404': self.global_response_ref('404'), 
                    '406': self.global_response_ref('406'), 
                    'default': self.global_response_ref('default')
                    }
                }
        if rel_tuples[-1][0]:
            parameters = self.build_parameters(rel_tuples)
            if parameters:
                path_spec['parameters'] = parameters
        return path_spec
    
    def build_relationship_interface(self, rel_tuples):
        relationship_name = rel_tuples[-1][0]
        entity_name = rel_tuples[-1][2]
        path_spec = {
            'get': self.collection_get,
            'post': {
                'responses': {
                    '201': {
                        'description': 'Create a new %s' % entity_name,
                        'schema': self.global_definition_ref(entity_name),
                        'headers': {
                            'Location': {
                                'type': 'string',
                                'description': 'perma-link URL of newly-created %s'  % entity_name
                                }
                            }
                        }, 
                    '303': self.global_response_ref('303'),
                    '400': self.global_response_ref('400'),
                    '401': self.global_response_ref('401'), 
                    '403': self.global_response_ref('403'), 
                    '404': self.global_response_ref('404'), 
                    '406': self.global_response_ref('406'), 
                    'default': self.global_response_ref('default')
                    }                
                }
            }
        parameters = self.build_parameters(rel_tuples[:-1]) 
        if parameters:
            path_spec['parameters'] = parameters
        return path_spec

    def global_response_ref(self, key):
        return {'$ref': '#/responses/%s' % key}
    
    def global_definition_ref(self, key):
        return {'$ref': '#/definitions/%s' % key}
    
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
        
    def build_parameters(self, rel_tuples):
        result = []
        for rel_tuple in rel_tuples:
            rel_name = rel_tuple[0]
            rel_spec = rel_tuple[1]
            entity_name = rel_tuple[2]
            multiplicity = rel_spec.get('multiplicity')
            multivalued = multiplicity and multiplicity.split(':')[-1] == 'n'
            if multivalued:
                result.append( {
                    'name': '%s_id' % entity_name,
                    'in': 'path',
                    'type': 'string',
                    'description': "Specifies which '%s' entity from multi-valued relationship '%s'" % (entity_name, rel_name),
                    'required': True
                    } )
        return result
          
    def build_standard_responses(self):
        return {
            '303': {
                'description': 'See other. Server is redirecting client to a different resource',
                'headers': {
                    'Location': {
                        'type': 'string',
                        'description': 'URL of other resource'
                        }
                    }
                },
            '400': {
                'description': 'Bad Request. Client request in error',
                'schema': self.global_definition_ref('ErrorResponse')
                },
            '401': {
                'description': 'Unauthorized. Client authentication token missing from request',
                'schema': self.global_definition_ref('ErrorResponse')
                }, 
            '403': {
                'description': 'Forbidden. Client authentication token does not permit this method on this resource',
                'schema': self.global_definition_ref('ErrorResponse')
                }, 
            '404': {
                'description': 'Not Found. Resource not found',
                'schema': self.global_definition_ref('ErrorResponse')
                }, 
            '406': {
                'description': 'Not Acceptable. Requested media type not availalble',
                'schema': self.global_definition_ref('ErrorResponse')
                }, 
            '409': {
                'description': 'Conflict. Value provided in If-Match header does not match current ETag value of resource',
                'schema': self.global_definition_ref('ErrorResponse')
                }, 
            'default': {
                'description': '5xx errors and other stuff',
                'schema': self.global_definition_ref('ErrorResponse')
                }
            }
        
    def build_collection_get(self):
        return {
            'responses': {
                '200': {
                    'description': 'description',
                    'schema': self.global_definition_ref('Collection'),
                    'headers': {
                        'Content-Location': {
                            'type': 'string',
                            'description': 'perma-link URL of collection'
                            }
                        }
                    }, 
                '303': self.global_response_ref('403'),
                '401': self.global_response_ref('401'), 
                '403': self.global_response_ref('403'), 
                '404': self.global_response_ref('404'), 
                '406': self.global_response_ref('406'), 
                'default': self.global_response_ref('default')
                }
            }
 
    def build_standard_definitions(self):
        return {
            'ErrorResponse': build_error_definition(),
            'Collection': build_collection_definition()
            }
    
def build_error_definition():
    return {
        'properties': {
            'message': {
                'type': 'string'
                }
            }
        }

def build_collection_definition():
    return {
        'properties': {
            'selfLink': {
                'type': 'string'
                }, 
            'id': {
                'type': 'string'
                }, 
            'type': {
                'type': 'string'
                },
            'contents_type': {
                'type': 'string'
                }
            }
        }
   

def main(args):
    generator = Swagger_generator()
    print yaml.dump(generator.swagger_from_chutzpah(*args[1:]), default_flow_style=False)
        
if __name__ == "__main__":
    main(sys.argv)