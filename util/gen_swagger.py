#!/usr/bin/env python 

import yaml, sys, getopt
from collections import OrderedDict

class PresortedList(list):
    def sort(self, *args, **kwargs):
        pass

class PresortedOrderedDict(OrderedDict):
    def items(self, *args, **kwargs):
        return PresortedList(OrderedDict.items(self, *args, **kwargs))

class SwaggerGenerator(object):

    def __init__(self):
        pass

    def set_rapier_spec_from_filename(self, filename):
        with open(filename) as f:
            self.rapier_spec = yaml.load(f.read())
            
    def set_opts(self, opts):
        self.opts = opts
        self.opts_keys = [k for k,v in opts]
        self.yaml_merge = '--yaml-merge' in self.opts_keys or '-m' in self.opts_keys
        self.include_impl = '--include-impl' in self.opts_keys or '-i' in self.opts_keys

    def swagger_from_rapier(self, filename= None):
        if filename:
            self.set_rapier_spec_from_filename(filename)
        spec = self.rapier_spec 
        self.conventions = spec['conventions'] if 'conventions' in spec else {}     
        self.selector_location = self.conventions['selector_location'] if 'selector_location' in self.conventions else 'path-segment'
        if not self.selector_location in ['path-segment', 'path-parameter']:
            print 'error: invalid value for selector_location: %s' % self.selector_location
            return None
        patterns = spec.get('patterns')
        self.swagger = PresortedOrderedDict()
        self.swagger['swagger'] = '2.0'
        self.swagger['info'] = dict()
        self.paths = dict()
        self.uris = dict()
        if 'consumes' in spec:
            self.swagger['consumes'] = as_list(spec.get('consumes'))
        else:
            self.swagger['consumes'] = ['application/json']
        if 'produces' in spec:
            self.swagger['produces'] = as_list(spec.get('produces'))
        else:
            self.swagger['produces'] = ['application/json']
        self.definitions = self.build_standard_definitions()
        self.swagger['definitions'] = self.definitions
        self.mutable_definitions = dict()
        self.responses = self.build_standard_responses()
        self.swagger['paths'] = self.paths
        self.swagger['x-uris'] = self.uris
        self.header_parameters = self.build_standard_header_parameters()
        self.swagger['parameters'] = self.header_parameters
        self.swagger['responses'] = dict()
        self.entity_specs = {}
        self.response_sets = self.build_standard_response_sets()
        self.methods = self.build_standard_methods()
        self.swagger['info']['title'] = spec['title'] if 'title' in spec else 'untitled'
        self.swagger['info']['version'] = spec['version'] if 'version' in spec else 'initial'

        if 'entities' in spec:
            entities = spec['entities']
            self.swagger['definitions'] = self.definitions
            for entity_name, entity_spec in entities.iteritems():
                mutable_definition = dict()
                if 'allOf' in entity_spec:
                    mutable_definition['allOf'] = [{key: '%sProperties' % value.replace('entities', 'definitions') for key, value in ref.iteritems()} for ref in entity_spec['allOf']]
                structured = 'type' not in entity_spec
                if structured:
                    definition = dict()
                    if 'allOf' in entity_spec:
                        definition['allOf'] = [{key: value.replace('entities', 'definitions') for key, value in ref.iteritems()} for ref in entity_spec['allOf']]
                    else:
                        definition['allOf'] = list()                      
                    definition['allOf'].append(self.mutable_definition_ref(entity_name))
                    if 'properties' in entity_spec:
                        mutable_definition['properties'] = entity_spec['properties'].copy()
                    self.definitions['%sProperties' % entity_name] = mutable_definition
                else:
                    if 'properties' in spec:
                        sys.exit('error: unstructured entities must not have properties')
                    definition = dict()
                    definition['type'] = entity_spec['type']
                self.definitions[entity_name] = definition
            for entity_name, entity_spec in entities.iteritems():
                if 'well_known_URLs' in entity_spec:
                    for well_known_URL in as_list(entity_spec['well_known_URLs']):
                        self.swagger['paths'][well_known_URL] = self.get_entity_interface([Well_known_URL_Spec(well_known_URL, entity_name)])
                rel_property_specs = self.get_relationship_property_specs(entity_name)
                if len(rel_property_specs) > 0:
                    definition = self.definitions[entity_name]
                    structured = 'type' not in entity_spec
                    rel_prop_spec_dict = {}
                    for rel_property_spec in rel_property_specs:
                        rel_prop_name = rel_property_spec.property_name
                        if rel_prop_name in rel_prop_spec_dict:
                            rel_prop_spec_dict[rel_prop_name].append(rel_property_spec)
                        else:
                            rel_prop_spec_dict[rel_prop_name] = [rel_property_spec]
                    for rel_prop_name, rel_prop_specs in rel_prop_spec_dict.iteritems():
                        if structured:   
                            if rel_prop_specs[0].is_multivalued():
                                properties = self.definitions[entity_name].setdefault('properties', dict())
                                properties[rel_prop_name] = self.build_relationship_property_spec(rel_prop_name, rel_prop_specs)
                            else:
                                mutable_properties = self.definitions[entity_name].setdefault('properties', dict())
                                mutable_properties[rel_prop_name] = self.build_relationship_property_spec(rel_prop_name, rel_prop_specs)
                        else:
                            rel_name = {rel_property_spec.property_name for rel_property_spec in rel_property_specs if rel_property_spec.property_name == rel_prop_name}.pop()
                            sys.exit('error: unstructured entity cannot have property named %s in relationship %s: %s' % (rel_prop_name, rel_name, str(entity_spec)))
                if self.include_impl and 'implementation_path' in entity_spec:
                    implementation_path_spec = Implementation_path_spec(self.conventions, entity_spec['implementation_path'], entity_name)
                    implementation_path_specs = [Implementation_path_spec(self.conventions, e_s['implementation_path'], e_n) for e_n, e_s in entities.iteritems() if e_s.get('implementation_path') == entity_spec['implementation_path']]
                    entity_interface =  self.get_entity_interface([implementation_path_spec], implementation_path_specs)
                    self.paths[implementation_path_spec.path_segment()] = entity_interface
                elif 'abstract' not in entity_spec or not entity_spec['abstract']: 
                    entity_url_property_spec = Entity_URL_spec(entity_name)
                    self.swagger['x-uris'][entity_url_property_spec.path_segment()] = self.build_entity_interface([entity_url_property_spec])
                if 'query_paths' in entity_spec:
                    query_paths = as_list(entity_spec['query_paths'])[:]
                    for rel_property_spec in rel_property_specs:
                        rel_property_spec_stack = [rel_property_spec]
                        if 'well_known_URLs' in entity_spec:
                            well_known_URLs = as_list(entity_spec['well_known_URLs'])
                            for well_known_URL in well_known_URLs:
                                baseURL_spec = Well_known_URL_Spec(well_known_URL, entity_name)
                                self.add_query_paths(query_paths, [baseURL_spec] + rel_property_spec_stack, rel_property_specs)
                        else:
                            entity_url_property_spec = Entity_URL_spec(entity_name)
                            self.add_query_paths(query_paths, [entity_url_property_spec] + rel_property_spec_stack, rel_property_specs)
                    if len(query_paths) > 0:
                        sys.exit('query paths not valid or listed more than once: %s' % [query_paths])  
        if not self.uris:
            del self.swagger['x-uris']
        return self.swagger

    def build_relationship_property_spec(self, rel_prop_name, rel_prop_specs):
        if len({rel_prop_spec.is_multivalued() for rel_prop_spec in rel_prop_specs}) > 1:
            print 'error: all multiplicities for relationship property %s must be the same' % rel_prop_name
            return None
        return {
            'description': 
                    'URL of a Collection of %s' % 
                        (' and '.join(['%ss' % rel_prop_spec.target_entity for rel_prop_spec in rel_prop_specs]) if len(rel_prop_specs) > 1 else '%ss' % rel_prop_specs[0].target_entity) 
                if rel_prop_specs[0].is_multivalued() else 
                    'URL of %s' % ('%s %s' % (article(rel_prop_specs[0].target_entity), ' or '.join([rel_prop_spec.target_entity for rel_prop_spec in rel_prop_specs])) if len(rel_prop_specs) > 1 else articled(rel_prop_specs[0].target_entity))
                ,
            'type': 'string',
            'format': 'uri',
            'x-rapier-relationship': {
                'type': {
                    'oneOf': [{'$ref': '#/definitions/%s' % rel_prop_spec.target_entity} for rel_prop_spec in rel_prop_specs]
                    } if len(rel_prop_specs) > 1 else
                    {'$ref': '#/definitions/%s' % rel_prop_specs[0].target_entity },
                'multiplicity': rel_prop_specs[0].get_multiplicity()
                }
            }
    def get_relationship_property_specs(self, entity_name):
        spec = self.rapier_spec
        result = []
        def add_type(rel_name, one_end, other_end):
            if 'property' in one_end:
                p_spec = \
                    Rel_mv_property_spec(
                        self.conventions,
                        one_end['property'],
                        one_end['entity'],
                        other_end['entity'],
                        rel_name, 
                        one_end.get('selector'),
                        one_end.get('readonly')) if get_multiplicity(one_end) == 'n' else \
                    Rel_sv_property_spec(
                        one_end['property'],
                        one_end['entity'],
                        other_end['entity'],
                        rel_name,
                        one_end.get('readonly'))
                result.append(p_spec)
           
        if 'relationships' in spec:
            relationships = spec['relationships']
            for rel_name, relationship in relationships.iteritems():
                if relationship['one_end']['entity'] == entity_name:
                    add_type(rel_name, relationship['one_end'], relationship['other_end'])
                if relationship['other_end']['entity'] == entity_name:
                    add_type(rel_name, relationship['other_end'], relationship['one_end'])
        return result
        
    def add_query_paths(self, query_paths, rel_property_spec_stack, prev_rel_property_specs):
        rapier_spec = self.rapier_spec
        rel_property_spec = rel_property_spec_stack[-1]
        target_entity = rel_property_spec.target_entity
        entity_spec = rapier_spec['entities'][target_entity]
        rel_property_specs = self.get_relationship_property_specs(target_entity)
        for rel_spec in rel_property_specs:
            if rel_spec not in rel_property_spec_stack:
                rel_property_spec_stack.append(rel_spec)
                self.add_query_paths(query_paths, rel_property_spec_stack, rel_property_specs)
                rel_property_spec_stack.pop()
        rel_path = '/'.join([rel_property_spec.path_segment() for rel_property_spec in rel_property_spec_stack[1:] if rel_property_spec.path_segment()])
        if rel_path in query_paths:
            self.emit_query_path(rel_property_spec_stack, prev_rel_property_specs)
            query_paths.remove(rel_path)
                
    def emit_query_path(self, rel_property_spec_stack, rel_property_specs):
        rel_property_spec = rel_property_spec_stack[-1]
        multivalued = rel_property_spec.is_multivalued()
        path = '/'.join([rel_property_spec.path_segment(inx != (len(rel_property_spec_stack)-1)) for inx, rel_property_spec in enumerate(rel_property_spec_stack)])
        paths = self.uris if rel_property_spec_stack[0].is_uri_spec() else self.paths 
        if path not in paths:
            if multivalued:
                paths[path] = self.build_relationship_interface(rel_property_spec_stack, rel_property_specs)
            if not multivalued or rel_property_spec.selector:
                path = '/'.join([rel_property_spec.path_segment(True) for rel_property_spec in rel_property_spec_stack])
                paths[path] = self.build_entity_interface(rel_property_spec_stack)
            
    def get_entity_interface(self, rel_property_spec_stack, rel_property_specs=[]):
        rel_property_spec = rel_property_spec_stack[-1]
        entity_name = rel_property_spec.target_entity
        if len(rel_property_specs) > 0:
            return self.build_entity_interface(rel_property_spec_stack, rel_property_specs)
        elif entity_name not in self.entity_specs:
            self.entity_specs[entity_name] = self.build_entity_interface(rel_property_spec_stack)
        return self.entity_specs[entity_name]
        
    def build_entity_interface(self, rel_property_spec_stack, rel_property_specs=[]):
        rel_property_spec = rel_property_spec_stack[-1]
        entity_name = rel_property_spec.target_entity
        entity_spec = self.rapier_spec['entities'][entity_name]
        consumes = as_list(entity_spec['consumes']) if 'consumes' in entity_spec else None 
        produces = as_list(entity_spec['produces']) if 'produces' in entity_spec else None 
        structured = 'type' not in entity_spec
        response_200 = {
            'schema': self.global_definition_ref('Entity' if len(rel_property_specs) > 1 else entity_name)
            }
        if len(rel_property_specs) > 1:
            response_200['schema']['x-oneOf'] = [self.global_definition_ref(spec.target_entity) for spec in rel_property_specs]
        if not self.yaml_merge:
            response_200.update(self.responses.get('standard_200'))
        else:
            response_200['<<'] = self.responses.get('standard_200')
        path_spec = PresortedOrderedDict()
        root_property_spec = rel_property_spec_stack[0]
        x_description = root_property_spec.x_description()
        if x_description:
            path_spec['x-description'] = x_description
        parameters = self.build_parameters(rel_property_spec_stack)
        if parameters:
            path_spec['parameters'] = parameters
        path_spec['get'] = {
                'description': 'Retrieve %s' % articled(entity_name),
                'parameters': [{'$ref': '#/parameters/Accept'}],
                'responses': {
                    '200': response_200, 
                    }
                }
        if not self.yaml_merge:
            path_spec['get']['responses'].update(self.response_sets['entity_get_responses'])
        else:
            path_spec['get']['responses']['<<'] = self.response_sets['entity_get_responses']
        if not 'immutable' in entity_spec or entity_spec['immutable'] == False:
            if structured:
                update_verb = 'patch'
                description = 'Update %s entity'
                parameter_ref = '#/parameters/If-Match'
                body_desciption =  'The subset of properties of the %s being updated' % entity_name
                schema = self.mutable_definition_ref(entity_name)                 
            else:
                update_verb = 'put'
                description = 'Create or Update %s entity'
                self.define_put_if_match_header()
                parameter_ref = '#/parameters/Put-If-Match'
                body_desciption =  'The representation of the %s being replaced' % entity_name
                schema = self.global_definition_ref(entity_name)
            description = description % articled(entity_name)
            path_spec[update_verb] = {
                'description': description,
                'parameters': [
                    {'$ref': parameter_ref}, 
                    {'name': 'body',
                    'in': 'body',
                    'description': body_desciption,
                    'schema': schema
                    }
                    ],
                'responses': { 
                    '200': response_200
                    }
                }
            if not self.yaml_merge:
                path_spec[update_verb]['responses'].update(self.response_sets['put_patch_responses'])
            else:
                path_spec[update_verb]['responses']['<<'] = self.response_sets['put_patch_responses']
            if not structured:
                path_spec['put']['responses']['201'] = {
                    'description': 'Created new %s' % entity_name,
                    'schema': self.global_definition_ref(entity_name),
                    'headers': {
                        'Location': {
                            'type': 'string',
                            'description': 'perma-link URL of newly-created %s'  % entity_name
                            }
                        }
                    }
            if consumes:
                path_spec[update_verb]['consumes'] = consumes
            if produces:
                path_spec['get']['produces'] = produces
        well_known = entity_spec.get('well_known_URLs')
        if not well_known:        
            path_spec['delete'] = {
                'description': 'Delete %s %s' % ('an' if entity_name[0].lower() in 'aeiou' else 'a', entity_name),
                'responses': {
                    '200': response_200
                    }
                }
            if not self.yaml_merge:
                path_spec['delete']['responses'].update(self.response_sets['delete_responses'])
            else:
                path_spec['delete']['responses']['<<'] = self.response_sets['delete_responses']
        path_spec['head'] = {
                'description': 'retrieve HEAD'
                }
        if not self.yaml_merge:
            path_spec['head'].update(self.methods['head'])
        else:
            path_spec['head']['<<'] = self.methods['head']
        path_spec['options'] = {
                'description': 'Retrieve OPTIONS',
               }
        if not self.yaml_merge:
            path_spec['options'].update(self.methods['options'])
        else:
            path_spec['options']['<<'] = self.methods['options']        
        return path_spec

    def build_relationship_interface(self, rel_property_spec_stack, rel_property_specs):
        rel_property_spec = rel_property_spec_stack[-1]
        relationship_name = rel_property_spec.property_name
        entity_name = rel_property_spec.target_entity
        path_spec = PresortedOrderedDict()
        parameters = self.build_parameters(rel_property_spec_stack[:-1]) 
        if parameters:
            path_spec['parameters'] = parameters
        path_spec['get'] = self.global_collection_get()
        rel_property_specs = [spec for spec in rel_property_specs if spec.property_name == relationship_name]
        if len(rel_property_specs) > 1:
            schema = self.global_definition_ref('Entity')
            schema['x-oneOf'] = [self.global_definition_ref(spec.target_entity) for spec in rel_property_specs]
            i201_description = 'Created new %s' % ' or '.join([spec.target_entity for spec in rel_property_specs])
            location_desciption =  'perma-link URL of newly-created %s' % ' or '.join([spec.target_entity for spec in rel_property_specs])
            body_desciption =  'The representation of the new %s being created' % ' or '.join([spec.target_entity for spec in rel_property_specs])
        else:    
            schema = self.global_definition_ref(entity_name)
            i201_description = 'Created new %s' % entity_name
            location_desciption = 'perma-link URL of newly-created %s'  % entity_name
            body_desciption =  'The representation of the new %s being created' % entity_name 
        if not rel_property_spec.readonly:
            if len(rel_property_specs) > 1:
                post_schema = self.mutable_definition_ref('Entity')
                #if False: # should validate but does not?
                post_schema['x-oneOf'] = [self.mutable_definition_ref(spec.target_entity) for spec in rel_property_specs]
                description = 'Create a new %s' % ' or '.join([rel_prop_spec.target_entity for rel_prop_spec in rel_property_specs])
            else:
                post_schema = self.mutable_definition_ref(entity_name)
                description = 'Create a new %s' % entity_name
            path_spec['post'] = {
                'description': description,
                'parameters': [
                    {'name': 'body',
                     'in': 'body',
                     'description': body_desciption,
                     'schema': post_schema
                    }
                    ],
                'responses': {
                    '201': {
                        'description': i201_description,
                        'schema': schema,
                        'headers': {
                            'Location': {
                                'type': 'string',
                                'description': location_desciption
                                },
                            'ETag': {
                                'type': 'string',
                                'description': 'Value of ETag required for subsequent updates'
                                }
                            }
                        }
                    }                
                }
            if not self.yaml_merge:
                path_spec['post']['responses'].update(self.response_sets['post_responses'])
            else:
                path_spec['post']['responses']['<<'] = self.response_sets['post_responses']
        path_spec['head'] = {
                'description': 'Retrieve HEAD'
                }
        if not self.yaml_merge:
            path_spec['head'].update(self.methods['head'])
        else:
            path_spec['head']['<<'] = self.methods['head']
        path_spec['options'] = {
                'description': 'Retrieve OPTIONS',
               }
        if not self.yaml_merge:
            path_spec['options'].update(self.methods['options'])
        else:
            path_spec['options']['<<'] = self.methods['options']            
        return path_spec
        
    def build_standard_response_sets(self):
        result = dict()
        result['entity_get_responses'] = {
            '401': self.global_response_ref('401'), 
            '403': self.global_response_ref('403'), 
            '404': self.global_response_ref('404'), 
            '406': self.global_response_ref('406'), 
            'default': self.global_response_ref('default')
            }
        result['put_patch_responses'] = {
            '400': self.global_response_ref('400'),
            '401': self.global_response_ref('401'), 
            '403': self.global_response_ref('403'), 
            '404': self.global_response_ref('404'), 
            '406': self.global_response_ref('406'), 
            '409': self.global_response_ref('409'),
            'default': self.global_response_ref('default')
            }  
        result['delete_responses'] = {
            '400': self.global_response_ref('400'),
            '401': self.global_response_ref('401'), 
            '403': self.global_response_ref('403'), 
            '404': self.global_response_ref('404'), 
            '406': self.global_response_ref('406'), 
            'default': self.global_response_ref('default')
            }
        result['post_responses'] = {        
            '400': self.global_response_ref('400'),
            '401': self.global_response_ref('401'), 
            '403': self.global_response_ref('403'), 
            '404': self.global_response_ref('404'), 
            '406': self.global_response_ref('406'), 
            'default': self.global_response_ref('default')
            }
        return result

    def build_standard_methods(self):
        result = dict()
        result['head'] = {
            'responses': {
                '200': self.global_response_ref('standard_200'), 
                '401': self.global_response_ref('401'), 
                '403': self.global_response_ref('403'), 
                '404': self.global_response_ref('404'), 
                'default': self.global_response_ref('default')
                }
            }
        result['options'] = {
            'parameters': [ 
                {'$ref': '#/parameters/Access-Control-Request-Method'}, 
                {'$ref': '#/parameters/Access-Control-Request-Headers'} 
                ],
            'responses': {
                '200': self.global_response_ref('options_200'), 
                '401': self.global_response_ref('401'), 
                '403': self.global_response_ref('403'), 
                '404': self.global_response_ref('404'), 
                'default': self.global_response_ref('default')
                }
            }

        return result

    def global_collection_get(self):
        if not hasattr(self, 'collection_get'):
            self.collection_get = self.build_collection_get()
        return self.collection_get
        
    def global_response_ref(self, key):
        if key not in self.swagger['responses']:
             self.swagger['responses'][key] = self.responses[key]
        return {'$ref': '#/responses/%s' % key}

    def server_entity_properties_ref(self):
        if 'ServerEntityProperties' not in self.definitions:
            self.definitions['ServerEntityProperties'] = {'properties': self.server_entity_properties}
        return {'$ref': '#/definitions/ServerEntityProperties'}
    
    def global_definition_ref(self, key):
        if key == 'Entity' and 'Entity' not in self.definitions:
            return {}
        return {'$ref': '#/definitions/%s' % key}
        
    def mutable_definition_ref(self, key):
        mod_key = '%sProperties' % key
        return self.global_definition_ref(mod_key)
        
    def build_parameters(self, rel_property_spec_stack):
        result = []
        for rel_property_spec in rel_property_spec_stack:
            param = rel_property_spec.build_param()
            if param:
                result.append(param)
        return result
          
    def build_standard_responses(self):
        return {
            'standard_200': {
                'description': 'successful',
                'headers': {
                    'Content-Location': {
                        'type': 'string',
                        'description': 'perma-link URL of resource'
                        },
                    'ETag': {
                        'description': 'this value must be echoed in the If-Match header of every PATCH or PUT',
                        'type': 'string'
                        }
                    }
                },
            'options_200': {
                'description': 'successful',
                'headers': {
                    'Access-Control-Allow-Origin': {
                        'type': 'string',
                        'description': 'origins allowed'
                        },
                    'Access-Control-Allow-Methods': {
                        'description': 'methods allowed',
                        'type': 'string'
                        },
                    'Access-Control-Allow-Headers': {
                        'description': 'headers allowed',
                        'type': 'string'
                        },
                    'Access-Control-Max-Age': {
                        'description': 'length of time response can be cached',
                        'type': 'string'
                        }
                    }
                },
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
                'description': 'Not Acceptable. Requested media type not available',
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
        if 'Collection' not in self.definitions:
            sys.exit('error: must define Collection')
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
                '303': self.global_response_ref('303'),
                '401': self.global_response_ref('401'), 
                '403': self.global_response_ref('403'), 
                '404': self.global_response_ref('404'), 
                '406': self.global_response_ref('406'), 
                'default': self.global_response_ref('default')
                }
            }
 
    def build_standard_definitions(self):
        return {
            'ErrorResponse': self.build_error_definition()
            }
            
    def define_put_if_match_header(self):
        if not 'Put-If-Match' in self.header_parameters:
            self.header_parameters['Put-If-Match'] = {
                'name': 'If-Match',
                'in': 'header',
                'type': 'string',
                'description': 'specifies the last known ETag value of the resource being modified',
                'required': False
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
                },
            'Access-Control-Request-Method': {
                'name': 'Access-Control-Request-Method',
                'description': 'specifies the method the client wishes to use',
                'in': 'header',
                'required': True,
                'type': 'string'
                },
            'Access-Control-Request-Headers': {
                'name': 'Access-Control-Request-Headers',
                'description': 'specifies the custom headers the client wishes to use',
                'in': 'header',
                'required': True,
                'type': 'string'
                }
            }
    
    def build_error_definition(self):
        return {
            'properties': {
                'message': {
                    'type': 'string'
                    }
                }
            }

