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
The URI of the Mother entity is <baseURL>#Mother. This is why the line `relationship: '#Child'` is valid - '#Mother' is a valid URI reference.

In Rapier, the following two URIs reference different things
- `#Mother`
- `#/entities/Mother`
The first URI reference identifies an Entity, while the second identifies a JSON object. The JSON object is not the Entity - the JSON Object describes the Entity.
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
implementation_only:
  Child:
    properties:
      database_primary_key:
        type: integer
``` 

`#/entities/Child` and `#/implementation_only/Child` are two different JSON objects, but they both describe the same entity, whose URI reference is `#Child`.
This means that `#/implementation_only/Child` is providing additional information about the same entity that was described by `#/entities/Child`. In this case,
it is telling us about a new property of `#Child` that we didn't know about before. This new property is private to the implementation; it is not part of the API.
The API could also have been described as follows, although Rapier does not currently allow this syntax (maybe it should):

```yaml
- kind: 'https://github.com/apigee/rapier#Entity'
  id: '#Child'
  properties:
    - name: mother
      type: string
      format: uri
      relationship: '#Child'
    - name: database_primary_key
      implementation_only: True
      type: integer
- kind: 'https://github.com/apigee/rapier#Entity'
  id: '#Mother'
``` 

Those of you who are familiar with RDF or with more thoughtful discussions of the meanings of URLs will find nothing original or suprising in this model.