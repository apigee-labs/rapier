'use strict'

var async = require('async')
var todoListAPI = require('./todoListAPI')
var api = todoListAPI.api

function test_objects() {
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
