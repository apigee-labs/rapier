Welcome to Rapier - REST APIs from Entities and Relationships.

The goals of Rapier are to allow REST APIs to be specified with 10x less effort than with other APIs specification languages, and to
produce specifications that describe much higher quality REST APIs. (Following Fred Brooks, we take consistency as being the primary measure of
quality of an API.)

Rapier takes a data-oriented approach to API design, consistent with the model of REST and the world-wide-web. If your mental model of
an API is network of HTTP resources identified and located using URLs, you should be confortable with Rapier. If your model of a web API
consists of 'end-points' with 'parameters' (i.e. a more traditional service-oriented model), you may find the Rapier approach does not 
fit with your mental model.

You define an API with Rapier by specifying in YAML the entities and relationships that describe the resources of the API. The details of the API's 
HTTP messages are deduced from this specification using the standard patterns described in the HTTP standard specifications, plus a few conventions 
that we have added. In the future we will allow more options for these conventions - for now they are mostly fixed.

Here is a 'Hello-world' example in Rapier:

    info:
        title: Hello message
        version: "0.1"
    entities:
        Hello_message:
            well_known_URLs: /message
            properties:
                text:
                    type: string
                    
The API defined by this Rapier specification exposes a single resource whose type is `Hello-message` at the URL `/message`. This Entity has a single declared property called `text`.
The API implied by this specification does not allow this resource to be deleted, because it is well-known, but it does allow it to be
retrieved using GET and modified using PATCH. This is an example of the 'conventions' we mentioned. Rapier also assumes that a GET response
includes an ETag header that must be echoed in the 'If-Match' request header of the PATCH. Rapier also assumes that the server will add
a few standard properties to the `Hello-message` entity. The `Hello-message` at `/message` will actually look like this:

    {'selfLink': 'http://example.org/message',
     'type': 'Hello_message',
     'message': 'Hello world'
    }
 
Rapier provides a tool - gen-swagger.py - that will generate a Swagger document that will spell out the conventions used by Rapier for this API.
Swagger cannot describe everything that is important in the API, but it is a good start. Once you have seen a few examples of the Swagger to
understand the conventions, you will stop looking at the Swagger, whose details are repetitive and will become quickly obvious. However, the Swagger
documents may continue to be useful for integrating your API specification with tools that are Swagger-based. \[Swagger is also useful for
documenting APIs that are less consistent than Rapier APIs, or which follow a service-oriented rather than a data-oriented design patern.\] If
you would like to see the Swagger generated for this sample, [look here:](https://revision.aeip.apigee.net/mnally/rapier/raw/master/test/swagger-hello-message.yaml).
As you can see, our 9 lines of Rapier produced around 120 lines of Swagger - a good ratio. The Swagger is also more complex - we used both
JSON Refs and YAML anchors and aliases to try to avoid repetition.

Traditionally, the next example after 'Hello world' is 'To-do List':

    info:
        title: To-do List
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
                
This API defines a single resource at the URL `to-dos` whose type is `To_do_list`. In the relationships section, you can see that `To_do_list` has a property
called `items` that represents a multi-valued relationship to the items of the list. The value of the `items` property with be a URL that points to a Collection
resource that contains information on each item of the `To_do_list`. The `To_do_list` at `/to-dos` will actually look like this:

    {'selfLink': 'http://example.org/message',
     'type': 'To_do_list',
     'items': 'http://example.org/xxxxx'
    }
    
The Collection at `http://example.org/to-dos` will look like this:

    {'selfLink': 'http://example.org/xxxxx',
     'type': 'Collection',
     'contents_type': 'Item',
     'contents': [{
         'selfLink': 'http://example.org/items/yyyyy',
         'id': 'yyyyy',
         'type': 'Item'
         'description': 'Get milk on the way home',
         'due': '1439228983'
         }
      ]
    }
 
 The API does not specify what `xxxx` will look like, but we know from the `query_paths` property of the API specification that `http://example.org/to-dos/items` 
 is a valid URL with the same meaning as `http://example.org/xxxxx`, so it would not be surprising if `xxxxx` was in fact `to-dos/items`.
 
 You can POST items to `http://example.org/to-dos/items` to create new items, you can PATCH items to change them, and you can DELETE itesm to remove them.
 
 If you want to see the genenrated Swagger document for this API specification, [it is here](https://revision.aeip.apigee.net/mnally/rapier/raw/master/test/swagger-to-do-list.yaml)