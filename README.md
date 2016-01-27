# Welcome to Rapier - REST APIs from Entities and Relationships.

## Introduction

The goals of Rapier are to allow REST APIs to be specified with one tenth the effort required with other API specification languages, and to
produce specifications that describe higher quality APIs. \[1\]

You specify an API with Rapier by specifying, in a YAML file, the entities and relationships of the data model that underlies the API. The details of the API's 
HTTP messages are deduced from this specification using the standard patterns described in the HTTP specifications, plus a few conventions 
that we have added. With Rapier, your API is fully specified by the Entities and Relationships of your data model, plus some paths that traverse the relationships that specify queries over the model.
Rapier eliminates the need to repetitively document individual URLs and methods that vary only in the entity they return or the query they express.
This is how Rapier achieves its goals for productivity and quality.

Rapier takes a data-oriented approach to API design, which fits the model of REST and the world-wide-web. If your mental model of
a web API is a network of HTTP resources identified and located using URLs, you should be confortable with Rapier. If you think of a web API
as a set of 'end-points' with 'parameters' (i.e. a more traditional service-oriented model), you may find the Rapier approach less appealing.

Rapier is for specifying new APIs. You will not be able to describe existing APIs with Rapier unless that API used the same conventions that 
Rapier does and was absolutely consistent in applying them.

Rapier documents are complete API specifications — you can give them directly to API developers to implement servers and to app developers to 
implement clients without additional documentation other than the HTTP specs themselves. Since the Rapier specification language is not yet widely 
known and understood, we provide a tool that will generate an Open API Specification (OAS - formerly known as Swagger) 
document from a Rapier specification. The OAS documents spell out the conventions used by Rapier in a way that is familiar to many.
Once you have seen a few examples of the generated OAS, the conventions will become quickly obvious and you may stop looking at the OAS. 
You may wish to continue to generate OAS documents for integrating with tools that are OAS-based, or for communicating with
people who know OAS but not Rapier. 

OAS will likely remain important to you for documenting APIs that which follow a service-oriented rather than a data-oriented design pattern, 
or follow different conventions to the ones Rapier currently understands, or are less consistent than Rapier APIs. 

Rapier also includes SDK generators for Javascript and Python. In the future we intend to work on test tools, and server implementation frameworks.  


\[1\] Following Fred Brooks, we take consistency as being the primary measure of quality of an API. 
“Blaauw and I believe that consistency underlies all principles. A good architecture is consistent in the sense that, given a partial knowledge of the system, one can predict 
the remainder” - Fred Brooks, "The Design of Design", 2010

## Examples

