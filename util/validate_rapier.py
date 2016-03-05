#!/usr/bin/env python 

from difflib import SequenceMatcher
from collections import OrderedDict
from collections import Counter
import sys
from yaml.composer import Composer
from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.composer import Composer
from yaml.resolver import Resolver
from yaml.parser import Parser
from yaml.constructor import Constructor, BaseConstructor, SafeConstructor
from urlparse import urlsplit

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

    def validate_title(self, key, title):
        if not isinstance(title, basestring):
            self.error('title must be a string', key)

    def validate_version(self, key, version):
        if not isinstance(version, basestring):
            self.error('version must be a string ', key)
        
    def check_id_uniqueness(self):
        self.entities = {}
        for name, entity in {k:v for d in (self.rapier_spec.get('entities',{}), self.rapier_spec.get('non_entities',{})) for k,v in d.iteritems()}.iteritems():
            id = entity.get('id', '#%s'%name)
            if id in self.entities:
                self.info('information about %s is provided in multiple places - is this what you meant?' % id)
            else:
                self.entities[id] = entity
        self.checked_id_uniqueness = True
            
    def validate_entities(self, key, entities):
        if not self.checked_id_uniqueness:
            self.check_id_uniqueness()
        for entity in entities.itervalues():
            self.check_and_validate_keywords(self.__class__.entity_keywords, entity)

    def validate_conventions(self, key, conventions):
        if not hasattr(conventions, 'iteritems'):
            self.error('conventions must be a JSON object')
        self.check_and_validate_keywords(self.__class__.conventions_keywords, conventions)

    def validate_id(self, key, id):
        if not isinstance(id, basestring):
            self.error('id must be a string: %s' % id, key)

    def validate_query_paths(self, key, query_paths):
        if isinstance(query_paths, basestring):
            effective_query_paths = query_paths.split()
        elif isinstance(query_paths, list):
            effective_query_paths = query_paths
        else:
            return self.error('query paths must be either a space-delimited string or a sequence: %s' % query_paths, key)
        for query_path in effective_query_paths:
            self.validate_query_path(key, query_path)
            
    def validate_query_path(self, key, query_path):
        if isinstance(query_path, basestring):
            path_segments = query_path.split()
            for path_segment in path_segments:
                self.validate_query_path_segment_string(key, path_segment)
        elif hasattr(query_path, 'keys'):
            return self.error('structured query paths not supported: %s' % query_path, key)                   
        else:
            return self.error('query-path must be either a space-delimited string or a map: %s' % query_paths, key)            

    def validate_query_path_segment_string(self, key, query_path_segment_string):
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

    def validate_well_known_URLs(self, key, urls):
        if not isinstance(urls, (basestring, list)):
            self.error('well_known_URLs must be a string or an array: %s' % id, key)
        else:
            if isinstance(urls, basestring):
                urls = urls.split()
            for url in urls:
                parsed_url = urlsplit(url)
                if parsed_url.scheme or parsed_url.netloc or not parsed_url.path.startswith('/'):
                    self.error('validate_well_known_URLs must be begin with a single slash %s' % url, key)

    def validate_properties(self, key, properties):
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
            self.check_and_validate_keywords(self.__class__.property_keywords, property)

    def validate_readOnly(self, key, readOnly):
        if not (readOnly is True or readOnly is False) :
            self.error('id must be a boolean: %s' % readOnly, key)

    def validate_selector_location(self, key, location):
        if not location in ['path-segment', 'path-parameter']:
            self.error('%s must be either the string "path-segment" or "path-parameter"' % location)

    def similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio() > self.similarity_ratio
    
    def check_and_validate_keywords(self, keyword_validators, spec):
        for key, value in spec.iteritems():
            if key not in keyword_validators:
                similar_keywords = [keyword for keyword in keyword_validators.iterkeys() if self.similar(key, keyword)]
                message = 'unrecognized keyword %s at line %s, column %s' % (key, key.start_mark.line + 1, key.start_mark.column + 1)
                if similar_keywords:
                    message += ' - did you mean %s?' % ' or '.join(similar_keywords)
                self.info(message)
            else:
                keyword_validators[key](self, key, value)        

    def validate_property_type(self, key, p_type):
        if not p_type in ['array', 'boolean', 'integer', 'number', 'null', 'object', 'string']:
            self.error("type must be one of 'array', 'boolean', 'integer', 'number', 'null', 'object', 'string': " % p_type, key)   
        
            
    def validate_property_format(self, key, format):
        if not isinstance(format, basestring):
            self.error('format must be a string: %s' % format, key)    
            
    def validate_property_relationship(self, key, relationship):
        if hasattr(relationship, 'keys'):
            self.check_and_validate_keywords(self.__class__.relationship_keywords, relationship)
        elif isinstance(relationship, basestring):
            self.check_and_validate_keywords(self.__class__.relationship_keywords, {'entities': relationship})            
        else:
            self.error('relationship must be a string or a map %s' % relationship)        
            
    def validate_property_items(self, key, items):
        self.info('items not yet validated')  
        
    def validate_relationship_entities(self, key, entities):
        if isinstance(entities, basestring):
            entity_urls = entities.split()
        else:
            if not isinstance(entities, list):
                return self.error('entities must be a string or list %s' % s, key)
            else:
                entity_urls = entities
        for entity_url in entity_urls:
            self.validate_entity_url(entity_url, key)  
            
    def validate_relationship_multiplicity(self, key, multiplicity):
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
                        
    def validate_relationship_collection_resource(self, key, collection_resource):
        self.validate_entity_url(collection_resource, key)
            
    rapier_spec_keywords = {'title': validate_title, 'entities': validate_entities, 'conventions': validate_conventions, 'version': validate_version}
    entity_keywords = {'id': validate_id, 'query_paths': validate_query_paths, 'well_known_URLs': validate_well_known_URLs, 'properties': validate_properties, 'readOnly': validate_readOnly}
    conventions_keywords = {'selector_location': validate_selector_location}
    property_keywords = {'type': validate_property_type, 'format': validate_property_format, 'relationship': validate_property_relationship, 'items': validate_property_items, 'readOnly': validate_readOnly}
    relationship_keywords = {'entities': validate_relationship_entities, 'multiplicity': validate_relationship_multiplicity, 'collection_resource': validate_relationship_collection_resource}

    def validate_entity_url(self, entity_url, key):
        # in the future, handle URLs outisde the current document. for now assume fragment URLs
        if not isinstance(entity_url, basestring):
            self.error('entity URL must be a string %s' % entity_url, key)
        elif entity_url not in self.entities:
            self.error('entity not found %s' % entity_url, key)

    def validate(self):
        if not hasattr(self.rapier_spec, 'keys'):
            self.fatal_error('rapier specification must be a YAML mapping: %s' % self.filename)
        self.check_and_validate_keywords(self.__class__.rapier_spec_keywords, self.rapier_spec)

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
        
    def set_rapier_spec_from_filename(self, filename):
        self.filename = filename
        with open(filename) as f:
            self.rapier_spec = self.marked_load(f.read())
            
    def fatal_error(self, message):
        sys.exit(' '. join(['FATAL ERROR -', message, 'in', self.filename]))

    def error(self, message, key_node=None):
        self.errors += 1
        if key_node:
            message += ' after line %s column %s to line %s column %s' % (key_node.start_mark.line + 1, key_node.start_mark.column + 1, key_node.end_mark.line + 1, key_node.end_mark.column + 1)
        print >> sys.stderr, ' '. join(['ERROR -', message, 'in', self.filename])

    def warning(self, message):
        print >> sys.stderr, ' '. join(['WARNING -', message, 'in', self.filename])

    def info(self, message):
        print >> sys.stderr, ' '. join(['INFO -', message, 'in', self.filename])

def main(args):
    validator = OASValidator()
    validator.set_rapier_spec_from_filename(*args)

    validator.validate()

if __name__ == "__main__":
    main(sys.argv[1:])