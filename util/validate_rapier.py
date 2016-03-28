#!/usr/bin/env python 

from difflib import SequenceMatcher
from collections import OrderedDict
from collections import Counter
import sys, string
from yaml.composer import Composer
from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.composer import Composer
from yaml.resolver import Resolver
from yaml.parser import Parser
from yaml.constructor import Constructor, BaseConstructor, SafeConstructor
from urlparse import urlsplit
from numbers import Number
from os import path

class PresortedList(list):
    def sort(self, *args, **kwargs):
        pass

class PresortedOrderedDict(OrderedDict):
    def items(self, *args, **kwargs):
        return PresortedList(OrderedDict.items(self, *args, **kwargs))

def create_node_class(cls):
    class node_class(cls):
        def __init__(self, x, start_mark, end_mark):
            cls.__init__(self, x)
            self.start_mark = start_mark
            self.end_mark = end_mark

        def __new__(self, x, start_mark, end_mark):
            return cls.__new__(self, x)
    node_class.__name__ = '%s_node' % cls.__name__
    return node_class

dict_node = create_node_class(dict)
list_node = create_node_class(list)
unicode_node = create_node_class(unicode)

class NodeConstructor(SafeConstructor):
    # To support lazy loading, the original constructors first yield
    # an empty object, then fill them in when iterated. Due to
    # laziness we omit this behaviour (and will only do "deep
    # construction") by first exhausting iterators, then yielding
    # copies.
    def construct_yaml_map(self, node):
        obj, = SafeConstructor.construct_yaml_map(self, node)
        return dict_node(obj, node.start_mark, node.end_mark)

    def construct_yaml_seq(self, node):
        obj, = SafeConstructor.construct_yaml_seq(self, node)
        return list_node(obj, node.start_mark, node.end_mark)

    def construct_yaml_str(self, node):
        obj = SafeConstructor.construct_scalar(self, node)
        assert isinstance(obj, unicode)
        return unicode_node(obj, node.start_mark, node.end_mark)

NodeConstructor.add_constructor(
        u'tag:yaml.org,2002:map',
        NodeConstructor.construct_yaml_map)

NodeConstructor.add_constructor(
        u'tag:yaml.org,2002:seq',
        NodeConstructor.construct_yaml_seq)

NodeConstructor.add_constructor(
        u'tag:yaml.org,2002:str',
        NodeConstructor.construct_yaml_str)


class MarkedLoader(Reader, Scanner, Parser, Composer, NodeConstructor, Resolver):
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)

