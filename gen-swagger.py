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
        self.header_parameters = self.build_standard_header_parameters()
        self.swagger['parameters'] = self.header_parameters
        self.collection_get = self.build_collection_get()
    
    def swagger_from_apier(self, filename):
        with open(filename) as f:
            spec = yaml.load(f.read())
            self.apier_spec = spec
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
                    if 'well_known_URL' in entity_spec:
                        paths = self.swagger.setdefault('paths', self.paths)
                        paths[entity_spec['well_known_URL']] = self.build_entity_interface([{'target_entity': entity_name}])
                    else:
                        if 'query_paths' in entity_spec:
                            print 'error: query_path may only be set if well_known_URL is also set'
                            return None
                    rel_property_specs = self.get_relationship_property_specs(spec, entity_name)
                    if len(rel_property_specs) > 0:
                        definition = self.definitions[entity_name]
                        properties = definition.setdefault('properties',dict())
                        for rel_name in {rel_property_spec['property_name'] for rel_property_spec in rel_property_specs}:
                            properties[rel_name] = {'type': 'string'}
                    if 'query_paths' in entity_spec:
                        query_paths = entity_spec['query_paths'][:]
                        for rel_property_spec in rel_property_specs:
                            if 'well_known_URL' in entity_spec:
                                rel_property_spec_stack = [rel_property_spec]
                                self.add_query_paths(entity_spec['well_known_URL'], query_paths, spec, rel_property_spec_stack)
                        if len(query_paths) > 0:
                            for query_path in query_paths:
                                print 'query path not valid or listed more than once: %s' % query_path
                            return 'Error'                                     
            return self.swagger
 
    def get_relationship_property_specs(self, spec, entity_name):
        result = []
        def add_type(one_end, other_end):
            if 'property' in one_end:
                result.append({
                    'property_name': one_end['property'],
                    'multiplicity': one_end['multiplicity'], 
                    'source_entity': one_end['entity'],
                    'target_entity': other_end['entity']
                    })
           
        if 'relationships' in spec:
            relationships = spec['relationships']
            for relationship in relationships.itervalues():
                if relationship['one_end']['entity'] == entity_name:
                    add_type(relationship['one_end'], relationship['other_end'])
                elif relationship['other_end']['entity'] == entity_name:
                    add_type(relationship['other_end'], relationship['one_end'])
        return result
        
    def add_query_paths(self, well_known_URL, query_paths, apier_spec, rel_property_spec_stack):
        rel_property_spec = rel_property_spec_stack[-1]
        target_entity = rel_property_spec['target_entity']
        entity_spec = apier_spec['entities'][target_entity]
        rel_property_specs = self.get_relationship_property_specs(apier_spec, target_entity)
        for rel_spec in rel_property_specs:
            if rel_spec not in rel_property_spec_stack:
                rel_property_spec_stack.append(rel_spec)
                self.add_query_paths(well_known_URL, query_paths, apier_spec, rel_property_spec_stack)
        rel_path = '/'.join([rel_property_spec['property_name'] for rel_property_spec in rel_property_spec_stack])
        if rel_path in query_paths:
            self.emit_query_path(well_known_URL, rel_property_spec_stack)
            query_paths.remove(rel_path)
        rel_property_spec_stack.pop()
        
    def emit_query_path(self, well_known_URL, rel_property_spec_stack):
        rel_property_spec = rel_property_spec_stack[-1]
        multiplicity = rel_property_spec.get('multiplicity')
        multivalued = multiplicity and multiplicity.split(':')[-1] == 'n'
    
        path = '/'.join([self.path_segment(rel_property_spec) for rel_property_spec in rel_property_spec_stack])
        sep = '' if well_known_URL.endswith('/') else '/'
        abs_path = sep.join((well_known_URL, path))
        path_spec = self.build_entity_interface(rel_property_spec_stack)
        self.paths[abs_path] = path_spec
        if multivalued:
            path = '/'.join([self.path_segment(rel_property_spec, inx==len(rel_property_spec_stack)-1) for inx, rel_property_spec in enumerate(rel_property_spec_stack)])
            sep = '' if well_known_URL.endswith('/') else '/'
            abs_path = sep.join((well_known_URL, path))
            path_spec = self.build_relationship_interface(rel_property_spec_stack)
            self.paths[abs_path] = path_spec
            
    def build_entity_interface(self, rel_property_spec_stack):
        rel_property_spec = rel_property_spec_stack[-1]
        entity_name = rel_property_spec['target_entity']
        entity_spec = self.apier_spec['entities'][entity_name]
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
                'parameters': [{'$ref': '#/parameters/Accept'}],
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
                'parameters': [{'$ref': '#/parameters/If-Match'}],
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
        if 'property_name' in rel_property_spec:
            parameters = self.build_parameters(rel_property_spec_stack)
            if parameters:
                path_spec['parameters'] = parameters
        return path_spec
    
    def build_relationship_interface(self, rel_property_spec_stack):
        rel_property_spec = rel_property_spec_stack[-1]
        relationship_name = rel_property_spec['property_name']
        entity_name = rel_property_spec['target_entity']
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
        parameters = self.build_parameters(rel_property_spec_stack[:-1]) 
        if parameters:
            path_spec['parameters'] = parameters
        return path_spec

    def global_response_ref(self, key):
        return {'$ref': '#/responses/%s' % key}
    
    def global_definition_ref(self, key):
        return {'$ref': '#/definitions/%s' % key}
    
    def path_segment(self, rel_property_spec, allow_multivalued = False):
        rel_name = rel_property_spec['property_name']
        entity_name = rel_property_spec['target_entity']
        if allow_multivalued:
            dereference_multivalued = False
        else:
            multiplicity = rel_property_spec.get('multiplicity')
            dereference_multivalued = multiplicity and multiplicity.split(':')[-1] == 'n'
        return '%s;{%s_id}' % (rel_name, entity_name) if dereference_multivalued else rel_name
        
    def build_parameters(self, rel_property_spec_stack):
        result = []
        for rel_property_spec in rel_property_spec_stack:
            rel_name = rel_property_spec['property_name']
            entity_name = rel_property_spec['target_entity']
            multiplicity = rel_property_spec.get('multiplicity')
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
            
    def build_standard_header_parameters(self):
        return {
            'If-Match': {
                'name': 'If-Match',
                'in': 'header',
                'type': 'string',
                'description': 'specifies the last known ETag value of the resource being modified',
                'required': True
                },
            'Accept': {
                'name': 'Accept',
                'in': 'header',
                'type': 'string',
                'description': 'specifies the requested media type - required',
                'required': True
                }
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
    print yaml.dump(generator.swagger_from_apier(*args[1:]), default_flow_style=False)
        
if __name__ == "__main__":
    main(sys.argv)