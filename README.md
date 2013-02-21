===
PQL
===

PQL stands for Python-Query-Language. PQL translates python expressions to **MongoDB** queries.

PQL uses the builtin python **ast** module for parsing and analysis of python expressions.

PQL is resilient to code injections as it doesn't evaluate the code.

Installation
============

	pip install pql
	
Follow **@alonhorev** on **twitter** for updates.
Source located at: http://github.com/alonho/pql

Usage
=====

Schema-Free Example
-------------------

The schema-free parser converts python expressions to mongodb queries with no schema enforcment:

	>>> import pql
	>>> parser = pql.SchemaFreeParser()
	>>> parser.parse("a > 1 and b == 'foo' or not c.d == False")
	{'$or': [{'$and': [{'a': {'$gt': 1}}, {'b': 'foo'}]}, {'$not': {'c.d': False}}]}

Schema-Aware Example
--------------------

The schema-aware parser validates fields exist:

	>>> import pql
	>>> parser = pql.SchemaAwareParser({'a': pql.DateTimeField()})
	>>> parser.parse('b == 1') 
	Traceback (most recent call last):
		...
	pql.ParseError: Field not found: b. options: ['a']
	
Validates values are of the correct type:

	>>> parser.parse('a == 1')
	Traceback (most recent call last):
		...
	pql.ParseError: Unsupported syntax (Num).
	
Validates functions are called against the appropriate types:

	>>> parser.parse('a == regex("foo")')
	Traceback (most recent call last):
		...
	pql.ParseError: Unsupported function (regex). options: ['date', 'exists', 'type']
	
Data Types
----------

pql | mongo
--- | ---
a == 1 | {'a': 1}
a == "foo" | {'a': 'foo'}
a == True | {'a': True}
a == False | {'a': False}
a == [1, 2, 3] | {'a': [1, 2, 3]}
a == {"foo": 1} | {'a': {'foo': 1}}
a == date("2012-3-4") | {'a': datetime.datetime(2012, 3, 4, 0, 0)}
a == date("2012-3-4 12:34:56") | {'a': datetime.datetime(2012, 3, 4, 12, 34, 56)}
a == date("2012-3-4 12:34:56,123") | {'a': datetime.datetime(2012, 3, 4, 12, 34, 56, 123000)}
id == id("abcdeabcdeabcdeabcdeabcd") | {'id': bson.ObjectId("abcdeabcdeabcdeabcdeabcd")}

Operators
---------

pql | mongo
--- | ---
a > 1 | {'a': {'$gt': 1}}
a >= 1 | {'a': {'$gte': 1}}
a < 1 | {'a': {'$lt': 1}}
a <= 1 | {'a': {'$lte': 1}}
a in [1, 2, 3] | {'a': {'$in': [1, 2, 3]}}
a not in [1, 2, 3] | {'a': {'$nin': [1, 2, 3]}}

Boolean Logic
-------------

pql | mongo
--- | ---
not a == 1 | {'$not': {'a': 1}}
a == 1 or b == 2 | {'$or': [{'a': 1}, {'b': 2}]}
a == 1 and b == 2 | {'$and': [{'a': 1}, {'b': 2}]}

Functions
---------

pql | mongo
--- | ---
a == all([1, 2, 3]) | {'a': {'$all': [1, 2, 3]}}
a == exists(True) | {'a': {'$exists': True}}
a == match({"foo": "bar"}) | {'a': {'$elemMatch': {'foo': 'bar'}}}
a == mod(10, 3) | {'a': {'$mod': [10, 3]}}
a == regex("foo") | {'a': {'$regex': 'foo'}}
a == regex("foo", "i") | {'a': {'$options': 'i', '$regex': 'foo'}}
a == size(4) | {'a': {'$size': 4}}
a == type(3) | {'a': {'$type': 3}}

TODO
====

1. Generate a schema from a *mongoengine* or *mongokit* class.
2. Add a declarative schema generation syntax.
3. Add support for geospatial queries.
4. Add support for $where.
