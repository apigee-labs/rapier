#!/usr/bin/env python 

import sys, codecs
import validate_rapier

class HTMLGenerator(object):

    def generate_property_cell(self, property):
        rslt = property.get('description', '')
        return rslt
    
    def generate_property_rows(self, properties):
        rslt = ''
        for property_name, property in properties.iteritems():
            rslt += '''
                  <tr>
                    <td>%s</td>
                    <td>%s                    </td>
                  </tr>''' % (property_name, self.generate_property_cell(property))
        return rslt

    def generate_properties_table(self, properties):
        property_rows = self.generate_property_rows(properties)
        return '''
              <table class="table">
                <thead>
                  <tr>
                    <th>Property Name</th>
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
    
    def generate_entity_rows(self, entities):
        rslt = ''
        for entity_name, entity in entities.iteritems():
            rslt += '''
          <tr>
            <td>%s</td>
            <td>%s            </td>
          </tr>\n''' % (entity_name, self.generate_entity_cell(entity))
        return rslt

    def generate_entities_table(self, spec):
        entities = spec.get('entities')
        entity_rows = self.generate_entity_rows(entities) if entities is not None else ''
        return \
'''    <table class="table table.striped table.bordered">
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
        rslt = '''
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css">
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.0/jquery.min.js"></script>
  <script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js"></script>
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
    validator = validate_rapier.OASValidator()
    validator.set_rapier_spec_from_filename(*args)

    spec, errors = validator.validate()
    if errors == 0:
        html_generator = HTMLGenerator()
        entities = spec.get('entities')
        rslt = html_generator.generate_html(spec)
        print rslt

if __name__ == "__main__":
    main(sys.argv[1:])
