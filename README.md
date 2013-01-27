===
MQL
===

Usage
=====

Schema-Free Example
-------------------

The schema-free parser converts python expressions to mongodb queries with no schema enforcment.
This parser fits most use cases.

	>>> import mql
	>>> parser = mql.SchemaFreeParser()
	>>> parser.parse("a > 1 and b == 'foo' or not c.d == False")
	{'$or': [{'$and': [{'a': {'$gt': 1}}, {'b': 'foo'}]}, {'$not': {'c.d': False}}]}

Schema-Aware Example
--------------------

The schema-aware parser validates fields exist:

	>>> import mql
	>>> parser = mql.SchemaAwareParser({'a': mql.DateTimeField()})
	>>> parser.parse('b == 1') 
	Traceback (most recent call last):
		...
	mql.ParseError: Field not found: b. options: ['a']
	
Validates values are of the correct type:

	>>> parser.parse('a == 1')
	Traceback (most recent call last):
		...
	mql.ParseError: Unsupported syntax (Num).
	
Validates functions are called against the appropriate types:

	>>> parser.parse('a == regex("foo")')
	Traceback (most recent call last):
		...
	mql.ParseError: Unsupported function (regex). options: ['date', 'exists', 'type']

Data Types
----------

mql | mongo
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

Operators
---------

mql | mongo
--- | ---
a > 1 | {'a': {'$gt': 1}}
a >= 1 | {'a': {'$gte': 1}}
a < 1 | {'a': {'$lt': 1}}
a <= 1 | {'a': {'$lte': 1}}
a in [1, 2, 3] | {'a': {'$in': [1, 2, 3]}}
a not in [1, 2, 3] | {'a': {'$nin': [1, 2, 3]}}

Boolean Logic
-------------

mql | mongo
--- | ---
not a == 1 | {'$not': {'a': 1}}
a == 1 or b == 2 | {'$or': [{'a': 1}, {'b': 2}]}
a == 1 and b == 2 | {'$and': [{'a': 1}, {'b': 2}]}

Functions
---------

mql | mongo
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

1. Generate a schema from a *mongoengine*/*mongokit* class.
2. Add support for geospatial queries.
3. Add support for $where.
