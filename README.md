# Welcome to Rapier - REST APIs from Entities and Relationships.

## Introduction

The goals of Rapier are to allow REST APIs to be specified with one tenth the effort required with other APIs specification languages, and to
produce specifications that describe higher quality APIs. \[1\]

Rapier takes a data-oriented approach to API design, which fits the model of REST and the world-wide-web. If your mental model of
a web API is network of HTTP resources identified and located using URLs, you should be confortable with Rapier. If your model of a web API
consists of 'end-points' with 'parameters' (i.e. a more traditional service-oriented model), you may find the Rapier approach does not 
fit with your mental model. The data-oriented style and the service-oriented styles have equivalent expressiveness but they look different and require you to think differently.

You specify an API with Rapier by specifying, in YAML, the entities and relationships that describe the resources of the API. The details of the API's 
HTTP messages are deduced from this specification using the standard patterns described in the HTTP standard specifications, plus a few conventions 
that we have added. In the future we will allow more options for these add-on conventions - for now they are mostly fixed.

Rapier is for specifying new APIs. You will not be able to describe existing APIs with Rapier unless that API used the same conventions that Rapier does
and was absolutely consistent in applying them.

Today, Rapier provides only a language for API specifications and a tool for generating Swagger docments from them. In the future we intend to work on test tools,
SDK generators and server implementation frameworks.  

## Examples

Rapier is very easy to understand and learn. The easiest way is by example.

### Hello World

Here is a 'Hello-world' example in Rapier:

    info:
        title: Hello World API
        version: "0.1"
    entities:
        Hello_message:
            well_known_URLs: /message
            properties:
                text:
                    type: string
                    
The API defined by this Rapier specification exposes a single resource whose type is `Hello_message` at the URL `/message`. This resource has a single declared property called `text`.
The API does not allow this resource to be deleted, because it is well-known, but it does allow it to be
retrieved using GET and modified using PATCH. This is an example of the 'conventions' we mentioned. Rapier also assumes that a GET response
includes an ETag header that must be echoed in the 'If-Match' request header of the PATCH. In Rapier APIs, the server will add
a few standard properties to the `Hello-message` entity. The `Hello-message` at `/message` will actually look like this:

    {'self_link': 'http://example.org/message',
     'id': '1234567',
     'type': 'Hello_message',
     'message': 'Hello, world'
    }
 