class Segement_spec(object):
            
    def build_param(self):
        return None  
        
    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.__dict__.hash()

    def __str__(self):
        return self.__dict__.str()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(['%s=%s' % item for item in self.__dict__.iteritems()]))
        
    def x_description(self):
        return None
        
    def is_uri_spec(self):
        return False
        
class Rel_sv_property_spec(Segement_spec):
    
    def __init__(self, property_name, source_entity, target_entity, rel_name, readonly=False):
        self.property_name = property_name
        self.source_entity = source_entity
        self.target_entity = target_entity
        self.rel_name = rel_name
        self.readonly = readonly 
        
    def path_segment(self, select_one_of_many = False):
        return self.property_name
        
    def is_multivalued(self):
        False
        
    def get_multiplicity(self):
        return '1'
                
class Rel_mv_property_spec(Segement_spec):
    
    def __init__(self, conventions, property_name, source_entity, target_entity, rel_name, selector, readonly=False):
        self.property_name = property_name
        self.source_entity = source_entity
        self.target_entity = target_entity
        self.rel_name = rel_name
        self.selector = selector 
        self.readonly = readonly 
        self.conventions = conventions

    def path_segment(self, select_one_of_many = False):
        if select_one_of_many:
            separator = '/' if self.conventions.get('selector_location') == 'path-parameter' else ';'
            return '%s%s{%s-%s}' % (self.property_name, separator, self.target_entity, self.selector)
        return self.property_name
        
    def is_multivalued(self):
        return True
            
    def get_multiplicity(self):
        return 'n'

    def build_param(self):
        return {
            'name': '%s-%s' % (self.target_entity, self.selector),
            'in': 'path',
            'type': 'string',
            'description':
                "Specifies which '%s' entity from multi-valued relationship '%s'" % (self.target_entity, self.property_name),
            'required': True
            }

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __hash__():
        return self.__dict__.hash()

    def __ne__(self, other):
        return not self.__eq__(other)
        
