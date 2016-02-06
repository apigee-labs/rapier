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

    def validate_title(self, key, title):
        if not isinstance(title, basestring):
            self.errors += 1
            print >> sys.stderr, 'ERROR - title must be a string following line %s, column %s' % (key.end_mark.line + 1, key.end_mark.column + 1)
        
    def validate_entities(self, key, entities):
        pass

    rapier_spec_keywords = {'title': validate_title, 'entities': validate_entities}

    def similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio() > self.similarity_ratio
            
    def validate(self):
        if not hasattr(self.rapier_spec, 'keys'):
            sys.exit('rapier file must begin with a map: %s' % self.filename)
        for key, value in self.rapier_spec.iteritems():
            keyword_validators = self.__class__.rapier_spec_keywords
            if key not in keyword_validators:
                similar_keywords = [keyword for keyword in keyword_validators.iterkeys() if self.similar(key, keyword)]
                message = 'INFO - unrecognized keyword %s at line %s, column %s' % (key, key.start_mark.line + 1, key.start_mark.column + 1)
                if similar_keywords:
                    message += ' - did you mean %s?' % ' or '.join(similar_keywords)
                print >> sys.stderr, message
            else:
                keyword_validators[key](self, key, value)

    def marked_load(self, stream):
        def construct_mapping(loader, node):
            keys = [node_tuple[0].value for node_tuple in node.value]
            for item, count in Counter(keys).items():
                if count > 1:
                    key_nodes = [node_tuple[0] for node_tuple in node.value if node_tuple[0].value == item]
                    self.errors += 1
                    print >> sys.stderr, 'WARNING - %s occurs %s times, at %s' % (item, count, ' and '.join(['line %s, column %s' % (key_nodes.start_mark.line + 1, key_nodes.start_mark.column + 1) for key_nodes in key_nodes]))            
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

def main(args):
    validator = OASValidator()
    validator.set_rapier_spec_from_filename(*args)

    validator.validate()

if __name__ == "__main__":
    main(sys.argv[1:])