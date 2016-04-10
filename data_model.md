If you are just using Rapier, you can easily learn it by following the tutorials. If you are trying to design a modification to Rapier or an extensio to Rapier,
it may be useful to understand Rapier's data model and its approach to defining URLs. Consider the following Rapier spec:
```yaml
entities:
  Mother: {}
  Child:
    properties:
      mother:
        type: string
        format: uri
        relationship: '#Child'
```
In Rapier, this is a shorthand syntax for this:
```yaml
entities:
  Mother:
    id: '#Mother'
  Child:
    properties:
      mother:
        type: string
        format: uri
        relationship: '#Child'
```
The URI of the Mother entity is `<baseURL>#Mother`. This is why the line `relationship: '#Child'` is valid - `#Mother` is a valid URI reference.

In Rapier, the following two URIs reference different things
- `#Mother`
- `#/entities/Mother`

The first URI reference identifies an Entity, while the second identifies a JSON object. The JSON object is not the Entity—the JSON Object describes the Entity.
Because of this, `relationship: '#/entities/Child'` would be incorrect.

This distinction becomes important in the following example:

```yaml
entities:
  Mother: {}
  Child:
    properties:
      mother:
        type: string
        format: uri
        relationship: '#Child'
implementation_private_information:
  Child:
    permalink_template:
      template: /c3Rvc-Z3Jw-{implementation_key} 
      type: integer
``` 

`#/entities/Child` and `#/implementation_private_information/Child` are two different JSON objects, but they both describe the same entity, whose URI reference is `#Child`.
This means that `#/implementation_private_information/Child` is providing additional information about the same entity that was described by `#/entities/Child`. 
The API could also have been described as follows, although Rapier does not currently allow this syntax (maybe it should):

```yaml
- kind: 'https://github.com/apigee-labs/rapier/ns#Entity'
  id: '#Mother'
- kind: 'https://github.com/apigee-labs/rapier/ns#Entity'
  id: '#Child'
  properties:
    - name: mother
      type: string
      format: uri
      relationship: '#Child'
    permalink_template:
      template: /c3Rvc-Z3Jw-{implementation_key} 
      type: integer
``` 

Those of you who are familiar with RDF or with some of the more thoughtful discussions of URLs and their meanings will find nothing original or suprising in this model.