Rapier is very easy to understand and learn. The easiest way is by example. Rapier builds on top of [JSON Schema](http://json-schema.org/),
so if you are not familiar with that standard, you should spend a few minutes getting some level of understanding of what it looks like and what it does.

### Hello World

Here is a 'Hello-world' example in Rapier:
```yaml
title: HelloWorldAPI
entities:
  HelloMessage:
    well_known_URLs: /message
    properties:
      text:
        type: string
```                    
The API defined by this Rapier specification exposes a single resource whose type is `Hello_message` at the URL `/message`. This resource has a single declared property called `text`.
The API does not allow this resource to be deleted, because it is well-known, but it does allow it to be
retrieved using GET and modified using PATCH. You don't have to say this explicitly — it is implied by the standard HTTP patterns and our extensions. Rapier also assumes that a GET response
includes an ETag header that must be echoed in the 'If-Match' request header of the PATCH. This catches problems when two people try to update the resource at the same time.
The `Hello-message` at `/message` will look like this:
```json
    {"text": "Hello, world"}
``` 
The OAS document generated from this Rapier specification can be [found here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-hello-message.yaml). 

### Webmaster

The next step beyond our simple hello-world example is to show a Rapier API that illustrates a relationship:

```yaml
title: Site Webmaster API
entities:
  Site:
    well_known_URLs: /
    properties:
      webmaster:
        type: string
        format: uri
        relationship: '#Person'
  Person:
    properties:
      name:
        type: string
```

Here you see the definition of a property called webmaster that is a URI. The extra Rapier property `relationship` tells you that the entity
that is identified by that URI is a Person. Since Rapier is designed to describe HTTP APIs, we further assume that the URI will be an HTTP URL
that supports methods like GET, PATCH, DELETE, OPTIONS, HEAD etc. The [OAS document](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-todo-list-basic.yaml) generated from this example spells out all the detail,
but if you know the HTTP REST model, you probably know already what it will say.

### To-do List

The example above shows how easy it is to declare a single-valued realtionship. Here is what it looks like if your relationship is multi-valued:

```yaml
title: Todo List API
entities:
  TodoList:
    well_known_URLs: /to-dos
    readOnly: true
    properties:
      items:
        type: string
        format: uri
        relationship:
          collection_resource: '#Collection'
          entities: '#Item'
          multiplicity: O:n
  Item:
    properties:
      description:
        type: string
      due:
        type: string
        format: date-time
non_entity_resources:
  Collection:
    readOnly: true
    properties:
      items:
        type: array
        items: 
          $ref: '#/entities/Item'
```

This API defines a single resource at the well_known_URL `/to-dos` whose type is `To_do_list`. You can see that each `To_do_list` has a relationship 
property called `items`. In this case, the declaration of the relationship property is a bit more complex.
In addition to declaring the entity type at the end of the relationship, it declares the type of the resource that will be used to hold the list of 
entities of the relationship. This is specified in the `collection_resource` property. When `collection_resource` is present, the entity property is assumed to be
a URL that will point to a resource of this type. Clients can perform a GET on this resource to obtain information on the entities of the
relationship and can POST to make new ones. The `Collection` resource is defined in a `non_entity_resources` section of the Rapier spec because 
it is not an entity in the data model - it is a 'technical' resource needed to represent a collection of entities.
In JSON, the `To_do_list` at `/to-dos` will actually look like this:
```json
    {"items": "http://example.org/xxxxx"}
```
The Collection at `http://example.org/xxxxx` will look like this in JSON:
```json
    {"items": [{
         "description": "Get milk on the way home",
         "due": "2016-10-30T09:30:10Z"
         }
      ]
    }
``` 

The format of the resource for multi-valued relationships is under the control of the Rapier author - this Collection format is used here as an example.

### Query Paths
 
So far we have seen examples of APIs that are easy to navigate in a hypertext model. What if I want to include URLs in my API that allow the user to
quickly locate a particular resource without navigating the web of resources from the root to find it? In Rapier, those sorts of URLs are called `Query URLs` and they are declared using `Query Paths`.
A `Query Path` describes a pre-defined path though the web of resources for quickly locating resources. Each `Query Path` implies a URI or [URI Template](https://tools.ietf.org/html/rfc6570) that is part of the API.
The following example should make this clearer.

```yaml
title: Todo List API
version: "0.1"
conventions:
  selector_location: path-segment
entities:
  TodoList:
    well_known_URLs: /to-dos
    query_paths: [items, "items;{id}"]
    readOnly: true
    properties:
      items:
        type: string
        format: uri
        relationship:
          collection_resource: '#Collection'
          entities: '#Item'
          multiplicity: O:n
  Item:
    properties:
      self:
        type: string
        format: uri
        readOnly: true
      id:
        type: string
        readOnly: true
      description:
        type: string
      due:
        type: string
        format: date-time
non_entity_resources:
  Collection:
    readOnly: true
    properties:
      items:
        type: array
        items: 
          $ref: '#/entities/Item'
```                

The combination of the `well_known_URLS` and `query_paths` properties of `To_do_list` implies that the following URL and URL template are valid:

    /to-dos/items
    /to-dos/items/{id} [2]
    

These are examples of 'query URLs'. Query URLs are URLs and URL templates whose format is published by the server as part of the API, and clients are expected to understand their format and compose them. The provision of
hyperlinks in the resources themselves reduces the need for query URLs compared with an API that lacks hyperlinks, but there are still situations where query URLs are important.
In Rapier APIs, query URLs allow clients to navigate along paths defined by the relationships in the Rapier API specification without retrieving intermediate resources. 
The meaning of the first URL is "the resource that is referenced by the items property of the resource at `/todos`" — we are starting at `/todos`
and following the `items` relationship declared in the relationships section. From this, we know that `http://example.org/xxxxx`
and `http://example.org/todos/items` must be URLs for the same resource. An implementation may use the 
same URL for both the perma-link and the query URL in this case, but the API does not require this and clients should not count on it.

In this example, the Collection at `http://example.org/xxxxx` will look like this in JSON:
```json
    {"items": [{
         "self": "http://example.org/yyyyy",
         "id": "10293847",
         "description": "Get milk on the way home",
         "due": "2016-10-30T09:30:10Z"
         }
      ]
    }
``` 

The second URL template indicates that we can form a query URL by tacking the value of the `id` property of an `Item` on to the end 
of `todos/items/` to form a URL that will identify a single `Item`. We know from this and the example above that
`http://example.org/yyyyy` and `http://example.org/todos/items/10293847` must be URLs for the same resource. Since the `id` value is immutable, an implementation may use the 
same URL for both the perma-link and the query URL in this case, but the API does not require this and clients should not count on it. If the
query URL were based on a mutable property like `name` rather than `id`, the perma-link and the query URL would need to be different.
  
You can POST items to `http://example.org/to-dos/items` to create new items, you can PATCH items to change them, 
and you can DELETE items to remove them. You can also perform a GET on `http://example.org/yyyyy`, which will yield:
 
    {
     "self": "http://example.org/yyyyy",
     "id": "10293847",
     "description": "Get milk on the way home",
     "due": "2016-10-30T09:30:10Z"
    }
 
If you want to see the generated OAS document for this API specification, [it is here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-todo-list.yaml)

\[2\] The format of the template is influenced by the convention specification `selector_location: path-segment`. Without that, the template would have been `/to-dos/items;{id}`
 
### Dog Tracker
 
Another popular API example is the 'Dog Tracker' example. In Rapier, it looks lke this:
```yaml 
title: DogTrackerAPI
version: "0.1"
entities:
  DogTracker:
    allOf:
    - $ref: '#/entities/PersistentResource'
    properties:
      dogs:
        description: URL of a Collection of Dogs
        format: uri
        type: string
        relationship:
          collection_resource: '#Collection'
          entities: '#Dog'
          multiplicity: O:n
      people:
        description: URL of a Collection of Persons
        format: uri
        type: string
        relationship:
          collection_resource: '#Collection'
          entities: '#Person'
          multiplicity: O:n
    well_known_URLs: /
    query_paths: [dogs, "dogs;{name}", people, "people;{name}", "dogs;{name}/owner", "people;{name}/dogs"]
    readOnly: true
  Dog:
    allOf:
    - $ref: '#/entities/PersistentResource'
    properties:
      name:
        type: string
      birth_date:
        type: string
      fur_color:
        type: string
      owner:
        format: uri
        type: string
        relationship:
          entities: '#Person'
  Person:
    allOf:
    - $ref: '#/entities/PersistentResource'
    properties:
      name:
        type: string
      birth-date:
        type: string
      dogs:
        format: uri
        type: string
        relationship:
          collection_resource: '#Collection'
          entities: '#Dog'
          multiplicity: O:n
#Boilerplate entities from here
  Resource:
    abstract: true
    type: object
    properties:
      self:
        type: string
        readOnly: true
      kind:
        type: string
  PersistentResource:
    allOf:
    - $ref: '#/entities/Resource'
    abstract: true
    properties:
      created:
        type: string
        format: date-time
        readOnly: true
      creator:
        type: string
        format: URL
        readOnly: true
      modified:
        type: string
        format: date-time
        readOnly: true
      modifier:
        type: string
        format: date-time
        readOnly: true
    abstract: true
non_entity_resources:
  Collection:
    allOf:
    - $ref: '#/entities/Resource'
    properties:
      kind:
        type: string
        enum: [Collection]
      items:
        type: array
        items: 
          type: object
    readOnly: true
```
This API defines a single resource at the URL `/dog-tracker` whose type is `Dog_tracker`. In the relationships section, you can see that each `Dog_tracker` has properties
called `dogs` and `people` that point to the Dogs and Persons that are tracked. The value of each of these will be a URL that points to a Collection
resource that contains information on each Dog or Property. You can POST to either of these Collections to create new \[resources for\] Dogs or Persons. From the `well_known_URLs` and `query_paths` 
properties of `Dog-tracker` we know that these Collections can also be accessed at `/dog-tracker/dogs` and `/dog-tracker/people` respectively.

The API also defines a relationship between Dogs and Persons, which is called `owner` on one side and `dogs` on the other. The `owner` property is settable on each Dog - this is in fact
the only way to change which Person owns a Dog. When a Dog is created by POSTing to `/dog-tracker/dogs`, the `owner` property may be set by the client. If a Dog is POSTed to the `dogs` Collection of a specific
Person, the server would presumably set the `owner` property appropriately.

From the `well_known_URLs` and `query_paths` properties, you can infer that the following URLs and URL templates are part of the API:

    /dog-tracker
    /dog-tracker/dogs
    /dog-tracker/dogs;{name}
    /dog-tracker/dogs;{name}/owner
    /dog-tracker/people
    /dog-tracker/people;{name}
    /dog-tracker/people;{name}/dogs

Since you know the pattern, you already know what all these mean, but if you want to see a generated OAS document for this API specification, [it is here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-dog-tracker.yaml)

### Property Tracker
 
The next example shows a more complex set of relationships. In this example, a Dog can be owned by a Person or an Institution and People and Institutions can own Bicycles as well as Dogs.
The [source for this example is here](https://github.com/apigee-labs/rapier/blob/master/util/test/property-tracker.yaml). 
This example strains the expressive power of OAS - you can see a generated [OAS document here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-property-tracker.yaml).

### Spec Repo

Not every resource has structured content that can be expressed as JSON. Even for resources whose content can be expressed as JSON, there is sometimes a requirement to preserve the exact document format, character-by-character.
Resources with this characteristic must be updated with PUT instead of PATCH, and their properties must be stored outside of the resource content. [This sample](https://github.com/apigee-labs/rapier/blob/master/util/test/spec-hub.yaml) 
shows an example of how Rapier handles this case. Here is the [corresponding generated OAS document](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-spec-hub.yaml).
The SpecHub API includes some 'internal' URL tamplates that are used in the implementation but are not part of the API. The Rapier OAS generator supports a -i command-line option that allows the implementation
view of the API to be generated instead of the client view. It can be found [here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-spec-hub-with-impl.yaml).

## Navigating the Repository

- js - a directory containing a Node package that is used by the generated Javascript SDK
- py - a directory contains a Python module that is used by the generated Python SDK
- test-servers - a directory contains some simple servers used to test the genenrated SDKs
- util - directory containing the sdk generators and the OAS generator. This directory is a Python module
  - gen_openapispec.py - the OAS generator
  - gen_js_sdk.py - the Javascript SDK genenrator
  - gen_py_sdk.py - the Python SDK genenrator
  - requirements.txt - the pip file with the python dependencies for these generators
  - test - a directory containing tests for the generators. This directory contains numerous samples.
    - gen_openapispec - a directory containing openapispec files generated from the samples
    - gen_js_sdk - a directory containing Javascript sdk files generated from the samples
    - gen_js_sdk - a directory containing Python sdk files generated from the samples

## The Rapier Language Spec

### Schema

All properties are optional unless otherwise specified.

#### <a name="rapier"></a>Rapier

Field Name | Type | Description
---|:---:|---
title | `string` | The title of the API. Dublin Core title. The default is 'untitled'
version | `string` | The version of the API. The default is 'initial'
entities | [Entities](#entities) | The entities of the API.
consumes | `array` of [Media Type](media_type) | The media-types that may be used by clients when providing data in POST and PUT requests. The valid values for the Content-Type HTTP header in those requests. May also be specified as a single string, which is interpreted as a space-delimited list. This value can be overridden at a relationship level
produces | `array` of `strings' | The media-types that clients can request from the server in GET, POST, PUT, PATCH and DELETE requests. The valid values for the Accept HTTP header in those requests. May also be specified as a single string, which is interpreted as a space-delimited list. This value can be overridden at a relationship level

#### <a name="entities"></a>Entities

The set of entities defines the API.

Field Pattern | Type | Description
---|:---:|---
{entity name} | [Entity](#entity) | The name of an entity. Provides the default value of the id of the entity. That is, if the entity does not have an explicit id value, it can be addressed using the URI fragment `#{entity name}`. For more infomation on this, see the [Rapier data model decription](https://github.com/apigee-labs/rapier/blob/master/data_model.md)

#### <a name="entity"></a>Entity

Each entity is a [JSON Schema](http://json-schema.org/). It includes the standard JSON Schema properties (e.g. `properties`) as well as some Rapier-specific ones.

Field Name | Type | Description
---|:---:|---
id | `string` | The id of the entity. The default value is the name of the entity. If the Entity has an explicit id value, it can be addressed using the URI fragment `#{id}`. If it does not have an explicit id value, it can be addressed using the URI fragment `#{entity name}`. For more infomation on this, see the [Rapier data model decription](https://github.com/apigee-labs/rapier/blob/master/data_model.md)
query_paths | `string` or `array` of [Query Path](#query_path) | If the value is a string, it is interpreted as a space-deliminated list of `query paths`.
well_known_URLs | `string` or `array` of URLs | Well-known URLs at which a resource of this entity type can be found. If the value is a string, it is interpreted as a space-deliminated list of URLs. If the value is an array, each item is interpreted as a single URL. URLs must be path-absolute - i.e. they must begin with a single '/'.
properties | [Properties](#properties) | The properties of the entity. This is the standard JSON Schema `properties` property, with some Rapier extensions.
readOnly | `string` | Indicates that resources of this Entity type can be read (GET, HEAD and OPTIONS methods are supported), but not written (PATCH, PUT and DELETE are not allowed). Exceptionally, this property name is in camelCase rather than snake_case to align with the JSON Schema property of the same name.

#### <a name="properties"></a>Properties

Field Pattern | Type | Description
---|:---:|---
{property name} | [Property](#property) | A property name.

#### <a name="property"></a>Property

Each property is a JSON Schema. It includes the standard JSON Schema properties (e.g. `type`, `format`, `readOnly`) as well as the following Rapier-specific ones. `readOnly` is interpreted to mean that the property may appear in a GET, but may not be set by the client in a POST, PUT or PATCH.

TODO: Support the common case of a 'write-once' property that can be set on POST, but not modified on PUT or PATCH. 

Field Name | Type | Description
---|:---:|---
relationship | [Relationship](#relationship) | States that the property is a relationship property. If this property is present, the type of the property must be `string` with a `format` of `uri`. 
 
#### <a name="relationship"></a>Relationship

Describes [one end of] a relationship to one or more other entities

Field Name | Type | Description
---|:---:|---
entities | `string` or `array` of URLs | A set of URLs of the entities this relationship may reference. If the value is a string, it is interpreted as a space-deliminated list of URLs. If the value is an array, each item is interpreted as a single URL.
multiplicity | `string` | The multiplicity of the relationship. The value is of the form x:y or just y. If the value of y is `n`, or a number greater than 1, then the relationship is multi-valued. If x is missing, it is presumed to be 0.
relationship_resource | `url` | May only be set if the relationship is multi-valued. Its value is the URL of a JSON Schema for the 'collection-like' resource that represents the multi-valued relationship. The 'collection-like' resource should include, 
at a minimum, the URLs of the entities in the relationship.

#### <a name="query_path"></a>Query Path

A `query path` defines an URL in the API that represents a traversal of a declared relationship. For example, if an Entity called 
Child has a relationship property called 'mother',
then declaring the `query path` 'mother' for the Child entity says that
the URI template `{child-URL}/mother` is also part of the API where child-URL is the URL of any child. In other words, for a given value of child-URL, the
URL `{child-URL}/mother` is guaranteed to be a valid URL, and further, 
it is guaranteed to be an alias of the URL in the 'mother' property of the resource at `child-URL`.

A `query path` can be represented as a string. Here are some examples with their meaning:  
 
- `mother` - traverse the mother relationship. URL template is \{`child-URL`\}/mother  
- `siblings` - traverse the siblings relationship.  URL template is \{`child-URL`\}/siblings. Will return a collection  
- `siblings;{name}` - traverse the sibling relationship. Use the `name` property of the siblings to select a single sibling. URL template is \{`child-URL`\}/siblings;\{name\}  
- `siblings;name={name}` - same as the previous example except the URL template is \{`child-URL`\}/siblings;name=\{name\}  

Multiple query paths may be included in the same string as a space-deliminated list.

Alternatively, you can provide a query path as a JSON object:

Field Name | Type | Description
---|:---:|---
segments | `array` of [Query Path Segment](#query_path_segment) | A segment of a query path.

#### <a name="query_path_segment"></a>Query Path Segment

Describes one segment of a query path. Each segment corresponds to a single relationship being traversed.

Field Name | Type | Description
---|:---:|---
relationship | `string` | The name of the relationship for this segment
selectors | `array` of [Selector](#selector) | For multi-valued relationships, defines the properties that will be used to filter the relationship members. May be specified as a simple string, in which case the string is specified as a space-delimited list of property names
separator | `string` | The string that separates the relationship name from the selectors in the query URL. Default value is ';'. Popular alternative is '/'.
selector_template | `string` | A [URI Template](https://tools.ietf.org/html/rfc6570) for the selectors. For example: "`name={},age<{}`"

#### <a name="selector"></a>Selector

Describes one selector in a segment. Each selector corresponds to a single property of the elements of a relationship.

Field Name | Type | Description
---|:---:|---
property_name | `string` | the name of the property

#### <a name="media_type"></a>Media Type

Describes a media type. If a media type is given as a simple string, it applies to all entity types. If the media type is given as a JSON structure, you can say which entity types use it

Field pattern | Type | Description
---|:---:|---
{entity_id} | `array` of `string`s | the media types to be used with the associated entity. The list of media types may be given as an array or a space-deliminated list in a single string