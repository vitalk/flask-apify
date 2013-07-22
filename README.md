Flask-Apify
===========

The Flask extension to create an API to your application as a ninja.

Quickstart
----------

```python
from itertools import count

from flask import Flask, request
from flask.ext.apify import Apify
from flask.ext.apify.exc import ApiNotFound


app = Flask(__name__)
apify = Apify(url_prefix='/api/v1')
apify = apify.init_app(app)

mytodos = {}
next_todo_id = count().next


def abort_if_todo_doesnot_exists(todo_id):
    if todo_id not in mytodos:
        raise ApiNotFound('Todo does not exists')


@apify.route('/todos', methods=('GET',))
def todos():
    '''Returns all todos.'''
    return mytodos


@apify.route('/todos', methods=('POST',))
def addtodo():
    '''Create new todo.'''
    todo_id = next_todo_id()
    mytodos[todo_id] = request.form['todo']
    return {todo_id: mytodos[todo_id]}, 201


@apify.route('/todos/<int:todo_id>', methods=('DELETE',))
def rmtodo(todo_id):
    '''Remove todo.'''
    abort_if_todo_doesnot_exists(todo_id)
    del mytodos[todo_id]
    return None, 204


@apify.route('/todos/<int:todo_id>', methods=('GET',))
def todo(todo_id):
    abort_if_todo_doesnot_exists(todo_id)
    return {todo_id: mytodos[todo_id]}


# important to register all added routes to application
apify.register_routes()


if __name__ == '__main__':
    app.run(debug=True)
```

Usage example
-------------

Save the example above somewhere, for example to `apify.py` and launch it.

```sh
$ python apify.py
 * Running on http://127.0.0.1:5000/
 * Restarting with reloader
```

Then test it in your command prompt.

Add a new todo:

```sh
$ curl -i http://localhost:5000/api/v1/todos -X POST \
-H "Accept: application/json" \
-d "todo=Write documentation"

HTTP/1.0 201 CREATED
Content-Type: application/json

{"0": "Write documentation"}
```

```sh
$ curl -i http://localhost:5000/api/v1/todos -X POST \
-H "Accept: application/json" \
-d "todo=Publish to Github"

HTTP/1.0 201 CREATED
Content-Type: application/json

{"1": "Publish to Github"}
```

Get a todo list:

```sh
$ curl -i http://localhost:5000/api/v1/todos \
-H "Accept: application/json"

HTTP/1.0 200 OK
Content-Type: application/json

{"0": "Write documentation", "1": "Publish to Github"}
```

Get a single todo:

```sh
$ curl -i http://localhost:5000/api/v1/todos/1 \
-H "Accept: application/json"

HTTP/1.0 200 OK
Content-Type: application/json

{"1": "Publish to Github"}
```

Delete a todo:

```sh
$ curl -i http://localhost:5000/api/v1/todos/1 -X DELETE \
-H "Accept: application/json"

HTTP/1.0 204 NO CONTENT
Content-Type: application/json
```

Error example:

```sh
$ curl -i http://localhost:5000/api/v1/todos/1 \
-H "Accept: application/json"

HTTP/1.0 404 NOT FOUND
Content-Type: application/json

{"error": "Not Found", "message": "Todo does not exists"}
```
