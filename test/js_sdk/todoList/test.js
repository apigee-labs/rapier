'use strict'

var async = require('async')
var todoListAPI = require('./todoListAPI')
var api = todoListAPI.api

function test_objects() {
    async.waterfall([
        function(callback) {
            api.retrieve('http://localhost:3001/to-dos', function(error, todoList) {
                if (error) throw error;
                if (!(todoList instanceof todoListAPI.TodoList)) throw 'expected type TodoList';
                callback(null, todoList)
            })
        },
        function(todoList, callback) {
            todoList.retrieve('items', function(error, items) {
                if (error) throw error;
                if (!(items instanceof todoListAPI.Collection)) throw 'expected type Collection';
                callback(null, todoList, items)
            })
        },
        function(todoList, items, w_callback) {
            var new_item = new todoListAPI.Item({'description':'buy milk'});
            async.series([
                function (callback) {
                    items.create(new_item, function(error) {
                        if (error) throw error;
                        if (!(new_item._self)) throw 'created item has no _self value';
                        callback(null, 'created item')
                    })
                },
                function(callback) {
                    todoList.retrieve('items', function(error, items) {
                        if (error) throw error;
                        if (!(new_item._self in items.items)) throw 'new item not in items array';
                        callback(null, 'verified item in list')
                    })
                },
                function(callback) {
                    new_item.description = 'buy more milk';
                    new_item.due = 'tonight';
                    new_item.update(function(error) {
                        if (error) throw error;
                        callback(null, 'updated item');
                    })
                },
                function(callback) {
                    new_item.refresh(function(error) {   
                        if (error) throw error;
                        if (!(new_item.description == 'buy more milk')) throw 'assert';
                        callback(null, 'verified update');
                    })
                },
                function(callback) {
                    new_item.delete(function(error) {
                        if (error) throw error;
                        callback(null, 'deleted new item');
                    })
                },
                function (callback) {
                    items.refresh(function(error) {
                        if (error) throw error;
                        if (new_item._self in items.items) throw 'assert';
                        callback(null, 'created item')
                    })
                }
            ])
        }
    ])
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