Rapier provides a tool — gen-swagger.py — that will generate a Swagger document that will spell out the conventions used by Rapier for this API.
Swagger cannot describe everything that is important in the API, but it is a good tool. Once you have seen a few examples of the Swagger, you will
understand the conventions and you will stop looking at the Swagger, whose details are repetitive and will become quickly obvious. The Swagger
documents may continue to be useful for integrating your API specification with tools that are Swagger-based. Swagger is also useful for
documenting APIs that are less consistent than Rapier APIs, follow different conventions to the ones Rapier currently understands, or which follow a service-oriented rather than a data-oriented design patern. 
The Swagger generated for the 9-line Rapier sample above can be [found here](https://revision.aeip.apigee.net/mnally/rapier/raw/master/test/swagger-hello-message.yaml). It contains around 120 lines, which illustrates the efficiency of Rapier. 
The Swagger is also more complex - we used both JSON Refs and YAML anchors and aliases to try to avoid repetition, otherwise the Swagger would have been even longer.

### To-do List

Traditionally, the next example after 'Hello world' is 'To-do List':

    info:
        title: To-do List API
        version: "0.1"
    entities:
        To_do_list:
            well_known_URLs: /to-dos
            query_paths: [items]
        Item:
            properties:
                description:
                    type: string
                due_date:
                    type: date
    relationships:
        list-to-items:
            one_end:
                entity: To_do_list
                property: items
                multiplicity: 0:n
            other_end:
                entity: Item
                
This API defines a single resource at the URL `/to-dos` whose type is `To_do_list`. In the relationships section, you can see that each `To_do_list` has a property
called `items` that represents a multi-valued relationship to the `Items` of the list. The value of the `items` property will be a URL that points to a Collection
resource that contains information on each item of the `To_do_list`. In JSON, the `To_do_list` at `/to-dos` will actually look like this:

    {'self_link': 'http://example.org/to-dos',
     'id': '987655443',
     'type': 'To_do_list',
     'items': 'http://example.org/xxxxx'
    }
    
In JSON, the Collection at `http://example.org/xxxxx` will look like this:

    {'self_link': 'http://example.org/xxxxx',
     'type': 'Collection',
     'id': '5647382',
     'contents_type': 'Item',
     'contents': [{
         'self_link': 'http://example.org/items/yyyyy',
         'id': 'yyyyy',
         'type': 'Item'
         'description': 'Get milk on the way home',
         'due': '1439228983'
         }
      ]
    }
 
 The API does not specify what the string `xxxxx` will look like, but we know from the `query_paths` property of the `To_do_list` entity specification that `http://example.org/to-dos/items` 
 is a valid URL with the same meaning as `http://example.org/xxxxx`. We know it has the same meaning, because `items` as a query_path means 'follow the items relationship'. 
 It would not be surprising if `xxxxx` was in fact `to-dos/items`, but the API does not require this and 
 the server gets to decide what `xxxxx` looks like. Note that in order for the `query_path` called `items` to be valid, `items` has to be one of the declared properties of the 
 resource appearing in the relationships section.
 
 You can POST items to `http://example.org/to-dos/items` (and also `http://example.org/xxxxx` if that URL is different) to create new items, you can PATCH items to change them, 
 and you can DELETE items to remove them. You can also perform a GET on `http://example.org/items/yyyyy`, which will yield:
 
    {
     'self_link': 'http://example.org/items/yyyyy',
     'id': 'yyyyy',
     'type': 'Item'
     'description': 'Get milk on the way home',
     'due': '1439228983'
    }
 
 URLs matching the URL template `http://example.org/todos/items/{Item_id}` are also supported by the API. Whenever a `query_path` contains a segment that corresponds to a multi-valued relationship,
 the API will support an extra segment that is used to select a particular resource from the multi-valued collection. (An option allows the selector value to be in a path parameter instead of 
 a path segment - see the 'Property Tracker' example). 
 
 If you want to see the generated Swagger document for this API specification, [it is here](https://revision.aeip.apigee.net/mnally/rapier/raw/master/test/swagger-to-do-list.yaml)
 
### Dog Tracker
 
Another popular API example is the 'Dog Tracker' example. In Rapier, it looks lke this:
 
    info:
        title: Dog-tracker API
        version: "0.1"
    conventions:
        selector_location: path-parameter
    entities:
        Dog_tracker:
            well_known_URLs: /dog-tracker
            query_paths: [dogs, people, dogs/owner, people/dogs]
        Dog:
            properties:
                name:
                    type: string
                birth_date:
                    type: string
                fur_color:
                    type: string
        Person:
            properties:
                name:
                    type: string
                birth-date:
                    type: string
    relationships:
        tracker-to-dogs:
            one_end:
                entity: Dog_tracker
                property: dogs
                multiplicity: 0:n
            other_end:
                entity: Dog
        tracker-to-people:
            one_end:
                entity: Dog_tracker
                property: people
                multiplicity: 0:n
            other_end:
                entity: Person
        dogs-to-people:
            one_end:
                entity: Person
                property: dogs
                multiplicity: 0:n
            other_end:
                entity: Dog
                property: owner
                multiplicity: 0:1
                
This API defines a single resource at the URL `/dog-tracker` whose type is `Dog_tracker`. In the relationships section, you can see that each `Dog_tracker` has properties
called `dogs` and `people` that point to the Dogs and Persons that are tracked. The value of each of these will be a URL that points to a Collection
resource that contains information on each Dog or Property. You can POST to either of these Collections to create new \[resources for\] Dogs or Persons. From the `well_known_URLs` and `query_paths` 
properties of `Dog-tracker` we know that these Collections can also be accessed at `/dog-tracker/dogs` and `/dog-tracker/people` respectively.

The API also defines a relationship between Dogs and Persons, which is called owner on one side and dogs on the other. The `owner` property is settable on each Dog - this is in fact
the only way to change which Person owns a Dog. When a Dog is created by POSTing to `/dog-tracker/dogs`, the `owner` property may be set. If a Dog is POSTed to the `dogs` Collection of a specific
Person, the server will set the `owner` property appropriately.

If you want to see the generated Swagger document for this API specification, [it is here](https://revision.aeip.apigee.net/mnally/rapier/raw/master/test/swagger-dog-tracker.yaml)

### Property Tracker

Our last example shows a more complex set of relationships. In this example, a Dog can be owned by a Person or an Institution and People and Institutions can own Bicycles as well as Dogs.
The [source for this example is here](https://revision.aeip.apigee.net/mnally/rapier/raw/master/test/property-tracker.yaml). 
This example strains the expressive power of Swagger - for completeness we include a generated [Swagger document here](https://revision.aeip.apigee.net/mnally/rapier/raw/master/test/swagger-property-tracker.yaml).


\[1\] Following Fred Brooks, we take consistency as being the primary measure of
quality of an API. “Blaauw and I believe that consistency underlies all principles. A good architecture is consistent in the sense that, given a partial knowledge of the system, one can predict the remainder”
