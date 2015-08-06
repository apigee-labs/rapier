import yaml, sys

def swagger_from_chutzpah(filename):
    with open(filename) as f:
       spec = yaml.load(f.read())
       patterns = spec.get('patterns')
       swagger = {}

       if 'entities' in spec:
           entities = spec['entities']
           definitions = {}
           swagger['definitions'] = definitions
           definitions['ErrorResponse'] = build_error_definition()
           definitions['Collection'] = build_collection_definition()
           for entity, entity_spec in entities.iteritems():
               definition = {}
               definitions[entity] = definition
               if 'properties' in entity_spec:
                   definition['properties'] = entity_spec['properties'].copy()
               if 'relationships' in entity_spec:
                   properties = definition.setdefault('properties',dict())
                   for rel_name, rel_spec in entity_spec['relationships'].iteritems():
                       rel_def = {}
                       properties[rel_name] = rel_def
                       rel_def['type'] = 'string'
                       if 'well_known_URL' in entity_spec:
                           if 'query_paths' in entity_spec:
                               paths = swagger.setdefault('paths', dict())
                               add_query_paths(entity_spec, paths, spec, [[rel_name, rel_spec, None, None]])
                           
       return swagger
       
def build_error_definition():
    return {'required': ['message'], 'properties': {'message': {'type': 'string'}}}

def build_collection_definition():
    return {'required': ['selfLink', 'id', 'type'], 'properties': {'selfLink': {'type': 'string'}, 'id': {'type': 'string'}, 'type': {'type': 'string'}}}
    
def add_query_paths(entity_spec, paths, chutzpah_spec, rel_tuples):
    well_known_URL = entity_spec['well_known_URL']
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
                    add_query_paths(entity_spec, paths, chutzpah_spec, rel_tuples)
        if '/'.join([rel_tuple[0] for rel_tuple in rel_tuples]) in entity_spec['query_paths']:
            emit_query_path(well_known_URL, paths, rel_tuples)
    rel_tuples.pop()
    
def emit_query_path(well_known_URL, paths, rel_tuples):
    rel_tuple = rel_tuples[-1]
    rel_spec = rel_tuple[1]
    multiplicity = rel_spec.get('multiplicity')
    multivalued = multiplicity and multiplicity.split(':')[-1] == 'n'

    path = '/'.join([path_segment(rel_tuple) for rel_tuple in rel_tuples])
    sep = '' if well_known_URL.endswith('/') else '/'
    abs_path = sep.join((well_known_URL, path))
    path_spec = build_entity_path_spec(rel_tuples[-1])
    paths[abs_path] = path_spec
    if multivalued:
        path = '/'.join([path_segment(rel_tuple, inx==len(rel_tuples)-1) for inx, rel_tuple in enumerate(rel_tuples)])
        sep = '' if well_known_URL.endswith('/') else '/'
        abs_path = sep.join((well_known_URL, path))
        path_spec = build_collection_path_spec(rel_tuples[-1])
        paths[abs_path] = path_spec

        
def build_entity_path_spec(rel_tuple):
    path_spec = {'get': {'responses': {'200': {'schema': {'$ref': '#/definitions/%s' % rel_tuple[2]}}, 
                                   'default': {'schmea': {'$ref': '#/definitions/ErrorResponse'}}}}}
    return path_spec

def build_collection_path_spec(rel_tuple):
    path_spec = {'get': {'responses': {'200': {'schema': {'$ref': '#/definitions/Collection'}}, 
                                   'default': {'schmea': {'$ref': '#/definitions/ErrorResponse'}}}}}
    return path_spec

def path_segment(rel_tuple, allow_multivalued = False):
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
    print yaml.dump(swagger_from_chutzpah(*args[1:]))
        
if __name__ == "__main__":
    main(sys.argv)