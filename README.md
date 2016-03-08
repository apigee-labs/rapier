# Rapier - REST APIs from Entities and Relationships

## Table of Contents
- [Introduction](#introduction)
- [Tutorial](#tutorial)
- [Navigating the Repository](#navigating)
- [Specification](#specification)
- [OpenAPI Generator](#oas_generator)

## <a name="introduction">Introduction

Rapier is a new API specification language created by Apigee. The goals of Rapier are to allow REST APIs to be specified and learned with one tenth the effort required with other API specification languages, and to
produce specifications that describe higher quality APIs. [\[1\]](#footnote1)

You specify an API with Rapier by specifying in YAML the entities and relationships of the data model that underlies the API, along with query paths traversing the relationships. The details of the API's 
HTTP messages are deduced from this specification using the standard patterns described in the HTTP specifications, plus a few conventions 
that we have added. Rapier thereby eliminates the need to repetitively document individual URLs and their methods, which vary only in the entities 
they accept and return or the queries they express.

Rapier is for specifying new APIs. You will not be able to describe existing APIs with Rapier unless that API uses the same conventions that 
Rapier does and is perfectly consistent in applying them.

Rapier takes a data-oriented approach to API design, which aligns with the model of the world-wide-web. If your mental model of
an API is a network of HTTP resources identified and located using URLs, you should be comfortable with Rapier. If you think of a web API
as a set of 'end-points' with 'parameters' (a traditional service-oriented or RPC model), the Rapier approach may not resonate with you.

While Rapier APIs conform to the principles of REST, including the provision of hypermedia links, Rapier APIs do not require special clients that adapt
to changing server data formats—most clients of Rapier APIs are quite conventional.

Since the Rapier specification language is not yet widely 
known and adopted, we provide a tool that will generate an OpenAPI (formerly known as Swagger)
document from a Rapier specification. The generated OpenAPI document allows 
you to learn the precise details of the HTTP messages implied by the Rapier specification, the HTTP specifications and our additional conventions.
Generating OpenAPI documents is also useful for integrating with tools that are based on OpenAPI, or for communicating with
people who know OpenAPI but not Rapier. Even if you adopt Rapier enthusiastically, OpenAPI will likely remain important to you for documenting APIs that follow a service-oriented rather than a data-oriented design pattern, 
or follow different conventions to the ones Rapier currently understands, or are less consistent than Rapier APIs. Rapier is designed to complement, not replace, OpenAPI.

Rapier also includes SDK generators for Javascript and Python. A validator is in development. In the future we may work on test tools, and server implementation frameworks.  

<a name="footnote1">\[1\] Following Fred Brooks, we take consistency as being the primary measure of quality of an API. 
“Blaauw and I believe that consistency underlies all principles. A good architecture is consistent in the sense that, given a partial knowledge of the system, one can predict 
the remainder” - Fred Brooks, "The Design of Design", 2010

## <a name="tutorial">Tutorial

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
The API defined by this Rapier specification exposes a single resource whose type is `HelloMessage` (a JSON Schema) at the URL `/message`. This resource has a single property called `text`.
The API does not allow this resource to be deleted, because it is well-known, but it does allow it to be
retrieved using GET and modified using PATCH. [\[2\]](#footnote2) You don't have to say this explicitly — it is implied by the standard HTTP patterns and our conventions. Rapier also assumes that a GET response
includes an ETag header that must be echoed in the 'If-Match' request header of the PATCH. This catches problems when two people try to update the resource at the same time.
The `Hello-message` at `/message` will look like this:
```json
    {"text": "Hello, world"}
``` 
The OpenAPI document generated from this Rapier specification can be [found here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-hello-message.yaml). 

[\[2\]](#footnote2) Rapier assumes PATCH for structured objects and PUT for unstructured or semi-structured documents 

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

Here you see the definition of a property called webmaster whose value is a URI. The extra Rapier property `relationship` tells you that the entity
that is identified by that URI is a Person. Since Rapier is designed to describe HTTP APIs, we further assume that the URI will be an HTTP URL
that supports methods like GET, PATCH, DELETE, OPTIONS, and HEAD. The [OpenAPI document](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-todo-list-basic.yaml) generated from this example spells out all the detail.

### <a name="to_do_list"></a>To-do List

The example above shows how to declare a single-valued realtionship. Here is what it looks like if your relationship is multi-valued:

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
relationship and can POST to make new ones.
In JSON, the `To_do_list` at `/to-dos` will look like this:
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

If you want to see the generated OpenAPI document for this API specification, [it is here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-todo-list-basic.yaml)

### Query Paths
 
So far we have seen examples of APIs that are easy to navigate by following hyperlinks. What if I want to include URLs in my API that allow the user to
quickly locate a particular resource without navigating the web of resources from the root to find it? In Rapier, those sorts of URLs are called `Query URLs`. 
In contrast to hyperlinks, which are opaque, query URLs have formats that clients are expected to understand in order to compose them. Hyperlinks are
expected to be stable over time—you should be able to safely bookmark them or store them in a database, and when you recover them and reuse them, they should identify the same permanent entity. 
By contrast, query URLs, as the name implies, may return variable results over time, or may fail altogether in the future. For this reason, in most cases, it will be inappropriate to bookmark query URLs or to
store them in databases.
`Query URLs` are defined in Rapier using `Query Paths`.
A `Query Path` describes a path along the relationships between resources for quickly locating resources without having to retrieve all the resources along the path. 
Each segment of a `query path` corresponds to a relationship declared in the data model.
Each `Query Path` implies a URI or [URI Template](https://tools.ietf.org/html/rfc6570) that is part of the API.
The following example should make this clearer.

```yaml
title: Todo List API
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
      id:
        type: string
        readOnly: true
      description:
        type: string
      due:
        type: string
        format: date-time
  Collection:
    readOnly: true
    properties:
      items:
        type: array
        items: 
          $ref: '#/entities/Item'
```                

The combination of the `well_known_URLS` and `query_paths` properties of `To_do_list` implies that the following `Query URL` and URL template are valid:

    /to-dos/items
    /to-dos/items/{id} [3]

The provision of
hyperlinks in the resources themselves reduces the need for query URLs compared with an API that lacks hyperlinks, but there are still situations where query URLs are important.
The meaning of the first URL is "the resource that is referenced by the items property of the resource at `/todos`". In other words, we are starting at `/todos`
and following the `items` relationship declared in the data model, but without having to retrieve the resource at `/todos`. 
The second URL template indicates that we can form a query URL by appending the value of the `id` property of an `Item` on to the end 
of the URL `todos/items` to form a URL that will identify a single `Item` amongst the collection of items at `todos/items`. 

`/to-dos/items` and `/to-dos/items/{id}` are valid because there is a TodoList at `/to-dos`, but the template is valid for any TodoList URL, like this:

    {TodoList-URL}/items
    {TodoList-URL}/items/{id}
    
In the [To-do List example](#to_do_list) above, the value of the items property of the TodoList at `/to-dos` was shown as `http://example.org/xxxxx`. From this we know that `http://example.org/xxxxx` and 
`http://example.org/to-dos/items` must be aliases of each other, and a particular implementation may choose to make them the same (or not).

If you want to see the generated OpenAPI document for this API specification, [it is here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-todo-list-with-id.yaml)

\[3\] The format of the URI template is influenced by the convention specification `selector_location: path-segment`. Without that, the template would have been `/to-dos/items;{id}`

### Hiding the implementation detail

In the example above, we exposed an `id` property of an item and used it in a `query path`. This is a very common pattern in API design, but we do not consider it a best practice.
A better practice is to keep the `id` private to the implementation by providing the client of the API with an opaque URL to use rather than an `id` property value and a URL template. 
This avoids the need for the client to plug an `id` value into a template to get the URL of an entity—this job has already been done by the server. 
The entity URL can also be used in other URL templates, in the same maner that an `id` value can be used, so there is no loss of function in the API.
The URL of each entity is already available to the API client in the `Location` and `Content-Location` response headers of POST and GET or HEAD requests, but
when entities appear nested in collection resources, no header value is available to identify the nested resources, so it's useful to
also put the resource URL in a property in the representation, as follows:

```yaml
title: Todo List API
version: "0.1"
conventions:
  selector_location: path-segment
entities:
  TodoList:
    well_known_URLs: /to-dos
    query_paths: [items]
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
      description:
        type: string
      due:
        type: string
        format: date-time
  Collection:
    readOnly: true
    properties:
      items:
        type: array
        items: 
          $ref: '#/entities/Item'
```                

The changes are to replace the integer- or string-valued `id` property with a URL-valued `self` property, and to eliminate the `items;{id}` query path. 
We don't need this query path any more because its only purpose was to give the client this information it needed to form the URL that is now included in the self property.
The format of the `self` URL should be opaque to the API clients,
and it is a reasonable practice to obfuscate these URLs to clearly indicate which URLs are client-parsable `query URLs`, and which URLs are opaque.

In JSON, the `To_do_list` at `/to-dos` will look like this:
```json
    {"items": "http://example.org/xxxxx"}
```
The Collection at `http://example.org/xxxxx` will look like this in JSON:
```json
    {"items": [{
         "self": "http://example.org/yyyyy",
         "description": "Get milk on the way home",
         "due": "2016-10-30T09:30:10Z"
         }
      ]
    }
``` 

If you want to see the generated OpenAPI document for this API specification, [it is here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-todo-list-with-self.yaml)
 
### Query Parameters

Specifying Query URLs using `query paths` covers some interesting cases, but what about straightforward query parameters in the
query string portion of URLs? Rapier allows you to specify this on entities using the same syntax as OpenAPI. Here is an example:
```yaml
  PetCollection:
    properties:
      items:
        type: array
        items: 
          $ref: '#/entities/Pet'
    query_parameters:
    - name: tags
      items:
        type: string
      type: array
      collectionFormat: multi
      required: false
    - name: status
      type: integer
      collectionFormat: multi
      required: false
    readOnly: true
```
This definition comes from the Pet Store example. The full Rapier document [is here](https://github.com/apigee-labs/rapier/blob/master/util/test/petstore.yaml) and the generated OpenAPI specification [is here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-petstore.yaml). 

We have seen three common patterns for query parameters on entities:
- parameters that are specific to querying a collection. Examples are `limit`, `orderBy`, `direction` (ascending | descending). These are essentially properties of the collection itself. 
- a "projection" parameter that limits the fields being returned. In that case, the query parameter itself is not declared elsewhere, but its valid valid values would be declared properties of the entity
- parameters that select entities from a collection that match a particular property value. In this case the parameter is really a property of the the entity that defines the elements of the collection

Given this structure, we may model query parameters more carefully in the future.

### Dog Tracker
 
Another popular API example is the 'Dog Tracker' example. The Rapier spec for it [is here](https://github.com/apigee-labs/rapier/blob/master/util/test/dog-tracker.yaml). 
It shows a more complete example using the techniques we have already seen.
The generated OpenAPI document for this API specification [is here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-dog-tracker.yaml)

### Property Tracker
 
The next example shows a more complex set of relationships. In this example, a Dog can be owned by a Person or an Institution and People and Institutions can own Bicycles as well as Dogs.
The [source for this example is here](https://github.com/apigee-labs/rapier/blob/master/util/test/property-tracker.yaml). 
This example strains the expressive power of OpenAPI - you can see a generated [OpenAPI document here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-property-tracker.yaml).

### Spec Repo

Not every resource has structured content that can be expressed as JSON. Even for resources whose content can be expressed as JSON, there is sometimes a requirement to preserve the exact document format, character-by-character.
Resources with this characteristic must be updated with PUT instead of PATCH, and their properties must be stored outside of the resource content. [This sample](https://github.com/apigee-labs/rapier/blob/master/util/test/spec-hub.yaml) 
shows an example of how this case can be handled in Rapier. Here is the [corresponding generated OpenAPI document](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-spec-hub.yaml).
The SpecHub API includes some 'internal' URL tamplates that are used in the implementation but are not part of the API. The Rapier OpenAPI generator supports a -i command-line option that allows the implementation
view of the API to be generated instead of the client view. It can be found [here](https://github.com/apigee-labs/rapier/blob/master/util/test/gen_openapispec/openapispec-spec-hub-with-impl.yaml).

## <a name="navigating"></a>Navigating the Repository

- js - a directory containing a Node package that is used by the generated Javascript SDK
- py - a directory containing a Python module that is used by the generated Python SDK
- test-servers - a directory contains some simple servers used to test the genenrated SDKs
- util - directory containing the sdk generators and the OpenAPI generator. This directory is a Python module
  - gen_openapispec.py - the OpenAPI generator
  - gen_js_sdk.py - the Javascript SDK genenrator
  - gen_py_sdk.py - the Python SDK genenrator
  - requirements.txt - the pip file with the python dependencies for these generators
  - test - a directory containing tests for the generators. This directory contains numerous samples.
    - gen_openapispec - a directory containing openapispec files generated from the samples
    - gen_js_sdk - a directory containing Javascript sdk files generated from the samples
    - gen_js_sdk - a directory containing Python sdk files generated from the samples

## <a name="specification"></a>The Rapier Language Spec

### Schema

All properties are optional unless otherwise specified.

#### <a name="rapier"></a>Rapier

Field Name | Type | Description
---|:---:|---
id | `string` | The URI of the API. Note this is the URI of the API itself, not the Rapier document that describes it, nor the run-time URL at which an implementation of the API can be found. Can be any URI, although the use of URL fragments is popular for obvious reasons. The most common value is '#' - maybe we should make this the default.
title | `string` | The title of the API. Dublin Core title. The default is 'untitled'
version | `string` | The version of the API. The default is 'initial'
entities | [Entities](#entities) | The entities of the API.
consumes | `sequence` of [Media Type](media_type) | The media-types that may be used by clients when providing data in POST and PUT requests. The valid values for the Content-Type HTTP header in those requests. May also be specified as a single string, which is interpreted as a space-delimited list. This value can be overridden at a relationship level
produces | `sequence` of [Media Type](media_type) | The media-types that clients can request from the server in GET, POST, PUT, PATCH and DELETE requests. The valid values for the Accept HTTP header in those requests. May also be specified as a single string, which is interpreted as a space-delimited list. This value can be overridden at a relationship level
conventions | [Conventions](#conventions) | Conventions that affect the details of the HTTP messages of the API
securityDefinitions | [Security Definitions Object](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#securityDefinitionsObject) | From the OpenAPI specification
security | [Security Requirement Object](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#securityRequirementObject) | From the OpenAPI specification

#### <a name="conventions"></a>Conventions

Field Name | Type | Description
---|:---:|---
selector_location | `string` | Either the string "path-segment" or "path-parameter". The default is "path-parameter". This controls whether the selector for a multi-valued relationship appears in a separate path segment of the URL, or as a path parameter in the same path segment as the relationship name.
patch_consumes | `string` | The media type used for PATCH requests. Default is `['application/merge-patch+json']`
error_reponse | `schema` | the schema of the response for all error cases. the default is `{}`

#### <a name="entities"></a>Entities

The set of entities defines the API.

Field Pattern | Type | Description
---|:---:|---
{entity name} | [Entity](#entity) | The name of an entity. Provides the default value of the id of the entity. That is, if the entity does not have an explicit id value, it can be addressed using the URI fragment `#{entity name}`. For more infomation on this, see the [Rapier data model decription](https://github.com/apigee-labs/rapier/blob/master/data_model.md)

#### <a name="entity"></a>Entity

Each entity is a [JSON Schema](http://json-schema.org/). It includes the standard JSON Schema properties (e.g. `properties`) as well as some Rapier-specific ones.

Field Name | Type | Description
---|:---:|---
id | `string` | The URI of the entity. Can be any URI, although the use of URL fragments is popular for obvious reasons. The default value is a URL fragment composed from the entity name which is the YAML key of the entity. If the Entity has an explicit id value, it can be addressed using that URI. If it does not have an explicit id value, it can be addressed using the URI fragment `#{entity name}`. For more infomation on this, see the [Rapier data model decription](https://github.com/apigee-labs/rapier/blob/master/data_model.md)
query_paths | `string` or `sequence of [Query Path](#query_path)` | If the value is a string, it is interpreted as a space-deliminated list of `query paths`.
well_known_URLs | `string` or `sequence of URLs` | Well-known URLs at which a resource of this entity type can be found. If the value is a string, it is interpreted as a space-deliminated list of URLs. If the value is an sequence, each item is interpreted as a single URL. URLs must be path-absolute - i.e. they must begin with a single '/'.
properties | [Properties](#properties) | The properties of the entity. This is the standard JSON Schema `properties` property, with some Rapier extensions.
readOnly | `boolean` | Indicates that resources of this Entity type can be read (GET, HEAD and OPTIONS methods are supported), but not written (PATCH, PUT and DELETE are not allowed). Exceptionally, this property name is in camelCase rather than snake_case to align with the JSON Schema property of the same name.
consumes | `string` or `sequence of string` | Overrides the global value fo consumes for this entity. Specifies the media types clients may provide to create or update the entity with POST, PUT (for string entities). If the value is a string, it must be a space-delimited list of media types
produces | `string` or `sequence of string` | Overrides the global value fo produces for this entity. Specifies the media types clients may request to GET the entity. If the value is a string, it must be a space-delimited list of media types
query_parameters | `sequence` of [Query Parameter](#query_parameter)s

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

Describes a relationship to one or more other entities

Field Name | Type | Description
---|:---:|---
entities | `string` or `sequence of URLs` | A set of URLs of the entities this relationship may reference. If the value is a string, it is interpreted as a space-deliminated list of URLs. If the value is an sequence, each item is interpreted as a single URL.
multiplicity | `string` | The multiplicity of the relationship. The value is of the form x:y or just y. If the value of y is `n`, or a number greater than 1, then the relationship is multi-valued. If x is missing, it is presumed to be 0.
collection_resource | `url` | May only be set if the relationship is multi-valued. Its value is the URL of a JSON Schema for the 'collection-like' resource that represents the multi-valued relationship. The 'collection-like' resource should include, at a minimum, the URLs of the entities in the relationship.
readOnly | `true or false` | For multi-valued relationships, says whether a POST is valid. default is `false`

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
- `siblings;name={name}/siblings` - traverse the siblings relationship, select a specific sibling, and then traverse their siblings.  URL template is \{`child-URL`\}/siblings;name=\{name\}/siblings}  

Multiple query paths may be included in the same string as a space-deliminated list.

#### <a name="query_parameter"></a>Query Parameter

A Query parameter that may be appended to the URL of an entity to identify an entity that is closely related to the entity identified by the URL.
A common use is to restrict the fields returned. 

Field Name | Type | Description
---|:---:|---
name | `string` | The name
description | `string` | The description
required | `true or false` | The default is `false`
type | "string", "number", "integer", "boolean", or "array" | Required. The type of the parameter. Since the parameter is not located at the request body, it is limited to simple types (that is, not an object).
items | [Items Object](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#itemsObject) | Required if the value of type is "array". From the OpenAPI spec
collectionFormat | `string` | From OpenAPI Spec. Determines the format of the array if type array is used. Possible values are: <ul><li>`csv` - comma separated values `foo,bar`. <li>`ssv` - space separated values `foo%20bar`. <li>`tsv` - tab separated values `foo\tbar`. <li>`pipes` - pipe separated values <code>foo&#124;bar</code>. </ul> Default value is `csv`.

#### <a name="media_type"></a>Media Type

Describes a media type. If a media type is given as a simple string, it applies to all entity types. If the media type is given as a JSON structure, you can say which entity types use it

Field pattern | Type | Description
---|:---:|---
{entity_id} | `sequence` of `string`s | the media types to be used with the associated entity. The list of media types may be given as an sequence or a space-deliminated list in a single string

## <a name="oas_generator">OpenAPI Generator

