#!/usr/bin/env python 

import sys, codecs, os
import validate_rapier

class HTMLGenerator(object):

    def generate_property_cell(self, property):
        rslt = property.get('description', '')
        return rslt
    
    def create_link(self, url):
        split_url = url.split('#')
        name = split_url[1]
        if split_url[0] == self.validator.abs_filename:
            url = '#%s' % name
        return '<a href="{}">{}</a>'.format(url, name)
    
    def generate_property_type(self, property):
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
            return '%s (%s)' % (multiplicity, ' or '.join(entity_links))
        type = property.get('type', '')
        if type == 'array':
            items = property['items']
            rslt = '[%s]' % self.generate_property_type(items)
        elif 'properties' in property:
            rslt = self.generate_properties_table(property['properties'])
        else:
            rslt = type
        return rslt
    
    def generate_property_rows(self, properties):
        rslt = ''
        for property_name, property in properties.iteritems():
            rslt += '''
                  <tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s                    </td>
                  </tr>''' % (property_name, self.generate_property_type(property), self.generate_property_cell(property))
        return rslt

    def generate_properties_table(self, properties):
        property_rows = self.generate_property_rows(properties)
        return '''
              <table class="table table-striped table-bordered">
                <thead>
                  <tr>
                    <th>Property Name</th>
                    <th>Property Type</th>
                    <th>Property Description</th>
                  </tr>
                </thead>
                <tbody>%s
                </tbody>
              </table>''' % property_rows

    def allOf(self, allOf):
        if len(allOf) > 1:
            rslt = '''
                <div> 
                Includes properties and other constraints from all of:
                <ul><a href="{0}">{0}</a>
                </ul>
                </div>'''
            row = '''
                    <li>%s
                    </li>'''
            rows = [row.format(os.path.relpath(ref['$ref'], self.validator.abs_filename)) for ref in allOf]
            return rslt % ''.join(rows)
        else:
            return '''
                <div> 
                Includes properties and other constraints from <a href="{0}">{0}</a>
                </div>'''.format(os.path.relpath(allOf[0]['$ref'], self.validator.abs_filename))
             
    def generate_entity_cell(self, entity):
        rslt = entity.get('description', '')
        if 'allOf' in entity:
            rslt = rslt + self.allOf(entity['allOf'])
        properties = entity.get('properties')
        if properties is not None:
            rslt += self.generate_properties_table(properties)
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
        
    def generate_html(self, filename):
        self.validator = validate_rapier.OASValidator()
        spec, errors = self.validator.validate(filename)
        if errors == 0:
            entities = spec.get('entities')
            rslt = '''<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css">
</head>
<body>

  <div class="container">
    <div class="table-responsive">
    %s          
    </div>
  </div>

</body>
</html>
''' % self.generate_entities_table(spec) if entities is not None else ''
            UTF8Writer = codecs.getwriter('utf8')
            sys.stdout = UTF8Writer(sys.stdout)
            return rslt
        else:
            print >>sys.stderr, 'HTML generation of %s failed' % filename

def main(args):
    #try:
    html_generator = HTMLGenerator()
    rslt = html_generator.generate_html(*args)
    print rslt
    #except Exception as e:
    #    print >>sys.stderr, 'HTML generation of %s failed: %s' % (args, e)

if __name__ == "__main__":
    main(sys.argv[1:])