class Well_known_URL_Spec(Segement_spec):
    
    def __init__(self, base_URL, target_entity):
        self.base_URL = base_URL 
        self.target_entity = target_entity

    def path_segment(self, select_one_of_many = False):
        return self.base_URL[1:] if self.base_URL.endswith('/') else self.base_URL

    def build_param(self):
        return None        

class Implementation_path_spec(Segement_spec):

    def __init__(self, conventions, implementation_path, target_entity):
        self.implementation_path = implementation_path
        self.target_entity = target_entity
        self.conventions = conventions
        
    def path_segment(self, select_one_of_many = False):
        separator = '/' if self.conventions.get('selector_location') == 'path-parameter' else ';'
        return '%s%s{implementation_key}' % (self.implementation_path, separator)

    def build_param(self):
        return {
            'name': 'implementation_key',
            'in': 'path',
            'type': 'string',
            'description': 'This parameter is a private part of the implementation. It is not part of the API',
            'required': True
            }
            
    def x_description(self):
        return 'This path is NOT part of the API. It is used in the implementaton and may be ' \
            'important to implementation-aware software, such as proxies or specification-driven implementations.'

class Entity_URL_spec(Segement_spec):
    
    def __init__(self, target_entity):
        self.target_entity = target_entity

    def path_segment(self, select_one_of_many = False):
        return '{%s_URL}' % self.target_entity

    def build_param(self):
        return {
            'name': '%s_URL' % self.target_entity,
            'in': 'path',
            'type': 'string',
            'description':
                "The URL of %s entity" % articled(self.target_entity),
            'required': True
            }
            
    def is_uri_spec(self):
        return True
 

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
    
