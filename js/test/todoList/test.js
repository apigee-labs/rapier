'use strict'

var async = require('async')
var todoListAPI = require('./todoListAPI')
var api = todoListAPI.api

function test_objects() {
    api.retrieve('http://localhost:3001/to-dos', function(error, todoList) {
        todoList.retrieve('items', function(error, items) {
            if (error) throw JSON.stringify(error);
            var new_item = new todoListAPI.Item();
            new_item.description = 'buy milk';
            items.create(new_item, function(error) {
                new_item.description = 'buy more milk';
                new_item.due = 'tonight';
                new_item.update(function(error) {
                    new_item.delete(function(error) {
                    })
                })
            })
        }) 
    })
}

test_objects()

function test_api() {
    api.retrieve('http://localhost:3001/to-dos', function(error, todoList) {
        api.retrieve('http://localhost:3001/to-dos/items', function(error, entity) {
            var body = {
                kind: 'Item', 
                description:'buy milk'
                };
            api.create('http://localhost:3001/to-dos/items', body, function(error, entity) {
                var new_item = entity;
                var changes = {
                    description: 'buy more milk', 
                    due: 'tonight'
                    };
                api.update('http://localhost:3001/to-dos/items;' + new_item._id, new_item._etag, changes, function(error, entity) {
                    api.delete('http://localhost:3001/to-dos/items;' + new_item._id, function(error, entity) {
                    })
                })
            })
        }) 
    })    
}

test_api()

function test_objects_with_async() {
    async.waterfall([
        function(callback) {
            api.retrieve('http://localhost:3001/to-dos', function(error, todoList) {
                if (error) 
                    callback(error);
                else if (!(todoList instanceof todoListAPI.TodoList))
                    callback('expected type TodoList');
                else
                    callback(null, todoList)
            })
        },
        function(todoList, callback) {
            todoList.retrieve('items', function(error, items) {
                if (error) 
                    callback(error);
                else if (!(items instanceof todoListAPI.Collection))
                    callback('expected type Collection');
                else
                    callback(null, todoList, items)
            })
        },
        function(todoList, items, w_callback) {
            var new_item = new todoListAPI.Item({'description':'buy milk'});
            async.series([
                function (callback) {
                    items.create(new_item, function(error) {
                        if (error) 
                            callback(error);
                        else if (!(new_item._self))
                            callback('created item has no _self value');
                        else
                            callback(null, 'created item')
                    })
                },
                function(callback) {
                    todoList.retrieve('items', function(error, items) {
                        if (error)  
                            callback(error);
                        else if (!(new_item._self in items.items))
                            callback('new item not in items array');
                        else
                            callback(null, 'verified item in list')
                    })
                },
                function(callback) {
                    new_item.description = 'buy more milk';
                    new_item.due = 'tonight';
                    new_item.update(function(error) {
                        if (error)  
                            callback(error);
                        else
                            callback(null, 'updated item');
                    })
                },
                function(callback) {
                    new_item.refresh(function(error) {   
                        if (error)  
                            callback(error);
                        else if (!(new_item.description == 'buy more milk'))
                            callback('assert');
                        else
                            callback(null, 'verified update');
                    })
                },
                function(callback) {
                    new_item.delete(function(error) {
                        if (error)
                            callback(error);
                        else
                            callback(null, 'deleted new item');
                    })
                },
                function (callback) {
                    items.refresh(function(error) {
                        if (error) 
                            callback(error);
                        else if (new_item._self in items.items)
                            callback('assert');
                        else
                            callback(null, 'created item')
                    })
                }
            ], function(error, results) {
                if (error) {
                    console.log('error', error);
                    w_callback(error)
                } else {
                    console.log(results);
                    w_callback(null, 'successfully created, updated and deleted item')
                }
            })
        }
    ], function(error, result) {
        if (error)
            console.log('error', error);
        else
            console.log(result)
    })
}

test_objects_with_async()