'use strict'

var todoListAPI = require('./todoListAPI')
var api = todoListAPI.api

function test_objects() {
    api.retrieve('http://localhost:3001/to-dos', function(error, todoList) {
        if (error) throw error;
        if (!(todoList instanceof todoListAPI.TodoList)) throw 'assert';
        todoList.retrieve('items', function(error, items) {
            if (error) throw error;
            if (!(items instanceof todoListAPI.Collection)) throw 'assert';
            var new_item = new todoListAPI.Item({'description':'buy milk'});
            items.create(new_item, function(error) {
                if (error) throw error;
                if (!(new_item._self)) throw 'assert';
                todoList.retrieve('items', function(error, items) {
                    if (error) throw error;
                    if (!(new_item._self in items.items)) throw 'assert';
                    new_item.description = 'buy more milk'
                    new_item.due = 'tonight'
                    new_item.update(function(error) {
                        if (error) throw error;
                        new_item.refresh(function(error) {   
                            if (error) throw error;
                            if (!(new_item.description == 'buy more milk')) throw 'assert';                   
                            new_item.delete(function(error) {
                                if (error) throw error;
                                items.refresh(function(error) {
                                    if (error) throw error;
                                    if (new_item._self in items.items) throw 'assert';                   
                                })
                            })
                        })
                    })
                })
            })
        }) 
    })
}

test_objects()

function test_api() {
    api.retrieve('http://localhost:3001/to-dos', function(error, todoList) {
        if (error) throw error;
        if (!(todoList instanceof todoListAPI.TodoList)) throw 'assert';
        if (!('items' in todoList)) throw 'assert';
        api.retrieve('http://localhost:3001/to-dos/items', function(error, entity) {
            if (error) throw error;
            if (!(entity instanceof todoListAPI.Collection)) throw 'assert';
            api.create('http://localhost:3001/to-dos/items', {kind: 'Item', description:'buy milk'}, function(error, entity) {
                if (error) throw JSON.stringify(error);
                if (!(entity._self)) throw 'assert';
                if (!(entity._etag)) throw 'assert';
                var new_item = entity;
                api.retrieve('http://localhost:3001/to-dos/items', function(error, entity) {
                    if (error) throw JSON.stringify(error);
                    if (!(new_item._self in entity.items)) throw 'assert';
                    var changes = {description: 'buy more milk', due: 'tonight'};
                    api.update(new_item._location, new_item._etag, changes, function(error, entity) {
                        if (error) throw error;
                        api.retrieve(new_item._location, function(error, entity) {   
                            if (error) throw error;
                            if (!(entity.description == 'buy more milk')) throw 'assert';                   
                            if (!(entity.due == 'tonight')) throw 'assert';                   
                            api.delete(new_item._location, function(error, entity) {
                                if (error) throw error;
                                api.retrieve('http://localhost:3001/to-dos/items', function(error, entity) {
                                    if (error) throw error;
                                    if (new_item._self in entity.items) throw 'assert';                   
                                })
                            })
                        })
                    })
                })
            })
        }) 
    })    
}

test_api()
