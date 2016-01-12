#!/usr/bin/env python 

import yaml, sys, getopt, itertools
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
        self.suppress_annotations = '--suppress-annotations' in self.opts_keys or '-s' in self.opts_keys

    def swagger_from_rapier(self, filename= None):
        if filename:
            self.set_rapier_spec_from_filename(filename)
        spec = self.rapier_spec 
        self.conventions = spec['conventions'] if 'conventions' in spec else {}     
        if 'multi_valued_relationships' in self.conventions:
            self.collection_entity_name = self.conventions['multi_valued_relationships']['entity']
        if 'selector_location' in self.conventions:
            if self.conventions['selector_location'] not in ['path-segment', 'path-parameter']:
                sys.exit('error: invalid value for selector_location: %s' % self.selector_location)
            self.discriminator_separator = '/' if self.conventions['selector_location'] == 'path-segment' else ';'
        else:
            self.discriminator_separator = ';'
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
        if 'securityDefinitions' in spec:
            self.swagger['securityDefinitions'] = spec['securityDefinitions']            
        if 'security' in spec:
            self.swagger['security'] = spec['security']            
        self.definitions = {}
        if 'error_response' in self.conventions:
            self.definitions['ErrorResponse'] = self.conventions['error_response']
            self.error_response = self.global_definition_ref('ErrorResponse')
        else:
            self.error_response = {}
        self.patch_consumes = as_list(self.conventions['patch_consumes']) if 'patch_consumes' in self.conventions else ['application/merge-patch+json', 'application/json-patch+json']
        self.swagger['definitions'] = self.definitions
        self.responses = self.build_standard_responses()
        self.swagger['paths'] = self.paths
        self.swagger['x-uris'] = self.uris
        self.header_parameters = self.build_standard_header_parameters()
        self.swagger['parameters'] = self.header_parameters
        self.swagger['responses'] = dict()
        self.response_sets = self.build_standard_response_sets()
        self.methods = self.build_standard_methods()
        self.swagger['info']['title'] = spec['title'] if 'title' in spec else 'untitled'
        self.swagger['info']['version'] = spec['version'] if 'version' in spec else 'initial'

        if 'entities' in spec:
            entities = spec['entities']
            self.swagger['definitions'] = self.definitions
            for entity_name, entity_spec in entities.iteritems():
                definition = dict()
                if 'allOf' in entity_spec:
                    definition['allOf'] = [{key: value.replace('entities', 'definitions') for key, value in ref.iteritems()} for ref in entity_spec['allOf']]
                if  not 'type' in entity_spec or entity_spec['type'] == 'object': # TODO: maybe need to climb allOf tree to check this more fully
                    if 'properties' in entity_spec:
                        immutable_entity = entity_spec.get('readOnly', False)
                        properties = {prop_name: prop for prop_name, prop in entity_spec['properties'].iteritems()}
                        if immutable_entity:
                            for prop in properties.itervalues():
                                prop['readOnly'] = True
                        definition['properties'] = properties
                    if 'required' in entity_spec:
                        definition['required'] = entity_spec['required']
                    if 'type' in entity_spec:
                        definition['type'] = entity_spec['type']
                self.definitions[entity_name] = definition
            for entity_name, entity_spec in entities.iteritems():
                if 'well_known_URLs' in entity_spec:
                    for well_known_URL in as_list(entity_spec['well_known_URLs']):
                        self.swagger['paths'][well_known_URL] = self.build_entity_interface(WellKnownURLSpec(well_known_URL, entity_name))
                rel_property_specs = self.get_relationship_property_specs(entity_name)
                if len(rel_property_specs) > 0:
                    definition = self.definitions[entity_name]
                    rel_prop_spec_dict = {}
                    for rel_property_spec in rel_property_specs:
                        rel_prop_name = rel_property_spec.property_name
                        if rel_prop_name in rel_prop_spec_dict:
                            rel_prop_spec_dict[rel_prop_name].append(rel_property_spec)
                        else:
                            rel_prop_spec_dict[rel_prop_name] = [rel_property_spec]
                    for rel_prop_name, rel_prop_specs in rel_prop_spec_dict.iteritems():
                        definition = self.definitions[entity_name]
                        definition.setdefault('properties', dict())[rel_prop_name] = self.build_relationship_property_spec(rel_prop_name, rel_prop_specs)
                        if 'type' in entity_spec:
                            definition['type'] = entity_spec['type']
                if self.include_impl and 'implementation_spec' in entity_spec:
                    implementation_spec_spec = ImplementationPathSpec(self.conventions, entity_spec['implementation_spec'], entity_name)
                    implementation_spec_specs = [ImplementationPathSpec(self.conventions, e_s['implementation_spec'], e_n) for e_n, e_s in entities.iteritems() if e_s.get('implementation_spec') and e_s['implementation_spec']['path'] == entity_spec['implementation_spec']['path']]
                    entity_interface =  self.build_entity_interface(implementation_spec_spec, None, None, implementation_spec_specs)
                    self.paths[implementation_spec_spec.path_segment()] = entity_interface
                elif not self.include_impl and not entity_spec.get('abstract', False) and entity_spec.get('resource', True): 
                    entity_url_property_spec = EntityURLSpec(entity_name)
                    self.swagger['x-uris'][entity_url_property_spec.path_segment()] = self.build_entity_interface(entity_url_property_spec)
                if 'query_paths' in entity_spec:
                    query_paths = [QueryPath(query_path_string, self) for query_path_string in as_list(entity_spec['query_paths'])]
                    for rel_property_spec in rel_property_specs:
                        rel_property_spec_stack = [rel_property_spec]
                        if self.include_impl and 'implementation_spec' in entity_spec:
                            implementation_spec_spec = ImplementationPathSpec(self.conventions, entity_spec['implementation_spec'], entity_name)
                            self.add_query_paths(query_paths[:], implementation_spec_spec, rel_property_spec_stack, rel_property_specs)
                        if 'well_known_URLs' in entity_spec:
                            well_known_URLs = as_list(entity_spec['well_known_URLs'])
                            leftover_query_paths = query_paths
                            for well_known_URL in well_known_URLs:
                                leftover_query_paths = query_paths[:]
                                baseURL_spec = WellKnownURLSpec(well_known_URL, entity_name)
                                self.add_query_paths(leftover_query_paths, baseURL_spec, rel_property_spec_stack, rel_property_specs)
                            query_paths = leftover_query_paths
                        else:
                            entity_url_property_spec = EntityURLSpec(entity_name)
                            self.add_query_paths(query_paths, entity_url_property_spec, rel_property_spec_stack, rel_property_specs)
                    if len(query_paths) > 0:
                        sys.exit('query paths not valid or listed more than once: %s' % query_paths)  
        if not self.uris:
            del self.swagger['x-uris']
        return self.swagger

    def build_relationship_property_spec(self, rel_prop_name, rel_prop_specs):
        if len({rel_prop_spec.is_multivalued() for rel_prop_spec in rel_prop_specs}) > 1:
            sys.exit('error: all multiplicities for relationship property %s must be the same' % rel_prop_name)
        if rel_prop_specs[0].is_collection_resource():
            result = {
                'description': 
                        'URL of a Collection of %s' % 
                            (' and '.join(['%ss' % rel_prop_spec.target_entity for rel_prop_spec in rel_prop_specs]) if len(rel_prop_specs) > 1 else '%ss' % rel_prop_specs[0].target_entity) 
                    if rel_prop_specs[0].is_multivalued() else 
                        'URL of %s' % ('%s %s' % (article(rel_prop_specs[0].target_entity), ' or '.join([rel_prop_spec.target_entity for rel_prop_spec in rel_prop_specs])) if len(rel_prop_specs) > 1 else articled(rel_prop_specs[0].target_entity))
                    ,
                'type': 'string',
                'format': 'uri',
                'readOnly': True
                }
        elif rel_prop_specs[0].is_multivalued():
            result = {
                'description': 
                    'Array of URLs of %s' % 
                        (' and '.join(['%ss' % rel_prop_spec.target_entity for rel_prop_spec in rel_prop_specs]) if len(rel_prop_specs) > 1 else '%ss' % rel_prop_specs[0].target_entity),
                'type': 'array',
                'items': {
                    'type': 'string',
                    'format': 'uri'
                    }
                }
        else:
            result = {
                'description': 
                    'URL of %s' % ('%s %s' % (article(rel_prop_specs[0].target_entity), ' or '.join([rel_prop_spec.target_entity for rel_prop_spec in rel_prop_specs])) if len(rel_prop_specs) > 1 else articled(rel_prop_specs[0].target_entity)),
                'type': 'string',
                'format': 'uri',
                }
        if rel_prop_specs[0].readonly:
            result['readOnly'] = True
        if not self.suppress_annotations:
            result['x-rapier-relationship'] = {
                'type': {
                    'oneOf': [{'$ref': '#/definitions/%s' % rel_prop_spec.target_entity} for rel_prop_spec in rel_prop_specs]
                    } if len(rel_prop_specs) > 1 else
                    {'$ref': '#/definitions/%s' % rel_prop_specs[0].target_entity },
                'multiplicity': rel_prop_specs[0].get_multiplicity()
                }
        return result
        
    def get_relationship_property_specs(self, entity_name):
        spec = self.rapier_spec
        result = []
        def add_type(rel_name, one_end, other_end):
            if 'property' in one_end:
                p_spec = \
                    RelMVPropertySpec(
                        self.conventions, 
                        one_end['property'], 
                        one_end['entity'], 
                        other_end['entity'], 
                        rel_name, one_end.get('multiplicity'), 
                        one_end.get('collection_resource'), 
                        one_end.get('consumes'), 
                        one_end.get('readOnly')) \
                if get_multiplicity(one_end) == 'n' else \
                    RelSVPropertySpec(self.conventions, 
                        one_end['property'], 
                        one_end['entity'], 
                        other_end['entity'], 
                        rel_name, 
                        one_end.get('multiplicity'), 
                        one_end.get('readOnly'))
                result.append(p_spec)
           
        if 'relationships' in spec:
            relationships = spec['relationships']
            for rel_name, relationship in relationships.iteritems():
                if relationship['one_end']['entity'] == entity_name:
                    add_type(rel_name, relationship['one_end'], relationship['other_end'])
                if relationship['other_end']['entity'] == entity_name:
                    add_type(rel_name, relationship['other_end'], relationship['one_end'])
        return result
        
    def add_query_paths(self, query_paths, prefix, rel_property_spec_stack, prev_rel_property_specs):
        rapier_spec = self.rapier_spec
        rel_property_spec = rel_property_spec_stack[-1]
        target_entity = rel_property_spec.target_entity
        entity_spec = rapier_spec['entities'][target_entity]
        rel_property_specs = self.get_relationship_property_specs(target_entity)
        for rel_spec in rel_property_specs:
            if rel_spec not in rel_property_spec_stack:
                rel_property_spec_stack.append(rel_spec)
                self.add_query_paths(query_paths, prefix, rel_property_spec_stack, rel_property_specs)
                rel_property_spec_stack.pop()
        for query_path in query_paths[:]:
            if query_path.matches(rel_property_spec_stack):
                self.emit_query_path(prefix, query_path, rel_property_spec_stack, prev_rel_property_specs)
                query_paths.remove(query_path)
                
    def emit_query_path(self, prefix, query_path, rel_property_spec_stack, rel_property_specs):
        for inx, spec in enumerate(rel_property_spec_stack):
            if spec.is_multivalued() and not query_path.query_segments[inx].param and not inx == len(rel_property_spec_stack) - 1:
                sys.exit('query path has multi-valued segment with no parameter: %s' % query_path)
        is_collection_resource = rel_property_spec_stack[-1].is_collection_resource() and not query_path.query_segments[-1].param
        path = '/'.join([prefix.path_segment(), query_path.swagger_path_string])
        if not (self.include_impl and prefix.is_uri_spec()):
            paths = self.uris if prefix.is_uri_spec() else self.paths 
            if path not in paths:
                if is_collection_resource:
                    paths[path] = self.build_relationship_interface(prefix, query_path, rel_property_spec_stack, rel_property_specs)
                else:
                    paths[path] = self.build_entity_interface(prefix, query_path, rel_property_spec_stack)
                    
    def build_entity_interface(self, prefix, query_path=None, rel_property_spec_stack=[], rel_property_specs=[]):
        entity_name = rel_property_spec_stack[-1].target_entity if rel_property_spec_stack else prefix.target_entity
        entity_spec = self.rapier_spec['entities'][entity_name]
        consumes = as_list(entity_spec['consumes']) if 'consumes' in entity_spec else None 
        produces = as_list(entity_spec['produces']) if 'produces' in entity_spec else None 
        query_parameters = entity_spec.get('query_parameters') 
        structured = 'type' not in entity_spec
        response_200 = {
            'schema': {} if len(rel_property_specs) > 1 else self.global_definition_ref(entity_name)
            }
        if len(rel_property_specs) > 1:
            response_200['schema']['x-oneOf'] = [self.global_definition_ref(spec.target_entity) for spec in rel_property_specs]
        if not self.yaml_merge:
            response_200.update(self.responses.get('standard_200'))
        else:
            response_200['<<'] = self.responses.get('standard_200')
        path_spec = PresortedOrderedDict()
        if prefix.is_private():
            path_spec['x-private'] = True            
        x_description = prefix.x_description()
        if x_description:
            path_spec['x-description'] = x_description
        parameters = self.build_parameters(prefix, query_path)
        if parameters:
            path_spec['parameters'] = parameters
        path_spec['get'] = {
                'description': 'Retrieve %s' % articled(entity_name),
                'parameters': [{'$ref': '#/parameters/Accept'}],
                'responses': {
                    '200': response_200, 
                    }
                }
        if produces:
            path_spec['get']['produces'] = produces
        if query_parameters:
            path_spec['get']['parameters'] = [{k: v for d in [{'in': 'query'}, query_parameter] for k, v in d.iteritems()} for query_parameter in query_parameters]
        if not self.yaml_merge:
            path_spec['get']['responses'].update(self.response_sets['entity_get_responses'])
        else:
            path_spec['get']['responses']['<<'] = self.response_sets['entity_get_responses']
        immutable = entity_spec.get('readOnly', False)
        if not immutable:
            if structured:
                update_verb = 'patch'
                description = 'Update %s entity'
                parameter_ref = '#/parameters/If-Match'
                body_desciption =  'The subset of properties of the %s being updated' % entity_name
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
            if structured:
                path_spec['patch']['consumes'] = self.patch_consumes
            else:
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
                path_spec[update_verb]['produces'] = produces
        well_known = entity_spec.get('well_known_URLs')
        if not well_known and not immutable:        
            path_spec['delete'] = {
                'description': 'Delete %s %s' % ('an' if entity_name[0].lower() in 'aeiou' else 'a', entity_name),
                'responses': {
                    '200': response_200
                    }
                }
            if produces:
                path_spec['delete']['produces'] = produces
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

    def build_relationship_interface(self, prefix, query_path, rel_property_spec_stack, rel_property_specs):
        rel_property_spec = rel_property_spec_stack[-1] if rel_property_spec_stack else prefix
        relationship_name = rel_property_spec.property_name
        entity_name = rel_property_spec.target_entity
        entity_spec = self.rapier_spec['entities'][entity_name]
        path_spec = PresortedOrderedDict()
        if prefix.is_private():
            path_spec['x-private'] = True            
        parameters = self.build_parameters(prefix, query_path) 
        if parameters:
            path_spec['parameters'] = parameters
        path_spec['get'] = self.global_collection_get()
        rel_property_specs = [spec for spec in rel_property_specs if spec.property_name == relationship_name]
        consumes_entities = [entity for spec in rel_property_specs for entity in spec.consumes_entities]
        consumes_media_types = [media_type for spec in rel_property_specs if spec.consumes_media_types for media_type in spec.consumes_media_types]
        if len(rel_property_specs) > 1:
            schema = {}
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
            if len(consumes_entities) > 1:
                post_schema = {}
                post_schema['x-oneOf'] = [self.global_definition_ref(consumes_entity) for consumes_entity in consumes_entities]
                description = 'Create a new %s' % ' or '.join([rel_prop_spec.target_entity for rel_prop_spec in rel_property_specs])
            else:
                post_schema = self.global_definition_ref(entity_name)
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
            if consumes_media_types:
                path_spec['post']['consumes'] = consumes_media_types
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

    def global_definition_ref(self, key):
        return {'$ref': '#/definitions/%s' % key}
        
    def build_parameters(self, prefix, query_path):
        result = []
        param = prefix.build_param()
        if param:
            if isinstance(param, list):
                result.extend(param)
            else:
                result.append(param)
        if query_path:
            for query_segment in query_path.query_segments:
                param = query_segment.build_param()
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
                'schema': self.error_response
                },
            '401': {
                'description': 'Unauthorized. Client authentication token missing from request',
                'schema': self.error_response
                }, 
            '403': {
                'description': 'Forbidden. Client authentication token does not permit this method on this resource',
                'schema': self.error_response
                }, 
            '404': {
                'description': 'Not Found. Resource not found',
                'schema': self.error_response
                }, 
            '406': {
                'description': 'Not Acceptable. Requested media type not available',
                'schema': self.error_response
                }, 
            '409': {
                'description': 'Conflict. Value provided in If-Match header does not match current ETag value of resource',
                'schema': self.error_response
                }, 
            'default': {
                'description': '5xx errors and other stuff',
                'schema': self.error_response
                }
            }
        
    def build_collection_get(self):
        if not hasattr(self, 'collection_entity_name') or self.collection_entity_name not in self.definitions:
            sys.exit('error: must define entity for %s' % (self.collection_entity_name if hasattr(self, 'collection_entity_name') else 'multi-valued relationships'))
        rslt = {
            'responses': {
                '200': {
                    'description': 'description',
                    'schema': self.global_definition_ref(self.collection_entity_name),
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
        entity_spec = self.rapier_spec['entities'][self.collection_entity_name]
        query_parameters = entity_spec.get('query_parameters') 
        if query_parameters:
            rslt['parameters'] = [{k: v for d in [{'in': 'query'}, query_parameter] for k, v in d.iteritems()} for query_parameter in query_parameters]
        return rslt        
 
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

class SegmentSpec(object):
            
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
        
class PathPrefix(object):
            
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
        
    def is_private(self):
        return False
        
    def is_uri_spec(self):
        return False
      
class RelSVPropertySpec(SegmentSpec):
    
    def __init__(self, conventions, property_name, source_entity, target_entity, rel_name, multiplicity, readonly=False):
        self.property_name = property_name
        self.source_entity = source_entity
        self.target_entity = target_entity
        self.rel_name = rel_name
        self.multiplicity = multiplicity
        self.readonly = readonly 
        
    def is_multivalued(self):
        False
        
    def is_collection_resource(self):
        False
        
    def get_multiplicity(self):
        return self.multiplicity
                
class RelMVPropertySpec(SegmentSpec):
    
    def __init__(self, conventions, property_name, source_entity, target_entity, rel_name, multiplicity,  collection_resource, consumes, readonly):
        self.property_name = property_name
        self.source_entity = source_entity
        self.target_entity = target_entity
        self.rel_name = rel_name
        self.multiplicity = multiplicity
        self.readonly = readonly 
        self.conventions = conventions
        self.collection_resource = True if collection_resource == None else collection_resource
        self.consumes = consumes
        self.consumes_media_types = consumes.keys() if isinstance(consumes, dict) else as_list(consumes) if consumes is not None else None
        self.consumes_entities = [entity for entity_list in consumes.values() for entity in as_list(entity_list)] if isinstance(consumes, dict) else [self.target_entity] 

    def is_multivalued(self):
        return True
        
    def is_collection_resource(self):
        return self.collection_resource
            
    def get_multiplicity(self):
        return self.multiplicity

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __hash__():
        return self.__dict__.hash()
        
    def __ne__(self, other):
        return not self.__eq__(other)
        
class WellKnownURLSpec(PathPrefix):
    
    def __init__(self, base_URL, target_entity):
        self.base_URL = base_URL 
        self.target_entity = target_entity

    def path_segment(self, select_one_of_many = False):
        return self.base_URL[1:] if self.base_URL.endswith('/') else self.base_URL

    def build_param(self):
        input_string = self.base_URL
        param_name = ''
        params = []
        while param_name is not None:
            param_name, next_start = get_param_name(input_string)
            if param_name:
                params.append({
                'name': param_name,
                'in': 'path',
                'type': 'string',
                'required': True
                })
                input_string = input_string[next_start:]
        return params

class QueryPath(object):

    def __init__(self, query_path_string, generator):
        self.query_path_string = query_path_string
        self.query_segments = [QuerySegment(segment_string, generator) for segment_string in query_path_string.split('/')]
        for inx, query_segment in enumerate(self.query_segments):
            query_segment.parse_query_segment(inx, self.query_segments)
        self.swagger_path_string = '/'.join([query_segment.swagger_segment_string for query_segment in self.query_segments])
            
    def matches(self, rel_stack):
        if len(self.query_segments) == len(rel_stack):
            for segment, rel_spec in itertools.izip(self.query_segments, rel_stack):
                if segment.property_name != rel_spec.property_name:
                    return False
            return True
        else:
            return False
            
    def __str__(self):
        return self.query_path_string

    def __repr__(self):
        return 'QueryPath(%s)' % self.query_path_string
        
class QuerySegment(object):

    def __init__(self, segment_string, generator):
        self.query_segment_string = segment_string
        self.swagger_segment_string = segment_string.replace(';', generator.discriminator_separator)
        self.generator = generator
        
    def parse_query_segment(self, index, query_segments):
        parts = self.query_segment_string.split(';')
        if len(parts) > 2:
            sys.exit('query path segment contains more than 1 ; - %s' % self.query_segment_string)
        elif len(parts) == 2:
            path_params = parts[1]
            if '{' in path_params:
                open_brace_offset = path_params.index('{')
                if '}' in path_params:
                    close_brace_offset = path_params.index('}')
                    if open_brace_offset < close_brace_offset:
                        self.param = path_params[open_brace_offset+1 : close_brace_offset]
                        duplicate_count = len([query_segement.param == self.param for query_segement in query_segments[:index]])
                        if duplicate_count > 0:
                            self.param = '_'.join((self.param, str(duplicate_count)))
                            path_params = self.param.join((path_params[:open_brace_offset+1], path_params[close_brace_offset:]))
                            self.swagger_segment_string = self.generator.discriminator_separator.join((parts[0], path_params))
                    else:
                        sys.exit('empty path parameter ({}) - %s' % segment_string)
                else:
                    sys.exit('no closing { for path paramter - %s' % segment_string)
            else:
                sys.exit('missing path paramter ({xxx}) - %s' % segment_string)
        else:
            self.param = None
        self.property_name = parts[0]    

    def build_param(self):
        return {
            'name': self.param,
            'in': 'path',
            'type': 'string',
            'required': True
            } if self.param else None

    def __str__(self):
        return self.query_segment_string

    def __repr__(self):
        return 'QuerySegment(%s)' % self.query_segment_string
        
class ImplementationPathSpec(PathPrefix):

    def __init__(self, conventions, implementation_spec, target_entity):
        self.implementation_spec = implementation_spec
        self.target_entity = target_entity
        self.conventions = conventions
        
    def path_segment(self, select_one_of_many = False):
        separator = '/' if self.conventions.get('selector_location') == 'path-segment' else ';'
        return '%s%s{%s}' % (self.implementation_spec['path'], separator, self.implementation_spec['name'])

    def build_param(self):
        return {
            'name': self.implementation_spec['name'],
            'in': 'path',
            'type': self.implementation_spec['type'],
            'description': 'This parameter is a private part of the implementation. It is not part of the API',
            'required': True
            }
            
    def x_description(self):
        return 'This path is NOT part of the API. It is used in the implementaton and may be ' \
            'important to implementation-aware software, such as proxies or specification-driven implementations.'
            
    def is_private(self):
        return True

class EntityURLSpec(PathPrefix):
    
    def __init__(self, target_entity):
        self.target_entity = target_entity

    def path_segment(self, select_one_of_many = False):
        return '{%s_URL}' % self.target_entity

    def build_param(self):
        return {
            'name': '%s_URL' % self.target_entity,
            'in': 'URL',
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
        opts, args = getopt.getopt(sys.argv[1:], 'maivs', ['yaml-merge', 'yaml-alias', 'include-impl', 'suppress-annotations'])
    except getopt.GetoptError as err:
        usage = '\nusage: gen_swagger.py [-m, --yaml-merge] [-a, --yaml-alias] [-i, --include-impl] [-n, --suppress-annotations] filename'
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
    
def get_param_name(input_string):
    if '{' in input_string:
        open_brace_offset = input_string.index('{')
        if '}' in input_string:
            close_brace_offset = input_string.index('}')
            if open_brace_offset < close_brace_offset:
                param = input_string[open_brace_offset+1 : close_brace_offset]
            else:
                sys.exit('empty path parameter ({}) - %s' % segment_string)
        else:
            sys.exit('no closing { for path paramter - %s' % segment_string)
    else:
        param = None
        close_brace_offset = -1
    return param, close_brace_offset + 1
                
if __name__ == "__main__":
    main(sys.argv)