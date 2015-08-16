'use strict';

var express = require('express');
var app = express();
var modcount = 0;

var PORT = 3000;
var HOST = 'localhost';
var MESSAGE_URL = 'http://' + HOST + ':' + PORT + '/message';
var message = {
  self: MESSAGE_URL,
  type: 'HelloMessage',
  text: 'Hello, world'
}

app.get('/message', function(req, res) {
  var accept_type = req.get('Accept')
  if (typeof accept_type == 'undefined' || accept_type === '*/*'|| accept_type === 'application/json') {
    res.set('ETag', modcount.toString());
    res.set('Content-Type', 'application/json');
    res.set('Content-Location', MESSAGE_URL)
    res.json(message);
  } else {
    res.status(406).send('Unrecognized accept header media type: ' + accept_type)
  }
});

console.log('Listening on %d', PORT);
app.listen(PORT);
