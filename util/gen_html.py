#!/usr/bin/env python 

import sys, codecs
import validate_rapier

class HTMLGenerator(object):

    def generate_property_cell(self, property):
        rslt = property.get('description', '')
        return rslt
    
    def create_link(self, name):
        return '<a href="{}">{}</a>'.format(name, name[1:])
    
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
            rslt = 'array(%s)' % self.generate_property_type(items)
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

    def generate_entity_cell(self, entity):
        rslt = entity.get('description', '')
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
        
    def generate_html(self, spec):
        entities = spec.get('entities')
        rslt = '''<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
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

def main(args):
    try:
        validator = validate_rapier.OASValidator()

        spec, errors = validator.validate(*args)
        if errors == 0:
            html_generator = HTMLGenerator()
            entities = spec.get('entities')
            rslt = html_generator.generate_html(spec)
            print rslt
    except Exception as e:
        print >>sys.stderr, 'HTML generation of %s failed' % args

if __name__ == "__main__":
    main(sys.argv[1:])