class OASValidator(object):

    def __init__(self):
        self.errors = 0
        self.similarity_ratio = 0.7
        self.checked_id_uniqueness = False
        self.validated_nodes = set()
        self.external_spec_validators = dict()

    def validate_title(self, key, title):
        if not isinstance(title, basestring):
            self.error('title must be a string', key)

    def validate_version(self, key, version):
        if not isinstance(version, basestring):
            self.error('version must be a string ', key)
        
    def check_id_uniqueness(self):
        self.entities = {}
        for name, entity in self.rapier_spec.get('entities',{}).iteritems():
            id = entity.get('id', '#%s'%name)
            if id in self.entities:
                self.info('information about %s is provided in multiple places - is this what you meant?' % id)
            else:
                self.entities[id] = entity
        self.checked_id_uniqueness = True
            
    def validate_entities(self, node, key, entities):
        if not self.checked_id_uniqueness:
            self.check_id_uniqueness()
        for key, entity in entities.iteritems():
            self.check_and_validate_keywords(self.__class__.entity_keywords, entity, key)

    def validate_conventions(self, node, key, conventions):
        self.check_and_validate_keywords(self.__class__.conventions_keywords, conventions, key)

    def validate_id(self, node, key, id):
        if not isinstance(id, basestring):
            self.error('id must be a string: %s' % id, key)

    def validate_query_paths(self, node, key, query_paths):
        if isinstance(query_paths, basestring):
            effective_query_paths = query_paths.split()
        elif isinstance(query_paths, list):
            effective_query_paths = query_paths
        else:
            return self.error('query paths must be either a space-delimited string or a sequence: %s' % query_paths, key)
        for query_path in effective_query_paths:
            self.validate_query_path(node, key, query_path)
            
    def validate_query_path(self, node, key, query_path):
        if isinstance(query_path, basestring):
            path_segments = query_path.split()
            for path_segment in path_segments:
                self.validate_query_path_segment_string(node, key, path_segment)
        elif hasattr(query_path, 'keys'):
            return self.error('structured query paths not supported: %s' % query_path, key)                   
        else:
            return self.error('query-path must be either a space-delimited string or a map: %s' % query_paths, key)            

    def validate_query_path_segment_string(self, node, key, query_path_segment_string):
        parts = query_path_segment_string.split(';')
        if len(parts) == 1: # no ';'
            pass
        elif len(parts) == 2: # found ';'
            params_part = parts[1]
            formatter = string.Formatter()
            try:
                parsed_format = list(formatter.parse(params_part))
            except Exception as e:
                return self.error('error parsing query path segment string: %s' % e, key)
            leading_parts = [part for part in parsed_format if part[1] is not None]
            if len(leading_parts) == 0:
                self.error('query segment %s must include at least one {name} element after ;' % query_path_segment_string)
            if len ([part for part in leading_parts if part[1] == '']) > 0:
                self.error('property name required between {} characters after %s in query segment %s' %([part[0] for part in leading_parts if part[1]] ,query_path_segment_string))            

    def validate_well_known_URLs(self, nod, key, urls):
        if not isinstance(urls, (basestring, list)):
            self.error('well_known_URLs must be a string or an array: %s' % id, key)
        else:
            if isinstance(urls, basestring):
                urls = urls.split()
            for url in urls:
                parsed_url = urlsplit(url)
                if parsed_url.scheme or parsed_url.netloc or not parsed_url.path.startswith('/'):
                    self.error('validate_well_known_URLs must be begin with a single slash %s' % url, key)

    def validate_entity_consumes(self, node, key, consumes):
        if isinstance(consumes, basestring):
            pass
        elif isinstance(consumes, list):
            for media_type in consumes:
                if not isinstance(media_type, basestring):
                    self.error('consumes value must be a media_type string: %s' % media_type, key)
    
    def validate_entity_produces(self, node, key, produces):
        if isinstance(produces, basestring):
            pass
        elif isinstance(produces, list):
            for media_type in produces:
                if not isinstance(media_type, basestring):
                    self.error('produces value must be a media_type string: %s' % media_type, key)
    
    def validate_properties(self, node, key, properties):
        for property_name, property in properties.iteritems():
            if hasattr(property, 'keys'):
                p_type = property.get('type')
                if p_type == 'array':
                    if not 'items' in property:
                        self.error('items must be present if the type is array: %s' % property, property_name)
                else:
                    if 'items' in property:
                        self.error('items must be only be present if the type is array: %s' % property, property_name)
            else:
                self.error('property must be a map: %s' % property, property_name)
            self.check_and_validate_keywords(self.__class__.property_keywords, property, property_name)

    def validate_readOnly(self, node, key, readOnly):
        if not (readOnly is True or readOnly is False) :
            self.error('id must be a boolean: %s' % readOnly, key)

    def validate_conventions_selector_location(self, node, key, location):
        if not location in ['path-segment', 'path-parameter']:
            self.error('%s must be either the string "path-segment" or "path-parameter"' % location)

    def validate_conventions_patch_consumes(self, node, key, patch_consumes):
        if not isinstance(patch_consumes, basestring):
            self.error('patch_consumes must be a string: %s' % patch_consumes)

    def validate_conventions_error_response(self, node, key, error_response):
        self.check_and_validate_keywords(self.__class__.schema_keywords, error_response, key)

    def similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio() > self.similarity_ratio
    
    def check_and_validate_keywords(self, keyword_validators, node, node_key):
        if hasattr(node, 'keys'):
            if id(node) not in self.validated_nodes:
                self.validated_nodes.add(id(node))
                if '$ref' in node:
                    ref_key = [key for key in node.iterkeys() if key == '$ref'][0]
                    node = self.resolve_json_ref(node['$ref'], ref_key)
                else:
                    for key, value in node.iteritems():
                        if key not in keyword_validators:
                            similar_keywords = [keyword for keyword in keyword_validators.iterkeys() if self.similar(key, keyword)]
                            message = 'unrecognized keyword %s' % key
                            if similar_keywords:
                                message += ' - did you mean %s?' % ' or '.join(similar_keywords)
                            self.info(message, key)
                        else:
                            keyword_validators[key](self, node, key, value)        
        else:
            self.error('spec must be a map: %s' % spec, spec_key)

    def validate_property_type(self, node, key, p_type):
        if not p_type in ['array', 'boolean', 'integer', 'number', 'null', 'object', 'string']:
            self.error("type must be one of 'array', 'boolean', 'integer', 'number', 'null', 'object', 'string': " % p_type, key)   
            
    def validate_query_parameter_property_type(self, node, key, p_type):
        if not p_type in ['array', 'boolean', 'integer', 'number', 'string']:
            self.error("type must be one of 'array', 'boolean', 'integer', 'number', 'string': " % p_type, key)   
            
    def validate_property_format(self, node, key, format):
        if not isinstance(format, basestring):
            self.error('format must be a string: %s' % format, key)    
            
    def validate_property_relationship(self, node, key, relationship):
        if hasattr(relationship, 'keys'):
            self.check_and_validate_keywords(self.__class__.relationship_keywords, relationship, key)
        elif isinstance(relationship, basestring):
            self.validate_relationship_entities(key, relationship)
        else:
            self.error('relationship must be a string or a map %s' % relationship)        
            
    def validate_property_items(self, node, key, items):
        self.check_and_validate_keywords(self.__class__.property_keywords, items, key)
        
    def validate_relationship_entities(self, node, key, entities):
        if isinstance(entities, basestring):
            entity_urls = entities.split()
        else:
            if not isinstance(entities, list):
                return self.error('entities must be a string or list %s' % s, key)
            else:
                entity_urls = entities
        for entity_url in entity_urls:
            self.validate_entity_url(entity_url, key)  
        node[key] = [self.abs_url(entity_url) for entity_url in entity_urls]
            
    def validate_relationship_multiplicity(self, node, key, multiplicity):
        if not isinstance(multiplicity, basestring):
            self.error('relationship multiplicity mut be a string %s' %s, key)
        else:
            parts = multiplicity.split(':')
            if len(parts) == 1:
                lower_bound = '0'
                upper_bound = parts[0]
            elif len(parts) == 2:
                lower_bound = parts[0]
                upper_bound = parts[1]
            else:
                return self.error('only one : is allowed in multiplicity %s' %multiplicity, key)
            if not lower_bound.isdigit():
                self.error('multiplicity lower bound must be a digit: %s,' % lower_bound, key)
            if not upper_bound == 'n':
                if not upper_bound.isdigit():
                    self.error('multiplicity upper bound must be a digit or "n" %s' % lower_bound, key)
                else:
                    if int(upper_bound) < int(lower_bound):
                        self.error('multiplicity upper bound must be greater than or equal to lower bound %s %s' % (upper_bound, lower_bound), key)
                        
    def validate_relationship_collection_resource(self, node, key, collection_resource):
        abs_url = self.validate_entity_url(collection_resource, key)
        if abs_url:
            node[key] = abs_url

    def validate_relationship_readOnly(self, node, key, readOnly):
        if not (readOnly is True or readOnly is False):
            self.error('readOnly must be a boolean: %s' % readOnly, key) 

    def validate_enum_val(self, node, key, enum_val):
        if not (isinstance(enum_val, basestring) or isinstance(enum_val, Number) or enum_val is True or enum_val is False or enum_val is None):
            self.error('enum value must be a string, number, boolean or null: %s' % enum_val, key)
            
    def validate_enum(self, node, key, enum):
        if not isinstance(enum, list):
            self.error('enum must be a list: %s' % enum, key) 
        for enum_val in enum:
            self.validate_enum_val(enum_val, key)
                        
    def validate_relationship_name(self, node, key, name):
        if not isinstance(name, basestring):
            self.error('relationship name must be a string: %s' % name, key) 

    def validate_title(self, node, key, title):
        if not isinstance(title, basestring):
            self.error('title name must be a string: %s' % title, key) 

    def validate_description(self, node, key, description):
        if not isinstance(description, basestring):
            self.error('description name must be a string: %s' % description, key) 

    def validate_rapier_consumes(self, node, key, consumes):
        if not isinstance(consumes, basestring):
            self.error('consumes name must be a string: %s' % consumes, key) 

    def validate_rapier_produces(self, node, key, produces):
        if not isinstance(produces, basestring):
            self.error('produces name must be a string: %s' % produces, key) 

    def validate_rapier_security_definitions(self, node, key, security_definitions):
        self.info('Security definitions not yet validated')

    def validate_rapier_security(self, node, key, security):
        self.info('Security not yet validated')

    def validate_query_parameters(self, node, key, query_parameters):
        if not isinstance(query_parameters, list):
            return self.error('query_parameters must be a list: %s' % query_parameters, key)
        names = set()
        for query_parameter in query_parameters:
            self.check_and_validate_keywords(self.__class__.query_parameter_keywords, query_parameter, key)
            if hasattr(query_parameter, 'keys'):
                name = query_parameter.get('name')
                if name:
                    if name in names:
                        self.error('duplicate name: %s' %name, name)
                    else:
                        names.add(name)
                else:
                    self,error('name must not be null', name)
            
    def invalid(self, node, key, value):
        self.error('%s is not allowed: value' %key, key)
    
    def validate_starOf(self, node, key, starOf, keyword_validators):
        if isinstance(starOf, list):
            for one in starOf:
                self.check_and_validate_keywords(keyword_validators, one, key)
        else:
            self.error('oneOf value must be a list: %s' % value, key)

    def validate_schema_allOf(self, node, key, value):
        self.validate_starOf(key, value, self.__class__.schema_keywords)
                                    
    def validate_schema_oneOf(self, node, key, value):
        self.validate_starOf(key, value, self.__class__.schema_keywords)
                                    
    def validate_query_parameter_allOf(self, node, key, value):
        self.validate_starOf(key, value, self.__class__.schema_keywords)
                                    
    def validate_query_parameter_oneOf(self, node, key, value):
        self.validate_starOf(key, value, self.__class__.schema_keywords)
                                    
    def validate_query_parameter_name(self, node, key, name):
        if not isinstance(name, basestring):
            self.error('query_parameter name must be a string: %s' % name, key) 

    def validate_query_parameter_required(self, node, key, required):
        if not (required is True or required is False):
            self.error('query_parameter required must be true or false: %s' % required, key) 

    def validate_number(self, node, key, value):
        if not isinstance(value, Number):
            self.error('%s must be a number %s' % (key, number), key)
            
    def validate_implementation_private_information(self, node, key, entities):
        for key, entity in entities.iteritems():
            self.check_and_validate_keywords(self.__class__.implementation_private_keywords, entity, key)

    def validate_permalink_template(self, node, key, entity):
        self.check_and_validate_keywords(self.__class__.permalink_template_keywords, entity, key)
        
    def validate_permalink_template_template(self, node, key, template):
        formatter = string.Formatter()
        try:
            parsed_format = list(formatter.parse(template))
        except Exception as e:
            return self.error('error parsing query path segment string: %s' % e, key)
        leading_parts = [part for part in parsed_format if part[1] is not None]
        if len(leading_parts) != 1:
            self.error('permalink_template template %s must include exactly one {name} element after ;' % query_path_segment_string)
        else:
            part = leading_parts[0]
        if part[1] == '':
            self.error('property name required between {} characters after %s in permalink_template template %s' %(leading_parts[0] ,query_path_segment_string))

    def validate_permalink_template_type(self, node, key, a_type):
        if not (a_type == 'string' or a_type == 'integer' or a_type == 'number'):
            self.error('permalink_template type must be "string" or "interger" or "number": %s' % required, key) 
    
    def validate_media_type(self, node, key, media_type):
        if not isinstance(media_type, basestring):
            self.error('relationship consumes list entry must be media_type string: %s' % media_type, key)
        else:
            if len(media_type.split()) > 1:
                    self.error('relationship consumes media_type string may not contain whitespace: %s' % media_type, key)
        
    def validate_relationship_consumes(self, node, key, consumes):
        if hasattr(consumes, 'keys'):
            for media_type, entities in consumes.iteritems():
                self.validate_media_type(media_type, media_type)
                if isinstance(entities, list):
                    for entity in entities:
                        if not isinstance(entity, basestring):
                            self.error('entity URL must be a string: %s' % entity, media_type)
                elif not isinstance(entities, basestring):
                    self.error('entity URLs associated with media_type must be string or list: %s' % entities, media_type)
        elif isinstance(consumes, list):
            for media_type in consumes:
                self.validate_media_type(media_type, media_type)
        else:
            if not isinstance(consumes, basestring):
                self.error('relationship consumes must be a list, string or relationship_consumes object: %s' % consumes, key)
                
    def validate_rapier_description(self, node, key, description):
        if not isinstance(description, basestring):
            self.error('description must be a string: %s' % description, key)
    
    rapier_spec_keywords = {
        'title': validate_title, 
        'entities': validate_entities, 
        'conventions': validate_conventions, 
        'version': validate_version,
        'consumes': validate_rapier_consumes,
        'produces': validate_rapier_produces,
        'securityDefinitions': validate_rapier_security_definitions,
        'security': validate_rapier_security,
        'implementation_private_information': validate_implementation_private_information,
        'description': validate_rapier_description}
    schema_keywords =  {
        'id': validate_id, 
        'type': validate_property_type, 
        'format': validate_property_format, 
        'items': validate_property_items, 
        'properties': validate_properties, 
        'readOnly': validate_readOnly, 
        'oneOf': validate_schema_oneOf, 
        'allOf': validate_schema_allOf, 
        'enum': validate_enum,
        'title': validate_title,
        'description': validate_description,
        'minimum': validate_number,
        'maximum': validate_number}
    property_keywords = {
        'relationship': validate_property_relationship}
    property_keywords.update(schema_keywords)
    entity_keywords = {
        'query_paths': validate_query_paths, 
        'well_known_URLs': validate_well_known_URLs,
        'consumes': validate_entity_consumes,
        'produces': validate_entity_produces,
        'query_parameters': validate_query_parameters}
    entity_keywords.update(schema_keywords)
    conventions_keywords = {
        'selector_location': validate_conventions_selector_location,
        'patch_consumes': validate_conventions_patch_consumes,
        'error_response': validate_conventions_error_response}
    relationship_keywords = {
        'entities': validate_relationship_entities, 
        'multiplicity': validate_relationship_multiplicity, 
        'collection_resource': validate_relationship_collection_resource, 
        'name': validate_relationship_name,
        'readOnly': validate_relationship_readOnly,
        'consumes': validate_relationship_consumes}
    query_parameter_keywords =  {
        'type': validate_query_parameter_property_type, 
        'format': validate_property_format, 
        'items': validate_property_items, 
        'properties': invalid, 
        'oneOf': validate_query_parameter_oneOf, 
        'allOf': validate_query_parameter_allOf, 
        'enum': validate_enum,
        'title': validate_title,
        'description': validate_description,
        'name': validate_query_parameter_name,
        'required': validate_query_parameter_required,
        'minimum': validate_number,
        'maximum': validate_number}
    implementation_private_keywords =  {
        'permalink_template': validate_permalink_template}
    permalink_template_keywords =  {
        'template': validate_permalink_template_template,
        'type': validate_permalink_template_type}

    def abs_url(self, url):
        split_url = url.split('#')
        split_url[0] = path.abspath(path.join(self.abs_filename, split_url[0]))
        return '#'.join(split_url)
            
    def resolve_validator(self, namespace_url):
        if self.abs_url(namespace_url) == self.abs_filename:
            return self
        else:
            abs_namespace_url = path.abspath(path.join(self.abs_filename, namespace_url))
            abs_namespace_url = self.abs_url(namespace_url)
            if abs_namespace_url not in self.external_spec_validators:
                validator = OASValidator()
                spec, errors = validator.validate(abs_namespace_url)
                if errors > 0:
                    self.fatal_error('errors reading file: %s' % abs_namespace_url)
                self.external_spec_validators[abs_namespace_url] = validator
            return self.external_spec_validators[abs_namespace_url]

    def resolve_json_ref(self, json_ref, key, spec=None):
        if isinstance(json_ref, basestring):
            json_ref_split = json_ref.split('#')
            if len(json_ref_split) < 2:
                self.error('entity missing fragment %s' % json_ref, key)
            else:
                validator = self.resolve_validator(json_ref_split[0])
                json_ref_fragment = json_ref_split[1]
                if json_ref_fragment.startswith('/'):
                    parts = json_ref[2:].split('/')
                    spec = validator.rapier_spec
                    for part in parts:
                        spec = spec.get(part)
                        if spec is None:
                            return self.error('json ref segment value not found: %s' % part, key)
                    return spec
                else:
                    self.error('json ref value must begin with "#/" or "..": %s' % json_ref, key)
        else:
            self.error('json ref value must be a string: %s' % json_ref, key)

    def validate_entity_url(self, entity_url, key):
        if not isinstance(entity_url, basestring):
            self.error('entity URL must be a string %s' % entity_url, key)
        else:
            split_entity_uri_reference = entity_url.split('#')
            if len(split_entity_uri_reference) < 2:
                self.error('entity URL missing fragment %s' % entity_url, key)
            else:
                validator = self.resolve_validator(split_entity_uri_reference[0]) if split_entity_uri_reference[0] else self
                entity_url_fragment = split_entity_uri_reference[1]
                if validator.rapier_spec.get('entities', {}).get(entity_url_fragment) is None:
                    self.error('entity not found %s' % entity_url, key)
                else:
                    return validator.abs_url('#%s' % entity_url_fragment)

    def validate(self, filename):
        self.filename = filename
        self.abs_filename = path.abspath(filename)
        try:
            with open(filename) as f:
                self.rapier_spec = self.marked_load(f.read())
        except IOError as e:
            self.fatal_error('error reading file: %s %s' % (filename, e.strerror))
        if not hasattr(self.rapier_spec, 'keys'):
            self.fatal_error('rapier specification must be a YAML mapping: %s' % self.filename)
        self.check_and_validate_keywords(self.__class__.rapier_spec_keywords, self.rapier_spec, None)
        return self.rapier_spec, self.errors

    def entity_iteritems(self):
        for entity_item in self.rapier_spec.get('entities', {}).iteritems():
            yield entity_item
        for validator in self.external_spec_validators.itervalues():
            for entity_item in validator.entity_iteritems():
                yield entity_item

    def uri_map(self):
        entities = self.rapier_spec.get('entities', {})
        result = {'%s#/entities/%s' % (self.abs_filename, name): entity for name, entity in entities.iteritems()}
        for validator in self.external_spec_validators.itervalues():
            result.update(validator.uri_map())
        return result

    def marked_load(self, stream):
        def construct_mapping(loader, node):
            keys = [node_tuple[0].value for node_tuple in node.value]
            for item, count in Counter(keys).items():
                if count > 1:
                    key_nodes = [node_tuple[0] for node_tuple in node.value if node_tuple[0].value == item]
                    self.errors += 1
                    self.warning('%s occurs %s times, at %s' % (item, count, ' and '.join(['line %s, column %s' % (key_node.start_mark.line + 1, key_node.start_mark.column + 1) for key_node in key_nodes])))            
            loader.flatten_mapping(node)
            return PresortedOrderedDict(loader.construct_pairs(node))
        MarkedLoader.add_constructor(
            Resolver.DEFAULT_MAPPING_TAG,
            construct_mapping)
        return MarkedLoader(stream).get_single_data()
        
    def fatal_error(self, message):
        sys.exit(' '. join(['FATAL ERROR -', message, 'in', self.filename]))

    def error(self, message, key_node=None):
        self.errors += 1
        if key_node:
            message += ' after line %s column %s to line %s column %s' % (key_node.start_mark.line + 1, key_node.start_mark.column + 1, key_node.end_mark.line + 1, key_node.end_mark.column + 1)
        print >> sys.stderr, ' '. join(['ERROR -', message, 'in', self.filename])

    def warning(self, message, key_node=None):
        if key_node:
            message += ' after line %s column %s to line %s column %s' % (key_node.start_mark.line + 1, key_node.start_mark.column + 1, key_node.end_mark.line + 1, key_node.end_mark.column + 1)
        print >> sys.stderr, ' '. join(['WARNING -', message, 'in', self.filename])

    def info(self, message, key_node=None):
        if key_node:
            message += ' after line %s column %s to line %s column %s' % (key_node.start_mark.line + 1, key_node.start_mark.column + 1, key_node.end_mark.line + 1, key_node.end_mark.column + 1)
        print >> sys.stderr, ' '. join(['INFO -', message, 'in', self.filename])

def main(args):
    validator = OASValidator()
    validator.validate(*args)
    return validator.rapier_spec, validator.errors

if __name__ == "__main__":
    main(sys.argv[1:])