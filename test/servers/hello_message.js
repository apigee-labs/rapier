'use strict';

var express = require('express');
var app = express();
var bodyParser = require('body-parser');
var modcount = 0;

var PORT = 3000;
var HOST = 'localhost';
var MESSAGE_URL = 'http://' + HOST + ':' + PORT + '/message';
var message = {
  _self: MESSAGE_URL,
  kind: 'HelloMessage',
  text: 'Hello, world'
}

app.use(bodyParser.json()); // for parsing application/json

app.get('/message', function(req, res) {
  var accept_type = req.get('Accept');
  if (typeof accept_type == 'undefined' || accept_type === '*/*'|| accept_type === 'application/json') {
    res.set('ETag', modcount.toString());
    res.set('Content-Type', 'application/json');
    res.set('Content-Location', MESSAGE_URL)
    res.json(message);
  } else {
    res.status(406).send('Unrecognized accept header media type: ' + accept_type)
  }
});

app.patch('/message', function(req, res) {
  var content_type = req.get('Content-Type');
  if (content_type === 'application/json') {
    var accept_type = req.get('Accept');
    if (typeof accept_type == 'undefined' || accept_type === '*/*'|| accept_type === 'application/json') {
      for (var attrname in req.body) { message[attrname] = req.body[attrname]; }
      modcount +=1;
      res.set('ETag', modcount.toString());
      res.set('Content-Type', 'application/json');
      res.set('Content-Location', MESSAGE_URL)
      res.json(message);
    } else {
      res.status(406).send('Unrecognized accept header media type: ' + accept_type)
    }
  } else {
      res.status(406).send('Unrecognized content-type media type: ' + content_type)    
  }
});

app.delete('/message', function(req, res) {
  res.status(405);
  var error_msg = 'cannot delete well-known resource: /message';
  var accept_type = req.get('Accept');
  if (typeof accept_type == 'undefined' || accept_type === '*/*'|| accept_type === 'application/json') {
    res.json({text: error_msg});
  } else {
    res.send(error_msg)
  }
})

console.log('Listening on %d', PORT);
app.listen(PORT);