def get_multiplicity(rel_property_spec):
    multiplicity = rel_property_spec.get('multiplicity')
    return multiplicity.split(':')[-1] if multiplicity else 1
    
def main(args):
    generator = SwaggerGenerator()
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'mai', ['yaml-merge', 'yaml-alias', 'include-impl'])
    except getopt.GetoptError as err:
        usage = '\nusage: gen_swagger.py [-m, --yaml-merge] [-a, --yaml-alias] [-i, --include-impl] filename'
        sys.exit(str(err) + usage)
    generator.set_rapier_spec_from_filename(*args)
    generator.set_opts(opts)
    Dumper = yaml.SafeDumper
    opts_keys = [k for k,v in opts]
    if '--yaml-alias' not in opts_keys and '-m' not in opts_keys:
        Dumper.ignore_aliases = lambda self, data: True
    Dumper.add_representer(PresortedOrderedDict, yaml.representer.SafeRepresenter.represent_dict)
    print str.replace(yaml.dump(generator.swagger_from_rapier(), default_flow_style=False, Dumper=Dumper), "'<<':", '<<:')
    
def article(name):
    return 'an' if name[0].lower() in 'aeiou' else 'a'
        
def articled(name):
    return '%s %s' % (article(name), name)
        
if __name__ == "__main__":
    main(sys.argv)