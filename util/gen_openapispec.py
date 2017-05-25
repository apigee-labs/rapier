#!/usr/bin/env python 

import yaml, sys, getopt, itertools, string, re
import validate_rapier
from validate_rapier import PresortedOrderedDict
import os
import re

class OASGenerator(object):

    def __init__(self):
        pass

    def set_opts(self, opts):
        self.opts = opts
        self.opts_keys = [k for k,v in opts]
        self.yaml_merge = '--yaml-merge' in self.opts_keys or '-m' in self.opts_keys
        self.include_impl = '--include-impl' in self.opts_keys or '-i' in self.opts_keys
        self.use_templates = not ('--suppress-templates' in self.opts_keys or '-t' in self.opts_keys)

    def openAPI_spec_from_rapier(self, filename):
        self.validator = validate_rapier.OASValidator()
        spec, errors = self.validator.validate(filename, None)
        if errors > 0:
            sys.exit('Validation of %s failed. OpenAPI spec generation not attempted' % filename)
        elif spec is None:
            sys.exit('Empty spec: %s - no OpenAPI spec generated' % filename)        
        else:
            self.rapier_spec = spec
        self.conventions = spec.get('conventions',{})     
        if 'queryPathSelectorLocation' in self.conventions:
            self.relationship_separator = '/' if self.conventions['queryPathSelectorLocation'] == 'pathSegment' else ';'
        else:
            self.relationship_separator = ';'
        self.patch_consumes = as_list(self.conventions['patchConsumes']) if 'patchConsumes' in self.conventions else ['application/merge-patch+json']
        self.use_etag = self.conventions.get('useEtag', True) is True
        patterns = spec.get('patterns')
        self.openapispec = PresortedOrderedDict()
        if self.include_impl:
            self.openapispec['x-description'] = \
                '*** This document is not a specification of an API. This document includes implementation-specific additions and modifications ' \
                'to an API that are designed to aid implementation-aware software like proxies and implementation frameworks. ' \
                'If you are looking for the API specification, find the version that was generated without implementation extensions and modifications'
        # Start building OpenAPI specification
        self.openapispec['swagger'] = '2.0'
        # Build info object
        self.openapispec['info'] = dict()
        self.openapispec['info']['title'] = spec.get('title', 'untitled')
        self.openapispec['info']['version'] = spec['version'] if 'version' in spec else 'initial'
        description = spec.get('description')
        if description is not None:
            self.openapispec['info']['description'] = description
        if 'consumes' in spec:
            self.openapispec['consumes'] = as_list(spec.get('consumes'))
        else:
            self.openapispec['consumes'] = ['application/json']
        if 'produces' in spec:
            self.openapispec['produces'] = as_list(spec.get('produces'))
        else:
            self.openapispec['produces'] = ['application/json', 'text/html']
        # Interfaces is better before paths and templates, otherwise YAML merge operator (<<) gives awkward results            
        self.openapispec_interfaces = dict()
        self.openapispec['x-interfaces'] = self.openapispec_interfaces
        # Templates is better before paths, otherwise YAML merge operator (<<) gives awkward results            
        if self.use_templates:
            self.openapispec_templates = dict()
        if self.use_templates:
            self.openapispec['x-templates'] = self.openapispec_templates
        # Now add paths
        self.openapispec_paths = PresortedOrderedDict()
        self.openapispec['paths'] = self.openapispec_paths
        # Next put definitions. In OpenAPI, it is usual for definitions to come after paths
        self.definitions = PresortedOrderedDict()
        self.openapispec['definitions'] = self.definitions
        self.header_parameters = self.build_standard_header_parameters()
        self.openapispec['parameters'] = self.header_parameters
        self.openapispec['responses'] = dict()
        if 'securityDefinitions' in spec:
            self.openapispec['securityDefinitions'] = spec['securityDefinitions']            
        if 'security' in spec:
            self.openapispec['security'] = spec['security']            

        if 'entities' in spec:
            entities = spec['entities']
            self.interfaces = dict()
            self.included_entity_map = self.validator.build_included_entity_map()
            self.openapispec_uri_map = self.oas_definition_map(self.validator)
            self.openapispec['definitions'] = self.definitions
            self.referenced_entities = {entity['id'] for entity in entities.itervalues() if 'wellKnownURLs' in entity}
            self.referenced_entities.update({entity['id'] for entity in entities.itervalues() if 'URL_templates' in entity})                        
            error_response = self.conventions.get('errorResponse')
            if error_response:
                if isinstance(error_response, basestring):
                    self.error_response = self.global_definition_ref(self.abs_url(error_response))                   
                else:
                    self.definitions['ErrorResponse'] = self.conventions['errorResponse']
                    self.openapispec_uri_map[self.abs_url('#ErrorResponse')] = '#/definitions/ErrorResponse'
                    self.error_response = self.global_definition_ref(self.abs_url('#ErrorResponse'))
            else:
                self.error_response = {}
            self.responses = self.build_standard_responses()
            self.response_sets = self.build_standard_response_sets()
            self.methods = self.build_standard_methods()
            for entity_uri, entity_spec in self.entities_and_dependencies_iteritems():
                entity_name = entity_spec['name']
                entity_uri = entity_spec['id']
                entity_url_spec = EntityURLSpec(entity_uri, self)
                interface = self.build_entity_interface(entity_url_spec)
                self.interfaces[entity_uri] = interface
                if entity_uri in self.referenced_entities:
                    self.openapispec_interfaces[entity_url_spec.interface_id()] = interface
                rel_property_specs = self.get_entity_relationship_property_specs(entity_uri, entity_spec)
                for rel_property_spec in rel_property_specs:
                    q_p = QueryPath(rel_property_spec.relationship_name, self)
                    if rel_property_spec.is_collection_resource(): 
                        interface = self.build_relationship_interface(entity_url_spec, q_p, rel_property_spec, rel_property_specs)
                        self.openapispec_interfaces[rel_property_spec.interface_id()] = interface
                        self.interfaces[rel_property_spec.interface_id()] = interface
                    else:
                        self.referenced_entities.update([spec.target_entity_uri for spec in rel_property_specs])        
            for entity_uri, entity_spec in self.entities_and_dependencies_iteritems():
                entity_name = entity_spec['name']
                definition = self.to_openapispec(entity_spec)
                self.definitions[entity_name] = definition
            for entity_spec in entities.itervalues():
                entity_uri = entity_spec['id']
                if 'wellKnownURLs' in entity_spec:
                    for well_known_URL in as_list(entity_spec['wellKnownURLs']):
                        path = well_known_URL[:-1] if well_known_URL.endswith('/') and len(well_known_URL) > 1 else well_known_URL
                        spec = WellKnownURLSpec(path, entity_uri, self)
                        path_spec = spec.build_oas_path_spec()
                        self.openapispec_paths[path] = path_spec
                uri_templates = entity_spec.get('uriTemplates')
                if uri_templates is not None:
                    for uri_template in as_list(uri_templates):
                        spec = URITemplateSpec(uri_template, entity_uri, self)
                        spec.emit_openapi_path()
                rel_property_specs = self.get_entity_relationship_property_specs(entity_uri, entity_spec)
                if self.include_impl and 'permalinkTemplate' in entity_spec:
                    implementation_spec = ImplementationPathSpec(entity_spec['permalinkTemplate'], entity_uri, self)
                    entity_interface = implementation_spec.build_interface_reference()
                    path_spec = implementation_spec.build_oas_path_spec()
                    self.openapispec_paths[implementation_spec.path_segment()] = path_spec
                if 'queryPaths' in entity_spec:
                    query_paths = [QueryPath(query_path, self) for query_path in as_list(entity_spec['queryPaths'])]
                    for rel_property_spec in rel_property_specs:
                        rel_property_spec_stack = [rel_property_spec]
                        if self.include_impl and 'permalinkTemplate' in entity_spec:
                            implementation_spec = ImplementationPathSpec(entity_spec['permalinkTemplate'], entity_uri, self)
                            self.add_query_paths(query_paths[:], implementation_spec, rel_property_spec_stack, rel_property_specs)
                        if 'wellKnownURLs' in entity_spec:
                            qps = query_paths[:]
                            well_known_URLs = as_list(entity_spec['wellKnownURLs'])
                            for well_known_URL in well_known_URLs:
                                baseURL_spec = WellKnownURLSpec(well_known_URL, entity_uri, self)
                                self.add_query_paths(qps, baseURL_spec, rel_property_spec_stack, rel_property_specs)
                        entity_url_property_spec = EntityURLSpec(entity_uri, self)
                        self.add_query_paths(query_paths, entity_url_property_spec, rel_property_spec_stack, rel_property_specs)
                    if len(query_paths) > 0:
                        sys.exit('query paths not valid or listed more than once: %s' % [query_path.openapispec_path_string for query_path in query_paths] )  
        if not self.openapispec_interfaces:
            del self.openapispec['x-interfaces']
        return self.openapispec

    def entities_and_dependencies_iteritems(self):
        for entity_item in self.rapier_spec.get('entities', {}).iteritems():
            yield entity_item
        for entity_item in self.validator.included_entity_iteritems():
            yield entity_item

    def get_one_relationship_property_specs(self, prop_name, property, entity_uri, entity_spec):
        result = []
        relationship = as_relationship(prop_name, property['relationship'])
        upper_multiplicity = relationship.get('multiplicity', '0:1').split(':')[-1]
        multi_valued = upper_multiplicity == 'n' or (upper_multiplicity.isdigit() and int(upper_multiplicity) > 1)
        for target_entity_uri in as_list(relationship['entities']):
            p_spec = (RelMVPropertySpec if multi_valued else RelSVPropertySpec)(self, entity_uri, entity_spec, property, relationship, target_entity_uri)
            result.append(p_spec)
        return result

    def get_entity_relationship_property_specs(self, entity_uri, entity_spec):
        spec = self.rapier_spec
        result = []
        def add_properties(spec):
            if hasattr(spec, 'keys'):
                if '$ref' in spec:
                    add_properties(self.resolve_ref_uri(spec['$ref']))
                elif 'properties' in spec:
                    for prop_name, property in spec['properties'].iteritems():
                        if 'relationship' in property:
                            result.extend(self.get_one_relationship_property_specs(prop_name, property, entity_uri, entity_spec))
                        else:
                            add_properties(property)
                elif 'type' in spec and spec['type'] == 'array':
                    add_properties(spec['items'])
                if 'oneOf' in spec:
                    for o_spec in spec['oneOf']:
                        add_properties(o_spec)
                if 'allOf' in spec:
                    for o_spec in spec['allOf']:
                        add_properties(o_spec)

        add_properties(entity_spec)
        return result
        
    def add_query_paths(self, query_paths, prefix, rel_property_spec_stack, prev_rel_property_specs):
        rapier_spec = self.rapier_spec
        rel_property_spec = rel_property_spec_stack[-1]
        target_entity_uri = rel_property_spec.target_entity_uri
        target_entity_spec = self.validator.resolve_referenced_entity(target_entity_uri)
        if target_entity_spec: # if it is external, it may not be found
            rel_property_specs = self.get_entity_relationship_property_specs(target_entity_uri, target_entity_spec)
            for query_path in query_paths[:]:
                if query_path.matches(rel_property_spec_stack):
                    self.emit_query_path(prefix, query_path, rel_property_spec_stack, prev_rel_property_specs)
                    query_paths.remove(query_path)
            for rel_spec in rel_property_specs:
                if rel_spec not in rel_property_spec_stack:
                    rel_property_spec_stack.append(rel_spec)
                    self.add_query_paths(query_paths, prefix, rel_property_spec_stack, rel_property_specs)
                    rel_property_spec_stack.pop()
                
    def emit_query_path(self, prefix, query_path, rel_property_spec_stack, rel_property_specs):
        for inx, spec in enumerate(rel_property_spec_stack):
            if spec.is_multivalued() and not query_path.query_segments[inx].selects_single_value() and not inx == len(rel_property_spec_stack) - 1:
                sys.exit('query path has multi-valued segment with no parameter: %s' % query_path)
        rel_spec = rel_property_spec_stack[-1]
        is_collection_resource = rel_spec.is_collection_resource() and not query_path.query_segments[-1].selects_single_value()
        interface_id = rel_spec.interface_id() if is_collection_resource else rel_spec.target_entity_uri
        is_private = reduce(lambda x, y: x or y.is_private(), rel_property_spec_stack, False)
        if not is_private or self.include_impl:
            # There are multiple cases for getting here:
            # 1. prefix is an ImplementationPathSpec. We need to create an OAS path (which may or may not reference a template)
            # 2. prefix is an EntityURLSpec. We need to create an OAS template
            # . prefix is a WellKnownURLSpec. We need to create an OAS path (which may or may not reference a template)
            prefix.emit_openapi_element(query_path, rel_spec)

    def build_entity_interface(self, entity_url_spec):
        entity_uri = entity_url_spec.entity_uri
        entity_spec = self.validator.resolve_included_entity(entity_uri)
        parameters = entity_url_spec.build_parameters()
        consumes = as_list(entity_spec['consumes']) if 'consumes' in entity_spec else None 
        produces = as_list(entity_spec['produces']) if 'produces' in entity_spec else None 
        query_parameters = entity_spec.get('queryParameters') 
        structured = 'type' not in entity_spec or entity_spec['type'] == 'object'
        def build_response_200():
            response_200 = {
                'schema': self.global_definition_ref(entity_uri)
                }
            if not self.yaml_merge or propduces and len(produces) > 1:
                response_200.update(self.build_standard_200(produces or self.openapispec.get('produces')))
            else:
                response_200['<<'] = self.responses.get('standard_200')
            return response_200  
        response_200 = build_response_200()
        interface = PresortedOrderedDict()
        if entity_url_spec.is_private():
            interface['x-private'] = True
            x_description = 'This path is NOT part of the API. It is used in the implementaton and may be ' \
                'important to implementation-aware software, such as proxies or specification-driven implementations.'
        else:
            x_description = entity_url_spec.x_description()
        if x_description:
            interface['x-description'] = x_description
        if parameters:
            interface['parameters'] = parameters
        interface['get'] = {
                'description': 'Retrieve %s' % articled(self.validator.resolve_included_entity_name(entity_uri)),
                'parameters': [{'$ref': '#/parameters/Accept'}],
                'responses': {
                    '200': build_response_200(), 
                    }
                }
        if produces:
            interface['get']['produces'] = produces if self.yaml_merge else produces[:]
        if query_parameters:
            interface['get']['parameters'] = [{k: v for d in [{'in': 'query'}, {'name': param_name}, query_parameter] for k, v in d.iteritems()} for param_name, query_parameter in query_parameters.iteritems()]
        if not self.yaml_merge:
            interface['get']['responses'].update(self.build_entity_get_responses())
        else:
            interface['get']['responses']['<<'] = self.response_sets['entity_get_responses']
        usage_set = as_list(entity_spec.get('usage', ['c', 'r', 'u', 'd']))
        usage_set = [v.lower() for v in usage_set]
        if 'readOnly' in entity_spec:
            updatable = False
            deletable = False
        else:
            updatable = len(self.validator.__class__.u_usage_values & set(usage_set)) > 0
            deletable = len(self.validator.__class__.d_usage_values & set(usage_set)) > 0
        if updatable:
            if structured:
                update_verb = 'patch'
                description = 'Update %s entity'
                parameter_ref = '#/parameters/If-Match'
                body_desciption =  'The subset of properties of the %s being updated' % self.validator.resolve_included_entity_name(entity_uri)
            else:
                update_verb = 'put'
                description = 'Create or Update %s entity'
                self.define_put_if_match_header()
                parameter_ref = '#/parameters/Put-If-Match'
                body_desciption =  'The representation of the %s being replaced' % self.validator.resolve_included_entity_name(entity_uri)
            schema = self.global_definition_ref(entity_uri)
            description = description % articled(self.validator.resolve_included_entity_name(entity_uri))
            interface[update_verb] = {
                'description': description,
                'parameters': [
                    {'name': 'body',
                    'in': 'body',
                    'description': body_desciption,
                    'schema': schema,
                    'required': True
                    }
                    ],
                'responses': { 
                    '200': response_200 if self.yaml_merge else build_response_200()
                    }
                }
            if self.use_etag:
                interface[update_verb]['parameters'].insert(0, {'$ref': parameter_ref})
            if not self.yaml_merge:
                interface[update_verb]['responses'].update(self.build_put_patch_responses())
            else:
                interface[update_verb]['responses']['<<'] = self.response_sets['put_patch_responses']
            if structured:
                interface['patch']['consumes'] = self.patch_consumes if self.yaml_merge else self.patch_consumes[:]
            else:
                interface['put']['responses']['201'] = {
                    'description': 'Created new %s' % self.validator.resolve_included_entity_name(entity_uri),
                    'schema': self.global_definition_ref(entity_uri),
                    'headers': {
                        'Location': {
                            'type': 'string',
                            'description': 'perma-link URL of newly-created %s'  % self.validator.resolve_included_entity_name(entity_uri)
                            },
                        'Content-Type': {
                            'type': 'string',
                            'description': 'The media type of the returned body'
                            }
                        }
                    }
                if consumes:
                    interface[update_verb]['consumes'] = consumes

            if produces:
                interface[update_verb]['produces'] = produces if self.yaml_merge else produces[:]
        if deletable:        
            interface['delete'] = {
                'description': 'Delete %s' % articled(self.validator.resolve_included_entity_name(entity_uri)),
                'responses': {
                    '200': response_200
                    }
                }
            if produces:
                interface['delete']['produces'] = produces if self.yaml_merge else produces[:]
            if not self.yaml_merge:
                interface['delete']['responses'].update(self.build_delete_responses())
            else:
                interface['delete']['responses']['<<'] = self.response_sets['delete_responses']
        interface['head'] = {
                'description': 'retrieve HEAD'
                }
        if not self.yaml_merge:
            interface['head'].update(self.build_head_method())
        else:
            interface['head']['<<'] = self.methods['head']
        interface['options'] = {
                'description': 'Retrieve OPTIONS',
               }
        if not self.yaml_merge:
            interface['options'].update(self.build_options_method())
        else:
            interface['options']['<<'] = self.methods['options']  
        interface['x-id'] = entity_url_spec.interface_id()
        return interface

    def build_relationship_interface(self, entity_url_spec, query_path, rel_property_spec, rel_property_specs):
        parameters = entity_url_spec.build_parameters(query_path) 
        relationship_name = rel_property_spec.relationship_name
        entity_uri = rel_property_spec.target_entity_uri
        entity_spec = self.validator.resolve_referenced_entity(entity_uri)
        interface = PresortedOrderedDict()
        is_private = rel_property_spec.is_private() or entity_url_spec.is_private()
        if is_private:
            interface['x-private'] = True            
        if parameters:
            interface['parameters'] = parameters
        produces = self.openapispec.get('produces')
        if rel_property_spec.readable():
            interface['get'] = self.build_collection_get(rel_property_spec, produces)
        rel_property_specs = [spec for spec in rel_property_specs if spec.relationship_name == relationship_name]
        consumes_entities = [entity for spec in rel_property_specs for entity in spec.consumes_entities]
        consumes_media_types = [media_type for spec in rel_property_specs if spec.consumes_media_types for media_type in spec.consumes_media_types]
        self.referenced_entities.update([spec.target_entity_uri for spec in rel_property_specs])
        if rel_property_spec.postable():
            if len(rel_property_specs) > 1:
                schema = {}
                schema['x-oneOf'] = [self.referenced_definition_ref(spec.target_entity_uri) for spec in rel_property_specs]
                i201_description = 'Created new %s' % ' or '.join([self.validator.resolve_referenced_entity_name(spec.target_entity_uri) for spec in rel_property_specs])
                location_desciption =  'perma-link URL of newly-created %s' % ' or '.join([self.validator.resolve_referenced_entity_name(spec.target_entity_uri) for spec in rel_property_specs])
                body_desciption =  'The representation of the new %s being created' % ' or '.join([self.validator.resolve_referenced_entity_name(spec.target_entity_uri) for spec in rel_property_specs])
            else:    
                schema = self.referenced_definition_ref(entity_uri)
                i201_description = 'Created new %s' % self.validator.resolve_referenced_entity_name(entity_uri)
                location_desciption = 'perma-link URL of newly-created %s'  % self.validator.resolve_referenced_entity_name(entity_uri)
                body_desciption =  'The representation of the new %s being created' % self.validator.resolve_referenced_entity_name(entity_uri) 
            if len(consumes_entities) > 1:
                post_schema = {}
                post_schema['x-oneOf'] = [self.referenced_definition_ref(consumes_entity) for consumes_entity in consumes_entities]
                description = 'Create a new %s' % ' or '.join([self.validator.resolve_referenced_entity_name(rel_prop_spec.target_entity_uri) for rel_prop_spec in rel_property_specs])
            else:
                post_schema = self.referenced_definition_ref(consumes_entities[0])
                description = 'Create a new %s' % self.validator.resolve_referenced_entity_name(consumes_entities[0])
            interface['post'] = {
                'description': description,
                'parameters': [
                    {'name': 'body',
                     'in': 'body',
                     'description': body_desciption,
                     'schema': post_schema,
                     'required': True
                    },
                    {'name': 'Content-Type',
                     'in': 'header',
                     'required': True,
                     'description': 'The media type of the body',
                     'type': 'string'
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
                            'Content-Type': {
                                'type': 'string',
                                'description': 'The media type of the returned body'
                                }                                
                            }
                        }
                    }                
                }
            if self.use_etag:
                interface['post']['responses']['201']['headers']['ETag'] = {
                     'type': 'string',
                     'description': 'Value of ETag required for subsequent updates'
                    }
            if self.include_impl and produces and len(produces)> 1:
                interface['post']['responses']['201']['headers']['Vary'] = {
                    'type': 'string',
                    'enum': ['Accept'],
                    'description': 'Make sure a cache of one content type is not returned to a client wanting a different one.'
                    }
            if consumes_media_types:
                interface['post']['consumes'] = consumes_media_types
            if not self.yaml_merge:
                interface['post']['responses'].update(self.build_post_responses())
            else:
                interface['post']['responses']['<<'] = self.response_sets['post_responses']
        if rel_property_spec.readable():
            interface['head'] = {
                    'description': 'Retrieve HEAD'
                    }
            if not self.yaml_merge:
                interface['head'].update(self.build_head_method())
            else:
                interface['head']['<<'] = self.methods['head']
        interface['options'] = {
                'description': 'Retrieve OPTIONS',
            }
        if not self.yaml_merge:
            interface['options'].update(self.build_options_method())
        else:
            interface['options']['<<'] = self.methods['options']  
        interface['x-id'] = rel_property_spec.interface_id()
        return interface

    def build_entity_get_responses(self):
        return  {
            '401': self.global_response_ref('401'), 
            '403': self.global_response_ref('403'), 
            '404': self.global_response_ref('404'), 
            '406': self.global_response_ref('406'), 
            'default': self.global_response_ref('default')
            }
                    
    def build_put_patch_responses(self):
        rslt = {
            '400': self.global_response_ref('400'),
            '401': self.global_response_ref('401'), 
            '403': self.global_response_ref('403'), 
            '404': self.global_response_ref('404'), 
            '406': self.global_response_ref('406'), 
            '409': self.global_response_ref('409'), 
            'default': self.global_response_ref('default')
            } 
        if self.use_etag:
            rslt['412'] = self.global_response_ref('412')
        return rslt

    def build_delete_responses(self):
        return  {
            '400': self.global_response_ref('400'),
            '401': self.global_response_ref('401'), 
            '403': self.global_response_ref('403'), 
            '404': self.global_response_ref('404'), 
            '406': self.global_response_ref('406'), 
            'default': self.global_response_ref('default')
            }

    def build_post_responses(self):
        return  {
            '400': self.global_response_ref('400'),
            '401': self.global_response_ref('401'), 
            '403': self.global_response_ref('403'), 
            '404': self.global_response_ref('404'), 
            '406': self.global_response_ref('406'), 
            '409': self.global_response_ref('409'), 
            'default': self.global_response_ref('default')
            }

    def build_standard_response_sets(self):
        result = dict()
        result['entity_get_responses'] = self.build_entity_get_responses
        result['put_patch_responses'] = self.build_put_patch_responses()
        result['delete_responses'] = self.build_delete_responses()
        result['post_responses'] = self.build_post_responses()
        return result

    def build_head_method(self):
        return {            
            'responses': {
                '200': self.global_response_ref('standard_200'), 
                '401': self.global_response_ref('401'), 
                '403': self.global_response_ref('403'), 
                '404': self.global_response_ref('404'), 
                'default': self.global_response_ref('default')
                }
            }
        
    def build_options_method(self):
        return {            
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
        
    def build_standard_methods(self):
        result = dict()
        result['head'] = self.build_head_method()
        result['options'] = self.build_options_method()
        return result

    def global_response_ref(self, key):
        if key not in self.openapispec['responses']:
             self.openapispec['responses'][key] = self.responses[key]
        return {'$ref': '#/responses/%s' % key}

    def global_definition_ref(self, key):
        return {'$ref': self.openapispec_uri_map[key]}
        
    def referenced_definition_ref(self, key):
        if key in self.openapispec_uri_map:
            return {'$ref': self.openapispec_uri_map[key]}
        else: 
            #print >> sys.stderr, 'need to handle references to entities in external files'
            #print key
            abs_filename, entityname = key.split('#')
            for validator in self.validator.referenced_spec_validators.itervalues():
                if abs_filename == validator.abs_filename:
                    filename_parts = validator.filename.split('.')
                    if len(filename_parts) > 1:
                        filename_parts.insert(-1, 'oas')
                    else:
                        filename_parts.append('oas')
                    return {'$ref': '%s#/definitions/%s' % ('.'.join(filename_parts), entityname)}
            print 'internal error - failed to resolve reference %s' % key
            sys.exit(-1)
        
    def build_standard_200(self, produces=None):
        rslt = {
            'description': 'successful',
            'headers': {
                'Content-Location': {
                    'type': 'string',
                    'description': 'perma-link URL of resource'
                    },
                'Content-Type': {
                    'type': 'string',
                    'description': 'The media type of the returned body'
                    }
                }
            }
        if self.use_etag:
            rslt['headers']['ETag'] = \
                {'description': 'this value must be echoed in the If-Match header of every PATCH or PUT',
                 'type': 'string'
                }
        if self.include_impl and produces and len(produces)> 1:
            rslt['headers']['Vary'] = {
                'type': 'string',
                'enum': ['Accept'],
                'description': 'Make sure a cache of one content type is not returned to a client wanting a different one.'
                }
        return rslt

    def build_standard_responses(self):
        rslt = {
            'standard_200': self.build_standard_200(),
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
                'schema': self.error_response if self.yaml_merge else self.error_response.copy() 
                },
            '401': {
                'description': 'Unauthorized. Client authentication token missing from request',
                'schema': self.error_response if self.yaml_merge else self.error_response.copy()
                }, 
            '403': {
                'description': 'Forbidden. Client authentication token does not permit this method on this resource',
                'schema': self.error_response if self.yaml_merge else self.error_response.copy()
                }, 
            '404': {
                'description': 'Not Found. Resource not found',
                'schema': self.error_response if self.yaml_merge else self.error_response.copy()
                }, 
            '406': {
                'description': 'Not Acceptable. Requested media type not available',
                'schema': self.error_response if self.yaml_merge else self.error_response.copy()
                }, 
            '409': {
                'description': 'Conflict. May be a duplicate',
                'schema': self.error_response if self.yaml_merge else self.error_response.copy()
                }, 
            'default': {
                'description': '5xx errors and other stuff',
                'schema': self.error_response if self.yaml_merge else self.error_response.copy()
                }
            }
        if self.use_etag: 
            rslt['412'] = \
                {'description': 'Precondition Failed. Value provided in If-Match header does not match current ETag value of resource',
                 'schema': self.error_response if self.yaml_merge else self.error_response.copy()
                }
        return rslt
        
    def build_collection_get(self, rel_property_spec, produces):
        collection_entity_uri = rel_property_spec.collection_resource
        if not collection_entity_uri:
            sys.exit('must provide collection_resource for property %s in entity %s in spec %s' % (rel_property_spec.relationship_name, rel_property_spec.source_entity_name(), self.validator.filename))
        collection_entity = self.validator.resolve_included_entity(collection_entity_uri)
        if collection_entity is None:
            sys.exit('error: must define entity %s' % collection_entity_uri)   
        rslt = {
            'responses': {
                '200': {
                    'description': 'description',
                    'schema': json_ref(self.openapispec_uri_map[collection_entity_uri]),
                    'headers': {
                        'Content-Location': {
                            'type': 'string',
                            'description': 'perma-link URL of collection'
                            },
                        'Content-Type': {
                            'type': 'string',
                            'description': 'The media type of the returned body'
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
        if self.include_impl and produces and len(produces)> 1:
            rslt['responses']['200']['headers']['Vary'] = {
                'type': 'string',
                'enum': ['Accept'],
                'description': 'Make sure a cache of one content type is not returned to a client wanting a different one.'
                }
        def add_query_parameters(entity, query_params):
            if 'queryParameters' in entity:
                params = entity['queryParameters']
                for param_name, param in params.iteritems():
                    new_param = dict()
                    new_param.update(param)
                    if 'enum' in param:
                        new_param['enum'] = param['enum'][:]
                    if 'items' in param:
                        new_param['items'] = param['items'].copy()
                    new_param['name'] = param_name
                    new_param['in'] = 'query'
                    query_params[param_name] = new_param
            if 'oneOf' in entity:
                for entity_ref in entity['oneOf']:
                    add_query_parameters(self.validator.resolve_included_entity_ref(entity_ref), query_params) 
        query_parameters = dict()
        add_query_parameters(collection_entity, query_parameters)
        if 'queryParameters' in rel_property_spec.relationship:
            add_query_parameters(rel_property_spec.relationship, query_parameters)
        if query_parameters:
            rslt['parameters'] = query_parameters.values()
        return rslt        
 
    def define_put_if_match_header(self):
        if self.use_etag and not 'Put-If-Match' in self.header_parameters:
            self.header_parameters['Put-If-Match'] = {
                'name': 'If-Match',
                'in': 'header',
                'type': 'string',
                'description': 'specifies the last known ETag value of the resource being modified',
                'required': False
                }
    
    def build_standard_header_parameters(self):
        rslt = {
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
        if self.use_etag:
            rslt['If-Match'] = {
                'name': 'If-Match',
                'in': 'header',
                'type': 'string',
                'description': 'specifies the last known ETag value of the resource being modified',
                'required': True
                }
        return rslt
                
    def resolve_ref_uri(self, ref_uri):
        if ref_uri.startswith('#/'):
            parts = ref_uri[2:].split('/')
            spec = self.rapier_spec
            for part in parts:
                if part not in spec:
                    sys.exit('%s not in %s' % (ref_uri, self.filename))
                spec = spec[part]
            return spec
        else:
            return self.resolve_included_entity(ref_uri)
    
    def resolve_included_entity(self, uri):
        return self.included_entity_map[self.abs_url(uri)]

    def resolve_included_entity_ref(self, ref):
        return self.resolve_included_entity(ref['$ref'])

    def resolve_included_entity_name(self, uri):
        return self.resolve_included_entity(uri)['name']

    def resolve_property(self, entity_uri, property_name):
        entity = self.resolve_included_entity(entity_uri)
        if not entity:
            return None
        if 'properties' in entity:
            if property_name in entity['properties']:
                return entity['properties'][property_name]
        if 'allOf' in entity:
            for entity_ref in entity['allOf']:
                property = self.resolve_property(entity_ref['$ref'], property_name)
                if property:
                    return property

    def to_openapispec(self, node, entity_spec=None, property_name=None):
        if hasattr(node, 'keys'):
            result = PresortedOrderedDict()
            for k, v in node.iteritems():
                if k == 'oneOf':
                    result['x-oneOf'] = self.to_openapispec(v, entity_spec, property_name)
                elif k == 'allOf':
                    result['allOf'] = self.to_openapispec(v, entity_spec, property_name)
                elif k == '$ref':
                    result['$ref'] = self.openapispec_uri_map[v]
                elif k == 'type':
                    result['type'] = self.to_openapispec(v, entity_spec, property_name)
                elif k == 'items':
                    result['items'] = self.to_openapispec(v, entity_spec, property_name)
                elif k == 'format':
                    result['format'] = self.to_openapispec(v, entity_spec, property_name)
                elif k == 'enum':
                    result['enum'] = v
                elif k == 'description':
                    result['description'] = v
                elif k == 'required':
                    result['required'] = v
                elif k == 'readOnly':
                    result['readOnly'] = v
                elif k == 'properties':
                    oas_properties = PresortedOrderedDict()
                    for k2, v2 in v.iteritems():
                        if not v2.get('implementation_private', False):
                            oas_properties[k2] = self.to_openapispec(v2, entity_spec or node, k2)
                    result['properties'] = oas_properties
                elif k == 'relationship':
                    rel_property_specs = self.get_one_relationship_property_specs(property_name, node, entity_spec['id'], entity_spec)
                    if len(rel_property_specs) > 1 and not rel_property_specs[0].is_multivalued():
                        result['x-interface'] = {'oneOf': [rel_property_spec.build_interface_reference()['$ref'] for rel_property_spec in rel_property_specs]}
                    else:
                        result['x-interface'] = rel_property_specs[0].build_interface_reference()['$ref']
                elif k == 'id' and v in self.referenced_entities:
                    result['x-interface'] = EntityURLSpec(v, self).build_interface_reference()['$ref']
            return result
        elif isinstance(node, list):
            return [self.to_openapispec(i, entity_spec, property_name) for i in node]
        else:
            return node
        
    def abs_url(self, url):
        split_url = url.split('#')
        split_url[0] = os.path.abspath(os.path.join(self.validator.abs_filename, split_url[0]))
        return '#'.join(split_url)
     
    def oas_definition_map(self, validator):
        entities = validator.rapier_spec.get('entities', {})
        result = {'%s#/entities/%s' % (validator.abs_filename, name): '#/definitions/%s' % name for name in entities.iterkeys()}
        result.update({entity['id']: '#/definitions/%s' % name for name, entity in entities.iteritems()})
        for nested_validator in validator.included_spec_validators.itervalues():
            result.update(self.oas_definition_map(nested_validator))
        return result
            
class SegmentSpec(object):
            
    def __init__(self, generator, entity_uri, entity_spec, property, relationship, target_entity_uri):
        self._generator = generator   
        self._entity_uri = entity_uri                   
        self._entity_spec = entity_spec      
        self._property = property
        self.relationship = relationship
        self.target_entity_uri = target_entity_uri

        self.readOnly = relationship.get('readOnly')                                 
        self.relationship_name = relationship['name']        
        self.implementation_private = property.get('implementation_private', False)    

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.__dict__.hash()

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__, self.__dict__.__str__())

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(['%s=%s' % item for item in self.__dict__.iteritems()]))

    def build_interface_reference(self):
        path = self.interface_id()
        path = path.replace('~', '~0')
        path = path.replace('/', '~1')
        for entity in self._generator.rapier_spec['entities'].itervalues():
            if entity['id'] == self.target_entity_uri:
                break
        else:
            entity = None        
        if entity is not None:
            if path not in self._generator.openapispec_interfaces: 
                self._generator.openapispec_interfaces[path] = self._generator.interfaces[self.target_entity_uri]
            return {'$ref': '#/x-interfaces/%s' % path}
        else:
            split_entity_uri = self.target_entity_uri.split('#')
            rel_path = self._generator.validator.relative_url(split_entity_uri[0])
            return {'$ref': '%s#/x-interfaces/%s' % (rel_path, path)}
        
class RelSVPropertySpec(SegmentSpec):
    
    def __init__(self, generator, entity_uri, entity_spec, property, relationship, target_entity_uri):
        super(RelSVPropertySpec, self).__init__(generator, entity_uri, entity_spec, property, relationship, target_entity_uri)
        
    def is_multivalued(self):
        return False
        
    def is_collection_resource(self):
        return False
        
    def get_multiplicity(self):
        return self.multiplicity
                
    def is_private(self):
        return self.implementation_private

    def source_entity_name(self):
        return self._entity_spec['name']
        
    def interface_id(self):
        return self.target_entity_uri.split('#')[1]

    def template_id(self):
        return '{%s-URL}' % self._generator.resolve_referenced_entity_name(self._entity_uri)
      
class RelMVPropertySpec(SegmentSpec):
    
    def __init__(self, generator, entity_uri, entity_spec, property, relationship, target_entity_uri):
        super(RelMVPropertySpec, self).__init__(generator, entity_uri, entity_spec, property, relationship, target_entity_uri)
        self._collection_resource = relationship.get('collectionResource', True)        
        self._consumes = relationship.get('consumes')

        self.consumes_media_types = self._consumes.keys() if isinstance(self._consumes, dict) else as_list(self._consumes) if self._consumes is not None else None
        self.consumes_entities = [entity for entity_list in self._consumes.values() for entity in as_list(entity_list)] if isinstance(self._consumes, dict) else [target_entity_uri]
        self.collection_resource = relationship.get('collectionResource')        

    def readable(self):
        usage = self.relationship.get('usage')
        if usage is None:
            return True
        else:
            return len(validate_rapier.OASValidator.r_usage_values & set(as_list(usage))) > 0
    
    def postable(self):
        usage = self.relationship.get('usage')
        if usage is None:
            return not self.relationship.get('readOnly', False)
        else:
            return len(validate_rapier.OASValidator.c_usage_values & set(as_list(usage))) > 0
        
    def is_multivalued(self):
        return True
        
    def is_private(self):
        return self.implementation_private
        
    def is_collection_resource(self):
        return not not self._collection_resource
            
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

    def interface_id(self):
        return '%s.%s' % (self._entity_spec['name'], self.relationship_name)
        
    def source_entity_name(self):
        return self._entity_spec['name']
        
    def build_interface_reference(self):
        path = self.interface_id()
        path = path.replace('~', '~0')
        path = path.replace('/', '~1')
        return {'$ref': '#/x-interfaces/%s' % path}
        
class PathPrefix(object):
            
    def __init__(self, entity_uri, generator):
        self.entity_uri = entity_uri
        self.generator = generator

    def build_params(self):
        return []  
        
    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.__dict__.hash()

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(['%s=%s' % item for item in self.__dict__.iteritems()]))
        
    def x_description(self):
        return None
        
    def is_private(self):
        return False
        
    def is_uri_spec(self):
        return False
        
    def is_impl_spec(self):
        return False
        
    def interface_id(self):
        return self.entity_uri.split('#')[1]
      
    def template_id(self):
        return '{%s-URL}' % self.interface_id()
        
    def build_parameters(self, query_path=None):
        result = self.build_params()
        if query_path:
            result.extend(query_path.build_parameters())
        return result
                
    def build_interface_reference(self):
        path = self.interface_id()
        path = path.replace('~', '~0')
        path = path.replace('/', '~1')
        for entity in self.generator.rapier_spec['entities'].itervalues():
            if entity['id'] == self.entity_uri:
                break
        else:
            entity = None        
        if entity is not None:
            if path not in self.generator.openapispec_interfaces: 
                self.generator.openapispec_interfaces[path] = self.generator.interfaces[self.entity_uri]
            return {'$ref': '#/x-interfaces/%s' % path}
        else:
            split_entity_uri = self.entity_uri.split('#')
            rel_path = self.generator.validator.relative_url(split_entity_uri[0])
            return {'$ref': '%s#/x-interfaces/%s' % (rel_path, path)}

    def build_template_reference(self, query_path=None):
        template_id = self.template_id()
        path = template_id
        if query_path:
            path = '/'.join([path, query_path.openapispec_path_string])
        path = path.replace('~', '~0')
        path = path.replace('/', '~1')
        rslt = {'$ref': '#/x-templates/%s' % path}
        if template_id not in self.generator.openapispec_templates:
            self.generator.openapispec_templates[template_id] = self.build_interface_reference()
        return rslt            

    def build_interface_ref_with_params(self, interface_id=None, rel_spec=None, query_path=None):
        interface_id = interface_id or self.entity_uri
        oas_interface_id = interface_id.split('#')[-1]
        rel_spec = rel_spec or self
        parameters = self.build_parameters(query_path)
        if parameters:
            path_spec = PresortedOrderedDict()
            path_spec['parameters'] = parameters
            path_spec['<<'] = self.generator.interfaces[interface_id]
            if oas_interface_id not in self.generator.openapispec_interfaces: 
                self.generator.openapispec_interfaces[oas_interface_id] = self.generator.interfaces[interface_id]
        else:
            path_spec = rel_spec.build_interface_reference()
        return path_spec
                
    def build_oas_path_spec(self, interface_id=None, path_spec=None, query_path=None):
        interface_id = interface_id or self.entity_uri
        if self.generator.use_templates:
            oas_path_spec = self.build_template_reference(query_path)
        else:
            oas_path_spec = self.build_interface_ref_with_params(interface_id, path_spec or self, query_path)
        return oas_path_spec

    def emit_openapi_path(self, query_path, rel_spec):
        is_collection_resource = rel_spec.is_collection_resource() and not query_path.query_segments[-1].selects_single_value()
        interface_id = rel_spec.interface_id() if is_collection_resource else rel_spec.target_entity_uri
        path = '/'.join([self.path_segment(), query_path.openapispec_path_string])
        if path not in self.generator.openapispec_paths:
            path_spec = self.build_oas_path_spec(interface_id, rel_spec, query_path)
            self.generator.openapispec_paths[path] = path_spec
       
    def emit_openapi_template(self, query_path, rel_spec):
        is_collection_resource = rel_spec.is_collection_resource() and not query_path.query_segments[-1].selects_single_value()
        interface_id = rel_spec.interface_id() if is_collection_resource else rel_spec.target_entity_uri
        path = '/'.join([self.template_id(), query_path.openapispec_path_string])
        if path not in self.generator.openapispec_templates:
            path_spec = self.build_interface_ref_with_params(interface_id, rel_spec, query_path)        
            self.generator.openapispec_templates[path] = path_spec

class WellKnownURLSpec(PathPrefix):
    
    def __init__(self, base_URL, entity_uri, generator):
        self.base_URL = base_URL 
        self.entity_uri = entity_uri
        self.generator = generator

    def path_segment(self, select_one_of_many = False):
        return self.base_URL[:-1] if self.base_URL.endswith('/') and len(self.base_URL) > 0 else self.base_URL

    def build_params(self):
        formatter = string.Formatter()
        param_names = [part[1] for part in formatter.parse(self.base_URL) if part[1] is not None]
        return [{
                'name': param_name,
                'in': 'path',
                'type': 'string',
                'required': True
                } for param_name in param_names]

    def build_oas_path_spec(self, interface_id=None, path_spec=None, query_path=None):
        interface_id = interface_id or self.entity_uri
        parameters = self.build_parameters() 
        if parameters: # putting parameters in a Well_known_URL is not really kosher
            if self.generator.use_templates:
                self.build_template_reference(query_path)
            parameters = self.build_parameters(query_path)
            oas_path_spec = PresortedOrderedDict()
            oas_path_spec['parameters'] = parameters
            oas_path_spec['<<'] = self.generator.interfaces[interface_id]
        else:
            oas_path_spec = super(WellKnownURLSpec, self).build_oas_path_spec(interface_id, path_spec, query_path)
        return oas_path_spec

    def emit_openapi_element(self, query_path, rel_spec):
        self.emit_openapi_path(query_path, rel_spec)
                
class URITemplateSpec(PathPrefix):
    
    TEMPLATE = re.compile("{([^\}]+)}")
    OPERATOR = "+#./;?&|!@"

    def __init__(self, uri_template, entity_uri, generator):
        self.uri_template = uri_template if hasattr(uri_template, 'keys') else {'template': uri_template}
        self.template_string = self.uri_template['template'] 
        self.template_variables = self.uri_template.get('variables', {})
        self.entity_uri = entity_uri
        self.generator = generator
        split = self.template_string.split('{?')
        if len(split) > 1:
            self._path_id = split[0]
        else:
            self._path_id = self.template_string.split('{?')

    def emit_openapi_path(self):
        if self.template_string not in self.generator.openapispec_templates:
            path_spec = self.build_interface_ref_with_params()        
            self.generator.openapispec_templates[self.template_string] = path_spec
        path_spec = self.build_template_reference()
        self.generator.openapispec_paths[self._path_id] = path_spec
       
    def template_id(self):
        return self.template_string
       
    def build_parameters(self, query_path=None):
        parameters = []
        is_query = False
        parts = self.__class__.TEMPLATE.split(self.template_string)
        for text, expression in zip(parts[::2], parts[1::2]):
            is_query = is_query or '?' in text
            if expression[0] in self.__class__.OPERATOR:
                varlist = expression[1:]
            else:
                varlist = expression
            varspecs = varlist.split(',')
            for var in varspecs:
                param = self.template_variables.get(var, {})
                # handle prefix values
                var_split = var.split(':')
                var = var_split[0]
                if len(var_split) > 1:
                    param['maxLength'] = int(var_split[1])
                # handle composite values
                if var.endswith('*'):
                    var = var[:-1]
                    param.setdefault('type', 'array') #in rfc6570 could also be a map
                    param['items'] = {'type': 'string'}
                else:
                    param.setdefault('type', 'string')
                param['name'] = var
                param['in'] = 'query' if is_query or expression[0] == '?' else 'path'
                parameters.append(param)
        return parameters

class ImplementationPathSpec(PathPrefix):
    
    def __init__(self, permalink_template, entity_uri, generator):
        self.permalink_template = permalink_template if hasattr(permalink_template, 'keys') else {'template': permalink_template}
        self.entity_uri = entity_uri
        self.generator = generator
        template = self.permalink_template['template']
        formatter = string.Formatter()
        try:
            parsed_format = list(formatter.parse(template))
        except Exception as e:
            sys.exit('error parsing permalinkTemplate template: %s e:' % (template, e))
        leading_parts = [part for part in parsed_format if part[1] is not None]
        if len(leading_parts) != 1:
            sys.exit('permalinkTemplate template %s must include exactly one {name} element after ;' % query_path_segment_string)
        else:
            part = leading_parts[0]
        if part[1] == '':
            self.error('property name required between {} characters after %s in permalinkTemplate template %s' %(leading_parts[0] ,query_path_segment_string))
        else:
            self.implementation_url_variable_name = part[1]

    def path_segment(self, select_one_of_many = False):
        return self.permalink_template['template']

    def build_params(self):
        return [{
            'name': self.implementation_url_variable_name,
            'description': self.permalink_template.get('variables',{}).get(self.implementation_url_variable_name,{}).get('description','This parameter is a private part of the implementation. It is not part of the API'),
            'in': 'path',
            'type': self.permalink_template.get('variables',{}).get(self.implementation_url_variable_name,{}).get('type','string'),
            'required': True
            }]
        
    def is_private(self):
        return True

    def is_impl_spec(self):
        return True
        
    def build_template_reference(self, query_path=None):
        rslt = super(ImplementationPathSpec, self).build_template_reference(query_path)
        rslt['x-description'] = self.permalink_template.get('description', '*** This path is not part of the API - it is an implementation-private extension')        
        return rslt            

    def build_oas_path_spec(self, interface_id=None, path_spec=None, query_path=None):
        interface_id = interface_id or self.entity_uri        
        parameters = self.build_parameters() 
        if parameters: 
            if self.generator.use_templates:
                self.build_template_reference(query_path)
            parameters = self.build_parameters(query_path)
            oas_path_spec = PresortedOrderedDict()
            oas_path_spec['x-description'] = self.permalink_template.get('description', '*** This path is not part of the API - it is an implementation-private extension')
            oas_path_spec['parameters'] = parameters
            oas_path_spec['<<'] = self.generator.interfaces[interface_id]
        else:
            oas_path_spec = super(ImplementationPathSpec, self).build_oas_path_spec(interface_id, path_spec, query_path)
            oas_path_spec['x-description'] = self.permalink_template.get('description', '*** This path is not part of the API - it is an implementation-private extension')
        return oas_path_spec

    def emit_openapi_element(self, query_path, rel_spec):
        self.emit_openapi_path(query_path, rel_spec)
                
class EntityURLSpec(PathPrefix):
    
    def __init__(self, entity_uri, generator):
        self.entity_uri = entity_uri
        self.generator = generator

    def path_segment(self, select_one_of_many = False):
        return self.generator.resolve_referenced_entity_name(self.entity_uri)

    def build_params(self):
        return []
            
    def is_uri_spec(self):
        return True

    def emit_openapi_element(self, query_path, rel_spec):
        if self.generator.use_templates:
            self.emit_openapi_template(query_path, rel_spec)
 
class QueryPath(object):

    def __init__(self, query_path, generator):
        self.query_path = query_path
        self.query_segments = list()
        segments = query_path['segments'] if hasattr(query_path, 'keys') else query_path.split('/')
        for segment in segments:
            self.query_segments.append(QuerySegment(segment, self.query_segments, generator))
        self.openapispec_path_string = '/'.join([query_segment.openapispec_segment_string for query_segment in self.query_segments])
            
    def matches(self, rel_stack):
        if len(self.query_segments) == len(rel_stack):
            for segment, rel_spec in itertools.izip(self.query_segments, rel_stack):
                if segment.relationship != rel_spec.relationship_name:
                    return False
            for segment, rel_spec in itertools.izip(self.query_segments, rel_stack):
                segment.rel_property_spec = rel_spec            
            return True
        else:
            return False
            
    def __str__(self):
        return str(self.query_path)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(['%s=%s' % item for item in self.__dict__.iteritems()]))
        
    def build_parameters(self):
        result = []
        for query_segment in self.query_segments:
            result.extend(query_segment.build_params())
        return result
        
class QuerySegment(object):

    def __init__(self, query_segment, query_segments, generator):
        self.generator = generator
        if hasattr(query_segment, 'keys'):
            self.relationship = query_segment['relationship']
            self.relationship_separator = query_segment.get('separator', generator.relationship_separator)
            self.selectors = as_selectors(query_segment.get('selectors', []))
            upper_multiplicity = query_segment.get('multiplicity', '0:1').split(':')[-1]
            self.is_multivalued = upper_multiplicity == 'n' or (upper_multiplicity.isdigit() and int(upper_multiplicity) > 1)
            if 'selector_template' in query_segment:
                selector_template = query_segment['selector_template']
            else:
                if len(self.selectors) == 1:
                    selector_template = '{%s}'
                    self.selectors[0]['brace_offset'] = 1
                elif len(self.selectors) > 1:
                    brace_offset = 0
                    template = ''
                    for inx, selector in enumerate(self.selectors):
                        if inx > 0:
                            template += '&'
                        template = template + selector['property'] + '={%s}'
                        selector['open_brace_offset'] = len(template) -1
                    selector_template = template
        else:
            parts = query_segment.split(';')
            self.relationship_separator = generator.relationship_separator
            if len(parts) == 1:
                self.selector_property_name = None
                self.selectors = []    
            elif len(parts) == 2:
                params_part = parts[1]
                formatter = string.Formatter()
                try:
                    parsed_format = list(formatter.parse(params_part))
                    self.selectors = [{
                        'property': parsed_format_part[1],
                        'openapispec_param': parsed_format_part[1]
                        } for parsed_format_part in parsed_format if parsed_format_part[1] is not None] 
                    if len(self.selectors) == 0:
                        sys.exit('query segment %s must include {} element after ;' % query_segment)
                    selector_template = ''.join([part[0] if part[1] is None else part[0] + '{%s}'%inx for inx, part in enumerate(parsed_format)])
                except ValueError as e:
                    sys.exit('error parsing query path segment: %s' % e)
            else:
                sys.exit('query path segment contains more than 1 ; - %s' % query_segment_string)
            self.relationship = parts[0]
            self.is_multivalued = False
        for selector in self.selectors:
            duplicate_count = len([selector['property'] == disc['openapispec_param'] for qs in query_segments for disc in qs.selectors])
            selector['openapispec_param'] = '_'.join((selector['openapispec_param'], str(duplicate_count))) if duplicate_count > 0 else selector['property']
        if len(self.selectors) > 0:
            params_part = selector_template.format(*['{%s}'%disc['openapispec_param'] for disc in self.selectors])
            self.openapispec_segment_string = self.relationship_separator.join((self.relationship, params_part))
        else:
            self.openapispec_segment_string = self.relationship

    def build_params(self):
        if len(self.selectors) > 0:
            result = []
            for selector in self.selectors:
                property = self.generator.resolve_property(self.rel_property_spec.target_entity_uri, selector['property'])
                if not property:
                    sys.exit('Property named %s not found in Entity %s in file %s' % (selector['property'], self.rel_property_spec.target_entity_uri, self.generator.validator.filename))
                rslt = {
                    'name': selector['openapispec_param'],
                    'in': 'path',
                    'type': property['type'],
                    'required': True
                    } 
                if property['type'] == 'array':
                    rslt['items'] =  property['items']
                if self.rel_property_spec.implementation_private:
                    rslt['description'] = 'This parameter is a private part of the implementation. It is not part of the API'
                result.append(rslt)
            return result
        else:
            return []
            
    def selects_single_value(self):
        return len(self.selectors) > 0 and not self.is_multivalued

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(['%s=%s' % item for item in self.__dict__.iteritems()]))

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, ', '.join(['%s=%s' % item for item in self.__dict__.iteritems()]))
        
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
    
