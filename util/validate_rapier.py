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
import os

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
        self.included_spec_validators = dict()
        self.referenced_spec_validators = dict()
        self.relationship_targets = dict() 
        self.included_entities = dict()

    def validate_id(self, node, key, id):
        if not isinstance(id, basestring):
            self.error('id must be a string: %s' %s, key)
        elif len(id.split()) > 1:
            self.error('id string must not contain whitespace: %s' %s, key)            

    def validate_version(self, node, key, version):
        if not isinstance(version, basestring):
            self.error('version must be a string ', key)
        
    def check_id_uniqueness(self, entities):
        self.entities = {}
        for name, entity in entities.iteritems():
            if entity is not None:
                id = self.abs_url(entity.get('id', '#%s'%name))
                if id in self.entities:
                    self.info('information about %s is provided in multiple places - is this what you meant?' % id)
                else:
                    self.entities[id] = entity
                    entity['id'] = id
                    self.entities[self.abs_url('#/entities/%s' % name)] = entity
        self.checked_id_uniqueness = True
            
    def validate_entities(self, node, key, entities):
        for key, entity in entities.iteritems():
            self.check_and_validate_keywords(self.__class__.entity_keywords, entity, key)

    def validate_conventions(self, node, key, conventions):
        self.check_and_validate_keywords(self.__class__.conventions_keywords, conventions, key)

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

    def validate_wellKnownURLs(self, nod, key, urls):
        if not isinstance(urls, (basestring, list)):
            self.error('wellKnownURLs must be a string or an array: %s' % id, key)
        else:
            if isinstance(urls, basestring):
                urls = urls.split()
            for url in urls:
                parsed_url = urlsplit(url)
                if parsed_url.scheme or parsed_url.netloc or not parsed_url.path.startswith('/'):
                    self.error('wellKnownURLs must be begin with a single slash %s' % url, key)

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
        if properties is None:
            return self.error('properties value must be a map, not null', key)
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
            self.error('readOnly must be a boolean: %s' % readOnly, key)

    def validate_useEtag(self, node, key, readOnly):
        if not (readOnly is True or readOnly is False) :
            self.error('useEtag must be a boolean: %s' % readOnly, key)

    def validate_entity_readOnly(self, node, key, readOnly):
        if not (readOnly is True or readOnly is False) :
            self.error('readOnly must be a boolean: %s' % readOnly, key)

    def validate_conventions_queryPathSelectorLocation(self, node, key, location):
        if not location in ['pathSegment', 'pathParameter']:
            self.error('%s must be either the string "pathSegment" or "pathParameter"' % location)

    def validate_conventions_patch_consumes(self, node, key, patch_consumes):
        if not isinstance(patch_consumes, basestring):
            self.error('patchConsumes must be a string: %s' % patch_consumes)

    def validate_conventions_error_response(self, node, key, error_response):
        if isinstance(error_response, basestring):
            self.validate_included_entity_url(error_response, key)
        elif hasattr(error_response, 'keys'):
            self.check_and_validate_keywords(self.__class__.schema_keywords, error_response, key)
        else:
            self.error('errorResponse must be URL of entity or schema: %s' % error_response, key)

    def similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio() > self.similarity_ratio
    
    def check_and_validate_keywords(self, keyword_validators, node, node_key):
        if hasattr(node, 'keys'):
            if id(node) not in self.validated_nodes:
                self.validated_nodes.add(id(node))
                if '$ref' in node:
                    ref_key = [key for key in node.iterkeys() if key == '$ref'][0]
                    resolved_node = keyword_validators[key](self, node, ref_key, node['$ref']) 
                    node['$ref'] = self.abs_url(node['$ref'])
                    if node is not None:
                        node['resolved_node'] = resolved_node
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
            self.error('node must be a map: %s' % node, node_key)

    def validate_property_type(self, node, key, p_type):
        if hasattr(p_type, 'keys'): #nested schema done wrong?
            self.error('type may not be a yaml map - use "type: object" and place other schema elements as siblings of type', key)
        elif not p_type in ['array', 'boolean', 'integer', 'number', 'null', 'object', 'string']:
            self.error("type must be one of 'array', 'boolean', 'integer', 'number', 'null', 'object', 'string': %s" % p_type, key)   
            
    def validate_query_parameter_property_type(self, node, key, p_type):
        if not p_type in ['array', 'boolean', 'integer', 'number', 'string']:
            self.error("type must be one of 'array', 'boolean', 'integer', 'number', 'string': %s" % p_type, key)   
            
    def validate_property_format(self, node, key, format):
        if not isinstance(format, basestring):
            self.error('format must be a string: %s' % format, key)    
            
    def validate_property_relationship(self, node, key, relationship):
        if node.get('type') != 'string':
            self.error('relationship properties must be of type string', key)
        if node.get('format') != 'uri':
            self.error('relationship properties must have "format: uri"', key)
        if hasattr(relationship, 'keys'):
            if relationship.get('entities') is None:
              self.error('relationship must have property "entities"', key)
            self.check_and_validate_keywords(self.__class__.relationship_keywords, relationship, key)
        elif isinstance(relationship, basestring):
            self.validate_relationship_entities(node, key, relationship)
        else:
            self.error('relationship must be a string or a map %s' % relationship)        
            
    def validate_property_items(self, node, key, items):
        self.check_and_validate_keywords(self.__class__.property_keywords, items, key)
        
    def validate_relationship_entities(self, node, key, entities):
        if isinstance(entities, basestring):
            entity_urls = entities.split()
        else:
            if not isinstance(entities, list):
                return self.error('entities must be a string or list %s' % entities, key)
            else:
                entity_urls = entities
        entity_map = [self.validate_referenced_entity_url(entity_url, key) for entity_url in entity_urls]
        node[key] = [item[0] for item in entity_map]
        self.relationship_targets.update(entity_map) 
            
    def validate_relationship_multiplicity(self, node, key, multiplicity):
        if not isinstance(multiplicity, basestring):
            self.error('relationship multiplicity mut be a string %s' % multiplicity, key)
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
                        
    def validate_relationship_collectionResource(self, node, key, collection_resource):
        abs_url, _ = self.validate_included_entity_url(collection_resource, key)
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
            self.validate_enum_val(node, enum_val, key)
                        
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
        pass #self.info('Security definitions not yet validated')

    def validate_rapier_security(self, node, key, security):
        pass #self.info('Security not yet validated')

    def validate_query_parameters(self, node, key, query_parameters):
        if not hasattr(query_parameters, 'keys'):
            return self.error('queryParameters must be a map: %s' % query_parameters, key)
        names = set()
        for param_name, query_parameter in query_parameters.iteritems():
            self.check_and_validate_keywords(self.__class__.query_parameter_keywords, query_parameter, key)
            if not isinstance(param_name, basestring):
                self.error('name must be a string: %s' % name, param_name)

    def validate_uri_templates(self, node, key, url_templates):
        if isinstance(url_templates, basestring):
            for template_string in url_templates.split():
                self.validate_url_template(node, key, {"template": template_string})
        elif isinstance(url_templates, list):
            for url_template in url_templates:
                template = {"template": template_string} if isinstance(url_template, basestring) else url_template
                self.validate_url_template(node, key, template)
        else:
            self.validate_url_template(node, key, url_templates)
            
    def validate_url_template(self, node, key, url_template):
        if hasattr(url_template, 'keys'):
            template_string = url_template.get('template')
            if not isinstance(template_string, basestring):
                if template_string is None:
                    self.error('URI template must have a `temnplate` property: %s' % url_template)
                else:
                    self.error('`template` property of URI template must be a string: %s' % template_string)
            else:
                if len(template_string.split()) > 1:
                    self.error('template property of URI template must not contain whitespace: %s' % template_string)
            template_variables = url_template.get('variables')
            if template_variables is not None:
                if hasattr(template_variables, 'keys'):
                    for var_name, var in template_variables.iteritems():
                        self.check_and_validate_keywords(self.__class__.template_variable_keywords, var, var_name)
                else:
                    self.error('`variable` property of URI template must be a map: %s' % template_variables)
        elif isinstance(consumes, list):
            for media_type in consumes:
                self.validate_media_type(node, media_type, media_type)
        else:
            if not isinstance(consumes, basestring):
                self.error('relationship consumes must be a list, string or relationship_consumes object: %s' % consumes, key)

    def validate_relationship_query_parameters(self, node, key, query_parameters):
        self.validate_query_parameters(node, key, query_parameters)
        multiplicity = node.get('multiplicity')
        upperbound = 0
        if multiplicity:
            if isinstance(multiplicity, basestring):
                upperbound = multiplicity.split(':')[-1]
                if upperbound == 'n':
                    upper_bound = 2
                else:
                    try:
                        upper_bound = int(upper_bound)
                    except ValueError:
                        pass
        if upper_bound > 2:
            self.error('relationships with query paramaters must be multi-valued', key)
            
    def invalid(self, node, key, value):
        self.error('%s is not allowed: value' %key, key)
    
    def validate_ignore(self, node, key, value):
        pass
    
    def validate_schema_allOf(self, node, key, value):
        if isinstance(value, list):
            for one in value:
                self.check_and_validate_keywords(self.__class__.schema_keywords, one, key)
        else:
            self.error('allOf value must be a list: %s' % value, key)
                                    
    def validate_schema_oneOf(self, node, key, value):
        if isinstance(value, list):
            for one in value:
                self.check_and_validate_keywords(self.__class__.schema_keywords, one, key)
        else:
            self.error('oneOf value must be a list: %s' % value, key)
                                    
    def validate_entity_allOf(self, node, key, value):
        if isinstance(value, list):
            for one in value:
                self.check_and_validate_keywords(self.__class__.entity_keywords, one, key)
        else:
            self.error('allOf value must be a list: %s' % value, key)
                                    
    def validate_entity_oneOf(self, node, key, value):
        if isinstance(value, list):
            for one in value:
                self.check_and_validate_keywords(self.__class__.entity_keywords, one, key)
        else:
            self.error('oneOf value must be a list: %s' % value, key)
                                    
    def validate_query_parameter_allOf(self, node, key, value):
        if isinstance(value, list):
            for one in value:
                self.check_and_validate_keywords(self.__class__.schema_keywords, one, key)
        else:
            self.error('allOf value must be a list: %s' % value, key)
                                    
    def validate_query_parameter_oneOf(self, node, key, value):
        if isinstance(value, list):
            for one in value:
                self.check_and_validate_keywords(self.__class__.schema_keywords, one, key)
        else:
            self.error('oneOf value must be a list: %s' % value, key)
                                    
    def validate_query_parameter_name(self, node, key, name):
        if not isinstance(name, basestring):
            self.error('query_parameter name must be a string: %s' % name, key) 

    def validate_query_parameter_required(self, node, key, required):
        if not (required is True or required is False):
            self.error('query_parameter required must be true or false: %s' % required, key) 

    def validate_number(self, node, key, value):
        if not isinstance(value, Number):
            self.error('%s must be a number %s' % (key, number), key)
            
    def validate_integer(self, node, key, value):
        try: 
            int(value)
        except ValueError:
            self.error('%s must be an integer %s' % (key, value), key)

    def validate_implementation_private_information(self, node, key, entities):
        for key, entity in entities.iteritems():
            self.check_and_validate_keywords(self.__class__.implementation_private_keywords, entity, key)

    def validate_permalink_template_template(self, node, key, template):
        formatter = string.Formatter()
        try:
            parsed_format = list(formatter.parse(template))
        except Exception as e:
            return self.error('error parsing query path segment string: %s' % e, key)
        leading_parts = [part for part in parsed_format if part[1] is not None]
        if len(leading_parts) != 1:
            self.error('permalinkTemplate template %s must include exactly one {name} element after ;' % query_path_segment_string)
        else:
            part = leading_parts[0]
        if part[1] == '':
            self.error('property name required between {} characters after %s in permalinkTemplate template %s' %(leading_parts[0] ,query_path_segment_string))

    def validate_permalink_template_variable_type(self, node, key, a_type):
        if not (a_type == 'string' or a_type == 'integer' or a_type == 'number'):
            self.error('permalinkTemplate type must be "string" or "integer" or "number": %s' % required, key) 
    
    def validate_media_type(self, node, key, media_type):
        if not isinstance(media_type, basestring):
            self.error('relationship consumes list entry must be media_type string: %s' % media_type, key)
        else:
            if len(media_type.split()) > 1:
                    self.error('relationship consumes media_type string may not contain whitespace: %s' % media_type, key)
        
    def validate_relationship_consumes(self, node, key, consumes):
        if hasattr(consumes, 'keys'):
            for media_type, entities in consumes.iteritems():
                self.validate_media_type(node, media_type, media_type)
                if isinstance(entities, basestring):
                    entities = entities.split()
                elif isinstance(entities, list):
                    for entity in entities:
                        if not isinstance(entity, basestring):
                            self.error('entity URL must be a string: %s' % entity, media_type)
                else:
                    self.error('entity URLs associated with media_type must be string or list: %s' % entities, media_type)
                consumes[media_type] = [self.abs_url(entity) for entity in entities]
        elif isinstance(consumes, list):
            for media_type in consumes:
                self.validate_media_type(node, media_type, media_type)
        else:
            if not isinstance(consumes, basestring):
                self.error('relationship consumes must be a list, string or relationship_consumes object: %s' % consumes, key)
                
    def validate_rapier_description(self, node, key, description):
        if not isinstance(description, basestring):
            self.error('description must be a string: %s' % description, key)
            
    def validate_entity_ref(self, node, key, json_pointer):
         return self.resolve_json_ref(json_pointer, key)

    def validate_schema_ref(self, node, key, json_pointer):    
         return self.resolve_json_ref(json_pointer, key)

    def validate_required(self, node, key, required):
        if not isinstance(required, list):
            self.warning('value of required must be a list', key)
        else:
            for property_name in required:
                if not isinstance(property_name, basestring):
                    self.warning('required value must be a string: %s' % property_name, key)

    def validate_usage(self, node, key, usage, valid_usage_values_dict):
        if isinstance(usage, basestring):
            usage_values = usage.split()
        elif isinstance(usage, list):
            usage_values = usage
        else:
            return self.error('usage must be a string or list: %s' % usage, key)
        valid_usage_values = [v for aliases in valid_usage_values_dict.itervalues() for v in aliases]
        unrecognized_values = [u_val for u_val in usage_values if u_val not in valid_usage_values]
        if len(unrecognized_values) > 0:
            return self.error('unrecognized usage values: %s' % unrecognized_values, key)
        for op, valid_values in valid_usage_values_dict.iteritems():
            if len([u_val for u_val in usage_values if u_val in valid_values]) > 1:
                self.error('%s usage value specified more than once' % op, key)

    def validate_schema_usage(self, node, key, usage):
        return self.validate_usage(node, key, usage, self.__class__.usage_schema_values)

    def validate_entity_usage(self, node, key, usage):
        return self.validate_usage(node, key, usage, self.__class__.usage_entity_values)

    def validate_additional_properties(self, node, key, additional_properties):
        if hasattr(additional_properties, 'keys'):
            self.check_and_validate_keywords(self.__class__.property_keywords, additional_properties, None)
        elif additional_properties is not False:
            self.error('additionalProperties must be false or a schema: %s' % additional_properties, key)

    def validate_query_parameter_collection_format(self, node, key, collection_format):
        if collection_format not in ['csv', 'ssv', 'tsv', 'pipes', 'multi']:
            self.error("collection_format must be one of 'csv', 'ssv', 'tsv', 'pipes', 'multi': %s" % additional_properties, key)
            
    def validate_xItems(self, node, key, value, which):
        self.validate_integer(node, key, value)
        node_type = node.get('type')
        if node_type is not None:
            if node_type != 'array':
                self.error('%s is only valid for type array: %s' % (which, node_type), key)            
        else:
            if 'allOf' in Node:
                pass #todo follow the chain
            else:
                self.error('%s is only valid for type array' % which, key)
                
    def validate_maxItems(self, node, key, value):
        self.validate_xItems(node, key, value, 'maxItems')
    
    def validate_minItems(self, node, key, value):
        self.validate_xItems(node, key, value, 'minItems')
    
    c_usage_values = {'c', 'create'}
    r_usage_values = {'r', 'read', 'retrieve', 'g', 'get'}
    u_usage_values = {'u', 'update', 'put', 'patch'}
    d_usage_values = {'d', 'delete'}
    usage_entity_values = {'retrieve': r_usage_values, 'update': u_usage_values, 'delete': d_usage_values}
    usage_schema_values = {'create': c_usage_values, 'retrieve': r_usage_values, 'update': u_usage_values}
            
    rapier_spec_keywords = {
        'title': validate_title, 
        'id': validate_id,
        'entities': validate_entities, 
        'conventions': validate_conventions, 
        'version': validate_version,
        'consumes': validate_rapier_consumes,
        'produces': validate_rapier_produces,
        'securityDefinitions': validate_rapier_security_definitions,
        'security': validate_rapier_security,
        'implementationPrivateInformation': validate_implementation_private_information,
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
        'maximum': validate_number, 
        '$ref': validate_schema_ref,
        'required': validate_required,
        'additionalProperties': validate_additional_properties,
        'usage': validate_schema_usage,
        'minItems': validate_minItems,
        'maxItems': validate_maxItems}
    property_keywords = {
        'relationship': validate_property_relationship,
        'default': validate_ignore,
        'example': validate_ignore}
    property_keywords.update(schema_keywords)
    entity_keywords = schema_keywords.copy()
    entity_keywords.update({
        'queryPaths': validate_query_paths, 
        'wellKnownURLs': validate_wellKnownURLs,
        'consumes': validate_entity_consumes,
        'produces': validate_entity_produces,
        'queryParameters': validate_query_parameters,
        'name': validate_ignore,
        'oneOf': validate_entity_oneOf, 
        'allOf': validate_entity_allOf, 
        'readOnly': validate_entity_readOnly, 
        '$ref': validate_entity_ref,
        'usage': validate_entity_usage,
        'permalinkTemplate': validate_uri_templates,
        'uriTemplates': validate_uri_templates})
    conventions_keywords = {
        'queryPathSelectorLocation': validate_conventions_queryPathSelectorLocation,
        'patchConsumes': validate_conventions_patch_consumes,
        'useEtag': validate_useEtag,
        'errorResponse': validate_conventions_error_response}
    relationship_keywords = {
        'entities': validate_relationship_entities, 
        'multiplicity': validate_relationship_multiplicity, 
        'collectionResource': validate_relationship_collectionResource, 
        'name': validate_relationship_name,
        'readOnly': validate_relationship_readOnly,
        'usage': validate_schema_usage,
        'queryParameters': validate_relationship_query_parameters,
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
        'maximum': validate_number,
        'collectionFormat': validate_query_parameter_collection_format}
    template_variable_keywords =  {
        'type': validate_query_parameter_property_type, 
        'format': validate_property_format, 
        'items': validate_property_items, 
        'properties': invalid, 
        'oneOf': validate_query_parameter_oneOf, 
        'allOf': validate_query_parameter_allOf, 
        'enum': validate_enum,
        'title': validate_title,
        'description': validate_description,
        'required': validate_query_parameter_required,
        'minimum': validate_number,
        'maximum': validate_number,
        'collectionFormat': validate_query_parameter_collection_format}
    implementation_private_keywords =  {
        'permalinkTemplate': validate_uri_templates}

    def abs_url(self, url):
        split_url = url.split('#')
        if split_url[0] == '':
            split_url[0] = self.abs_filename
        else:
            split_url[0] = os.path.abspath(os.path.join(self.abs_directoryname, split_url[0]))
        return '#'.join(split_url)
            
    def relative_url(self, uri_ref):
        split_ref = uri_ref.split('#')
        url = split_ref[0]
        if url == self.abs_filename:
            split_ref[0] = ''
        elif url != '':
            split_ref[0] = os.path.relpath(url, self.abs_directoryname)
        return '#'.join(split_ref)
            
    def resolve_validator(self, entity_url, validators):
        abs_url = self.abs_url(entity_url)
        abs_namespace_url = abs_url.split('#')[0]
        if abs_namespace_url == self.abs_filename:
            return self, None
        else:
            if abs_namespace_url not in validators:
                validator = OASValidator()
                rel_spec_url = entity_url.split('#')[0]
                spec, errors = validator.validate(rel_spec_url, self.abs_directoryname)
                if spec is None:
                    return None, errors
                if errors > 0:
                    self.error('errors reading file: %s' % abs_namespace_url)
                validators[abs_namespace_url] = validator
            return validators[abs_namespace_url], None

    def validate_entity_url(self, entity_url, key, validators):
        if isinstance(entity_url, basestring):
            abs_entity_url = self.abs_url(entity_url)
            validator, errors = self.resolve_validator(entity_url, validators)
            if errors is not None:
                if isinstance(errors, IOError):
                    self.warning('unable to read file: %s %s' % (entity_url, errors), key)
                return abs_entity_url, None
            entity = validator.entities.get(abs_entity_url)
            if entity is not None:
                return abs_entity_url, entity  
            else:
                self.error('entity not found %s' % entity_url, key)
        else:
            self.error('entity URL must be a string %s' % entity_url, key)
        return None, None

    def resolve_json_ref(self, json_ref, key, spec=None):
        if isinstance(json_ref, basestring):
            json_ref_split = json_ref.split('#')
            if len(json_ref_split) < 2:
                self.error('entity missing fragment %s' % json_ref, key)
            else:
                validator, errors = self.resolve_validator(json_ref_split[0], self.included_spec_validators)
                if validator is None:
                    self.fatal_error('unable to open file: %s' % json_ref_split[0], key)
                json_ref_fragment = json_ref_split[1]
                if json_ref_fragment.startswith('/'):
                    parts = json_ref_fragment[1:].split('/')
                    spec = validator.rapier_spec
                    for part in parts:
                        spec = spec.get(part)
                        if spec is None:
                            return self.error('json ref segment value not found: %s' % part, key)
                    self.included_entities[self.abs_url(json_ref)] = spec
                    return spec
                else:
                    self.error('json ref fragment must begin with "#/": %s' % json_ref, key)
        else:
            self.error('json ref value must be a string: %s' % json_ref, key)

    def validate_referenced_entity_url(self, entity_url, key):
        return self.validate_entity_url(entity_url, key, self.referenced_spec_validators)

    def validate_included_entity_url(self, entity_url, key):
        abs_url, entity = self.validate_entity_url(entity_url, key, self.included_spec_validators)
        if abs_url is not None:
            self.included_entities[abs_url] = entity
        return abs_url, entity

    def validate(self, filename, abs_base_directory):
        self.filename = filename
        if abs_base_directory != None:
            self.abs_directoryname = abs_base_directory
            self.abs_filename = self.abs_url(filename)
        else:
            self.abs_filename = os.path.abspath(filename)
            self.abs_directoryname = os.path.dirname(self.abs_filename)
        try:
            with open(self.abs_filename) as f:
                self.rapier_spec = self.marked_load(f.read())
        except IOError as e:
            self.error('unable to open file: %s' % filename)
            return None, e
        if self.rapier_spec is None:
            return None
        if not hasattr(self.rapier_spec, 'keys'):
            self.fatal_error('rapier specification must be a YAML mapping: %s' % self.filename)
        entities = self.rapier_spec.setdefault('entities', {})
        self.check_id_uniqueness(entities)
        if 'implementationPrivateInformation' in self.rapier_spec:
            for entity_name, entity_desc in self.rapier_spec['implementationPrivateInformation'].iteritems():
                if 'properties' in entity_desc:
                    for property in entity_desc['properties'].itervalues():
                        property['implementation_private'] = True
                entity_id = self.abs_url(entity_desc.get('id', '#%s'%entity_name))
                if entity_id in self.entities:
                    if 'properties' in entity_desc:
                        properties = entity_desc['properties']
                        if 'properties' in entities[entity_name]:
                            entities[entity_name]['properties'].update(properties)
                        else:
                            entities[entity_name]['properties'] = properties
                    if 'queryPaths' in entity_desc:
                        entities[entity_name]['queryPaths'] = as_list(entities[entity_name].get('queryPaths', []))
                        entities[entity_name]['queryPaths'].extend(entity_desc['queryPaths'])
                    self.entities[entity_id].update({k:v for k,v in entity_desc.iteritems() if k not in ['properties', 'queryPaths']})
                else:
                    self.error('defining new entities in implementationPrivateInformation not yet supported: %s' % entity_id)
                    
        for entity_name, entity in entities.iteritems():
            if entity is not None:
                if 'name' in entity:
                    self.error('"name" property not allowed in entity: %s' % entity_name)
                else:
                    entity['name'] = entity_name
                if 'id' not in entity:
                    entity['id'] = self.abs_url('#%s' % entity_name)
        self.check_and_validate_keywords(self.__class__.rapier_spec_keywords, self.rapier_spec, None)
        return self.rapier_spec, self.errors

    def build_included_entity_map(self):
        result = {}
        result.update(self.entities)
        result.update(self.included_entities)
        for validator in self.included_spec_validators.itervalues():
            result.update(validator.included_entities)
        return result

    def included_entity_iteritems(self):
        for item in self.included_entities.iteritems():
            yield item
        for validator in self.included_spec_validators.itervalues():
            for item in validator.included_entity_iteritems():
                yield item

    def resolve_included_entity(self, uri):
        abs_uri = self.abs_url(uri)
        result = self.entities.get(abs_uri) or self.included_entities.get(abs_uri)
        if result is None:
            for validator in self.included_spec_validators.itervalues():
                result = validator.resolve_included_entity(abs_uri)
                if result is not None:
                    break
        return result
    
    def resolve_referenced_entity(self, uri):
        abs_uri = self.abs_url(uri)
        result = self.entities.get(abs_uri)
        if result is None:
            for validator in self.referenced_spec_validators.itervalues():
                result = validator.entities.get(abs_uri)
                if result is not None:
                    break
        return result

    def resolve_referenced_entity_ref(self, ref):
        return self.resolve_referenced_entity(ref['$ref'])

    def resolve_included_entity_ref(self, ref):
        return self.resolve_included_entity(ref['$ref'])

    def resolve_referenced_entity_name(self, uri):
        return self.resolve_referenced_entity(uri)['name']

    def resolve_included_entity_name(self, uri):
        return self.resolve_included_entity(uri)['name']

    def marked_load(self, stream):
        def construct_mapping(loader, node):
            keys = [node_tuple[0].value for node_tuple in node.value]
            for item, count in Counter(keys).items():
                if count > 1:
                    key_nodes = [node_tuple[0] for node_tuple in node.value if node_tuple[0].value == item]
                    self.warning('%s occurs %s times, at %s' % (item, count, ' and '.join(['line %s, column %s' % (key_node.start_mark.line + 1, key_node.start_mark.column + 1) for key_node in key_nodes])))            
            loader.flatten_mapping(node)
            return PresortedOrderedDict(loader.construct_pairs(node))
        MarkedLoader.add_constructor(
            Resolver.DEFAULT_MAPPING_TAG,
            construct_mapping)
        return MarkedLoader(stream).get_single_data()
        
    def fatal_error(self, message, key_node=None):
        message = ' '. join(['FATAL ERROR -', message, 'in', self.filename])
        if key_node and hasattr(key_node, 'start_mark'):
            message += ' after line %s column %s to line %s column %s' % (key_node.start_mark.line + 1, key_node.start_mark.column + 1, key_node.end_mark.line + 1, key_node.end_mark.column + 1)
        sys.exit(message)

    def error(self, message, key_node=None):
        self.errors += 1
        if key_node and hasattr(key_node, 'start_mark'):
            message += ' after line %s column %s to line %s column %s' % (key_node.start_mark.line + 1, key_node.start_mark.column + 1, key_node.end_mark.line + 1, key_node.end_mark.column + 1)
        print >> sys.stderr, ' '. join(['ERROR -', message, 'in', self.filename])

    def warning(self, message, key_node=None):
        if key_node and hasattr(key_node, 'start_mark'):
            message += ' after line %s column %s to line %s column %s' % (key_node.start_mark.line + 1, key_node.start_mark.column + 1, key_node.end_mark.line + 1, key_node.end_mark.column + 1)
        print >> sys.stderr, ' '. join(['WARNING -', message, 'in', self.filename])

    def info(self, message, key_node=None):
        if key_node and hasattr(key_node, 'start_mark'):
            message += ' after line %s column %s to line %s column %s' % (key_node.start_mark.line + 1, key_node.start_mark.column + 1, key_node.end_mark.line + 1, key_node.end_mark.column + 1)
        print >> sys.stderr, ' '. join(['INFO -', message, 'in', self.filename])

def main(args):
    validator = OASValidator()
    if not len(args) == 1:
        usage = 'usage: validate_rapier.py filename'
        sys.exit(usage)
    validator.validate(*args)
    return validator.rapier_spec, validator.errors

if __name__ == "__main__":
    main(sys.argv[1:])
