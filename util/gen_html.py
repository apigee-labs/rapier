#!/usr/bin/env python 

import sys, codecs, os
import validate_rapier

class HTMLGenerator(object):

    def generate_property_cell(self, property):
        rslt = property.get('description', '')
        return rslt
    
    def create_link(self, uri_ref):
        uri_ref = self.validator.relative_url(uri_ref)
        split_ref = uri_ref.split('#')
        split_ref[1] = split_ref[1].split('/')[-1]
        url = split_ref[0]
        if url.endswith('.yaml'):
            split_ref[0] = url[:-4] + 'html'
        uri_ref = '#'.join(split_ref)
        return '<a href="{}">{}</a>'.format(uri_ref, split_ref[1])
    
    def generate_property_type(self, entity, property):
        if 'relationship' in property:
            relationship = property['relationship']
            if isinstance(relationship, basestring):
                entity_urls = relationship.split()
                multiplicity = '0:1'
            elif isinstance(relationship, list):
                entity_urls = relationship
                multiplicity = '0:1'                
            else:
                entity_urls = relationship['entities']
                if isinstance(entity_urls, basestring):
                    entity_urls = entity_urls.split()
                multiplicity = relationship.get('multiplicity', '0:1')
            entity_links = [self.create_link(entity_url) for entity_url in entity_urls]
            upper_bound = multiplicity.split(':')[-1]
            multi_valued = upper_bound == 'n' or int(upper_bound) > 1
            return '%s (%s)' % (multiplicity, ' or '.join(entity_links)) if multi_valued else 'url of %s' % ' or '.join(entity_links)
        elif '$ref' in property:
            ref = property['$ref']
            return self.create_link(ref)
        else:
            type = property.get('type', '')
            if type == 'array':
                items = property['items']
                rslt = '[%s]' % self.generate_property_type(entity, items)
            elif 'properties' in property:
                rslt = self.generate_properties_table(entity, property['properties'])
            else:
                format = property.get('format')
                if format is not None:
                    rslt = format
                else:
                    rslt = type
            return rslt
            
    def generate_property_usage(self, entity, property):
        entity_readOnly = entity.get('readOnly')
        if entity_readOnly is None:
            entity_usage = entity.get('usage')            
            readOnly = property.get('readOnly')
            if readOnly is None:
                usage = property.get('usage')
                if usage is None:
                    return 'c r u'
                else:
                    result = ''
                    if len(validate_rapier.OASValidator.c_usage_values & set(as_list(usage))) > 0:
                        result += 'c'
                    if len(validate_rapier.OASValidator.r_usage_values & set(as_list(usage))) > 0:
                        result += 'r'                    
                    if len(validate_rapier.OASValidator.u_usage_values & set(as_list(usage))) > 0:
                        result += 'u'
                    return ' '.join(result)
        return 'r'            
    
    def generate_property_rows(self, entity, properties):
        rslt = ''
        for property_name, property in properties.iteritems():
            rslt += '''
                  <tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s                    </td>
                    <td>%s                    </td>
                  </tr>''' % (property_name, self.generate_property_cell(property), self.generate_property_type(entity, property), self.generate_property_usage(entity, property))
        return rslt

    def generate_properties_table(self, entity, properties):
        property_rows = self.generate_property_rows(entity, properties)
        return '''
              <table class="table table-striped table-bordered">
                <thead>
                  <tr>
                    <th>Property Name</th>
                    <th>Property Description</th>
                    <th>Property Type</th>
                    <th>usage</th>
                  </tr>
                </thead>
                <tbody>%s
                </tbody>
              </table>''' % property_rows

    def allOf(self, allOf):
        def replace_dot_yaml(url):
            split_url = url.split('#')
            if split_url[0].endswith('.yaml'):
                split_url[0] = split_url[0][:-4] + 'html'
                url = '#'.join(split_url)
        if len(allOf) > 1:
            rslt = '''
                <div> 
                Includes properties and other constraints from all of:
                <ul><{0}</a>
                </ul>
                </div>'''
            row = '''
                    <li>%s
                    </li>'''
            rows = [row.format(self.create_link(ref['$ref'])) for ref in allOf]
            return rslt % ''.join(rows)
        else:
            return '''
                <div> 
                Includes properties and other constraints from {0}
                </div>'''.format(self.create_link(self.entities[allOf[0]['$ref']]['id']))
             
    def generate_entity_cell(self, entity):
        rslt = entity.get('description', '')
        if 'allOf' in entity:
            rslt = rslt + self.allOf(entity['allOf'])
        properties = entity.get('properties')
        if properties is not None:
            rslt += self.generate_properties_table(entity, properties)
        return rslt
    
    def create_anchor(self, name):
        return '<a name="{0}"></a>{0}'.format(name)
    
    def generate_entity_rows(self, entities):
        rslt = ''
        for entity_name, entity in entities.iteritems():
            rslt += '''
          <tr>
            <td>%s</td>
            <td>%s            </td>
          </tr>\n''' % (self.create_anchor(entity_name), self.generate_entity_cell(entity))
        return rslt

    def generate_entities_table(self, spec):
        entities = spec.get('entities')
        entity_rows = self.generate_entity_rows(entities) if entities is not None else ''
        return \
'''    <table class="table table-bordered">
        <thead>
            <tr>
                <th>Entity Name</th>
                <th>Entity Description</th>
            </tr>
        </thead>
        <tbody>%s
        </tbody>
    </table>''' % entity_rows
        
    def generate_header(self, spec):
        version = str(spec.get('version', 'initial'))
        # If it's a string that looks like a number, add quotes around it so its clear it's a string
        try:
            number = float(version)
            version_str = repr(version)
        except ValueError:
            version_str = version
        return '''<h1>%s</h1>
    <h2>Id: %s</h2>
    <h2>Version: %s</h2>
    <p>%s</p>
        '''% (spec.get('title', 'untitled'), spec.get('id', '"#"'), version_str, spec.get('description', 'undescribed'))
    
    def generate_html(self, filename):
        self.validator = validate_rapier.OASValidator()
        spec, errors = self.validator.validate(filename)
        if errors == 0:
            
            self.entities = self.validator.build_included_entity_map()
            entities = spec.get('entities')
            rslt = '''<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="content-type" content="text/html; charset=UTF-8">
  <link rel="stylesheet" href="http://design.apigee.com/ui-framework/latest/css/ui-framework-core.css">
  <link href='https://fonts.googleapis.com/css?family=Source+Sans+Pro:400,400italic,700,700italic,300,300italic' rel='stylesheet' type='text/css'>
</head>
<body>
  <div class="container">
    %s
    <p>
    <div class="table-responsive">
    %s          
    </div>
  </div>

</body>
</html>
''' % (self.generate_header(spec), self.generate_entities_table(spec) if entities is not None else '')
            UTF8Writer = codecs.getwriter('utf8')
            sys.stdout = UTF8Writer(sys.stdout)
            return rslt
        else:
            print >>sys.stderr, 'HTML generation of %s failed' % filename

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
    
def main(args):
    #try:
    if not len(args) == 1:
        usage = 'usage: gen_html.py filename'
        sys.exit(usage)
    html_generator = HTMLGenerator()
    rslt = html_generator.generate_html(*args)
    print rslt
    #except Exception as e:
    #    print >>sys.stderr, 'HTML generation of %s failed: %s' % (args, e)

if __name__ == "__main__":
    main(sys.argv[1:])