def as_relationship(property_name, input):
    if hasattr(input, 'keys'):
        if not 'name' in input:
            result = {'name': property_name}
            result.update(input)
            return result
        else:
            return input
    else:
        return {
            'entities': input,
            'name': property_name
            }

def as_selectors(input):
    if isinstance(input, list):
        return input[:]
    else:
        return [{'property': property_name} for property_name in as_list(input)]       
        
class CustomAnchorDumper(yaml.SafeDumper):

    def generate_anchor(self, node):
        if node.__class__.id == 'mapping':
            d = {item[0].value: item[1].value for item in node.value \
                if  item[0].__class__.id == 'scalar' and item[1].__class__.id == 'scalar'} 
            if 'x-id' in d:
                return re.sub('[^a-zA-Z0-9]', '-', d['x-id'])
        anchor =  super(CustomAnchorDumper, self).generate_anchor(node)
        return anchor

def main(args):
    generator = OASGenerator()
    usage = 'usage: gen_openapispec.py [-m, --yaml-merge] [-i, --include-impl] [-t --suppress-templates] filename'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'mit', ['yaml-merge', 'include-impl', 'suppress-templates'])
    except getopt.GetoptError as err:
        sys.exit(str(err) + '\n' + usage)
    if not len(args) == 1:
        sys.exit(usage)        
    generator.set_opts(opts)
    Dumper = CustomAnchorDumper
    opts_keys = [k for k,v in opts]
    if False: #'--yaml-alias' not in opts_keys and '-m' not in opts_keys:
        Dumper.ignore_aliases = lambda self, data: True
    Dumper.add_representer(PresortedOrderedDict, yaml.representer.SafeRepresenter.represent_dict)
    Dumper.add_representer(validate_rapier.unicode_node, yaml.representer.SafeRepresenter.represent_unicode)
    Dumper.add_representer(validate_rapier.list_node, yaml.representer.SafeRepresenter.represent_list)
    openAPI_spec = generator.openAPI_spec_from_rapier(*args)
    openAPI_spec_yaml = yaml.dump(openAPI_spec, default_flow_style=False, Dumper=Dumper)
    openAPI_spec_yaml = str.replace(openAPI_spec_yaml, "'<<':", '<<:')
    print openAPI_spec_yaml
    
def article(name):
    return 'an' if name[0].lower() in 'aeiou' else 'a'
        
def articled(name):
    return '%s %s' % (article(name), name)
                    
def json_ref(key):
    return {'$ref': key}
        
if __name__ == "__main__":
    main(sys.argv)
