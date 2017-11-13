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

Find Queries
============

Schema-Free Example
-------------------

The schema-free parser converts python expressions to mongodb queries with no schema enforcement:

	>>> import pql
	>>> pql.find("a > 1 and b == 'foo' or not c.d == False")
	{'$or': [{'$and': [{'a': {'$gt': 1}}, {'b': 'foo'}]}, {'$not': {'c.d': False}}]}

Schema-Aware Example
--------------------

The schema-aware parser validates fields exist:

	>>> import pql
	>>> pql.find('b == 1', schema={'a': pql.DateTimeField()}) 
	Traceback (most recent call last):
		...
	pql.ParseError: Field not found: b. options: ['a']
	
Validates values are of the correct type:

	>>> pql.find('a == 1', schema={'a': pql.DateTimeField()})
	Traceback (most recent call last):
		...
	pql.ParseError: Unsupported syntax (Num).
	
Validates functions are called against the appropriate types:

	>>> pql.find('a == regex("foo")', schema={'a': pql.DateTimeField()})
	Traceback (most recent call last):
		...
	pql.ParseError: Unsupported function (regex). options: ['date', 'exists', 'type']

Referencing Fields
------------------

pql | mongo
--- | -----
a | a
a.b.c | a.b.c
"a-b" | a-b
	
Data Types
----------

pql | mongo
--- | -----
a == 1 | {'a': 1}
a == "foo" | {'a': 'foo'}
a == None | {'a': None}
a == True | {'a': True}
a == False | {'a': False}
a == [1, 2, 3] | {'a': [1, 2, 3]}
a == {"foo": 1} | {'a': {'foo': 1}}
a == date("2012-3-4") | {'a': datetime.datetime(2012, 3, 4, 0, 0)}
a == date("2012-3-4 12:34:56") | {'a': datetime.datetime(2012, 3, 4, 12, 34, 56)}
a == date("2012-3-4 12:34:56.123") | {'a': datetime.datetime(2012, 3, 4, 12, 34, 56, 123000)}
id == id("abcdeabcdeabcdeabcdeabcd") | {'id': bson.ObjectId("abcdeabcdeabcdeabcdeabcd")}

Operators
---------

pql | mongo
--- | -----
a != 1 | {'a': {'$ne': 1}}
a > 1 | {'a': {'$gt': 1}}
a >= 1 | {'a': {'$gte': 1}}
a < 1 | {'a': {'$lt': 1}}
a <= 1 | {'a': {'$lte': 1}}
a in [1, 2, 3] | {'a': {'$in': [1, 2, 3]}}
a not in [1, 2, 3] | {'a': {'$nin': [1, 2, 3]}}

Boolean Logic
-------------

pql | mongo
--- | -----
not a == 1 | {'$not': {'a': 1}}
a == 1 or b == 2 | {'$or': [{'a': 1}, {'b': 2}]}
a == 1 and b == 2 | {'$and': [{'a': 1}, {'b': 2}]}

Functions
---------

pql | mongo
--- | -----
a == all([1, 2, 3]) | {'a': {'$all': [1, 2, 3]}}
a == exists(True) | {'a': {'$exists': True}}
a == match({"foo": "bar"}) | {'a': {'$elemMatch': {'foo': 'bar'}}}
a == mod(10, 3) | {'a': {'$mod': [10, 3]}}
a == regex("foo") | {'a': {'$regex': 'foo'}}
a == regex("foo", "i") | {'a': {'$options': 'i', '$regex': 'foo'}}
a == size(4) | {'a': {'$size': 4}}
a == type(3) | {'a': {'$type': 3}}

Geo Queries
-----------

pql | mongo
--- | -----
location == geoWithin(center([1, 2], 3)) | {'location': {'$geoWithin': {'$center': [[1, 2], 3]}}}
location == geoWithin(centerSphere([1, 2], 3)) | {'location': {'$geoWithin': {'$centerSphere': [[1, 2], 3]}}}
location == geoIntersects(LineString([[1, 2], [3, 4]])) | {'location': {'$geoIntersects': {'$geometry': {'type': 'LineString', 'coordinates': [[1, 2], [3, 4]]}}}}
location == geoWithin(Polygon([[[1, 2], [3, 4], [5, 6]], [[1, 2], [3, 4], [5, 6]]])) | {'location': {'$geoWithin': {'$geometry': {'type': 'Polygon', 'coordinates': [[[1, 2], [3, 4], [5, 6]], [[1, 2], [3, 4], [5, 6]]]}}}}
location == near([1, 2], 10) | {'location': {'$maxDistance': 10, '$near': [1, 2]}}
location == near(Point(1, 2), 10) | {'location': {'$near': {'$geometry': {'type': 'Point', 'coordinates': [1, 2]}, '$maxDistance': 10}}}
location == nearSphere(Point(1, 2)) | {'location': {'$nearSphere': {'$geometry': {'type': 'Point', 'coordinates': [1, 2]}}}}
location == geoWithin(box([[1, 2], [3, 4], [5, 6]])) | {'location': {'$geoWithin': {'$box': [[1, 2], [3, 4], [5, 6]]}}}
location == geoWithin(polygon([[1, 2], [3, 4], [5, 6]])) | {'location': {'$geoWithin': {'$polygon': [[1, 2], [3, 4], [5, 6]]}}}

Aggregation Queries
===================

Example
-------

Lets say you have a collection of car listings:

	>>> list(db.cars.find())
    [{'_id': ObjectId('51794ce58c998f1e2b654b50'),
      'made_on': datetime.datetime(1971, 4, 7, 0, 0),
      'model': 'fiat',
      'price': 3},
     {'_id': ObjectId('51794cea8c998f1e2b654b51'),
      'made_on': datetime.datetime(1980, 10, 19, 0, 0),
      'model': 'subaru',
      'price': 5},
     {'_id': ObjectId('51794cf08c998f1e2b654b52'),
      'made_on': datetime.datetime(1983, 2, 27, 0, 0),
      'model': 'kia',
      'price': 4},
     {'_id': ObjectId('51794d3c8c998f1e2b654b53'),
      'made_on': datetime.datetime(1988, 1, 23, 0, 0),
      'model': 'kia',
      'price': 7}]
  
 How do you get the number of cars and the sum of their prices per model per decade:
 
    >>> collection.aggregate(project(model='model', made_on='year(made_on)', price='price * 3.7') | 
    		         match('made_on > 1975 and made_on < 1990') | 
				 group(_id=project(model='model', decade='made_on - (made_on % 10)'), 
						   count='sum(1)', total='sum(price)'))
    {'ok': 1.0,
     'result': [{'_id': {'decade': 1980, 'model': 'subaru'}, 'count': 1,'total': 18.5},
			    {'_id': {'decade': 1980, 'model': 'kia'}, 'count': 2, 'total': 40.7}]}

How would it look using the raw syntax:

    [{'$project': {'made_on': {'$year': '$made_on'},
                   'model': '$model',
                   'price': {'$multiply': ['$price', 3.7]}}},
     {'$match': {'$and': [{'made_on': {'$gt': 1975}},
                          {'made_on': {'$lt': 1990}}]}},
     {'$group': {'_id': {'decade': {'$subtract': ['$made_on',
                                                  {'$mod': ['$made_on', 10]}]},
                         'model': '$model'},
      'count': {'$sum': 1},
      'total': {'$sum': '$price'}}}]

Referencing Fields
------------------

pql | mongo
--- | -----
a | $a
a.b.c | $a.b.c

Arithmetic Operators
--------------------

pql | mongo
--- | -----
a + 1 | {'$add': ['$a', 1]}
a / 1 | {'$divide': ['$a', 1]}
a % 1 | {'$mod': ['$a', 1]}
a * 1 | {'$multiply': ['$a', 1]}
a - 1 | {'$subtract': ['$a', 1]}
a > 0 | {'$gt': ['$a', 0]}
a >= 0 | {'$gte': ['$a', 0]}
a < 0 | {'$lt': ['$a', 0]}
a <= 0 | {'$lte': ['$a', 0]}

Logical Operators
-----------------

pql | mongo
--- | -----
a == 0 | {'$eq': ['$a', 0]}
a != 0 | {'$ne': ['$a', 0]}
cmp(a, "bar") | {'$cmp': ['$a', 'bar']}
a and b | {'$and': ['$a', '$b']}
not a | {'$not': '$a'}
a or b | {'$or': ['$a', '$b']}
a if b > 3 else c | {'$cond': [{'$gt': ['$b', 3]}, '$a', '$c']}
ifnull(a + b, 100) | {'$ifnull': [{'$add': ['$a', '$b']}, 100]}

Date Operators
--------------

pql | mongo
--- | -----
dayOfYear(a) | {'$dayOfYear': '$a'}
dayOfMonth(a) | {'$dayOfMonth': '$a'}
dayOfWeek(a) | {'$dayOfWeek': '$a'}
year(a) | {'$year': '$a'}
month(a) | {'$month': '$a'}
week(a) | {'$week': '$a'}
hour(a) | {'$hour': '$a'}
minute(a) | {'$minute': '$a'}
second(a) | {'$second': '$a'}
millisecond(a) | {'$millisecond': '$a'}

String Operators
----------------

pql | mongo
--- | -----
concat("foo", "bar", b) | {'$concat': ['foo', 'bar', '$b']}
strcasecmp("foo", b) | {'$strcasecmp': ['foo', '$b']}
substr("foo", 1, 2) | {'$substr': ['foo', 1, 2]}
toLower(a) | {'$toLower': '$a'}
toUpper(a) | {'$toUpper': '$a'}

TODO
====

1. Generate a schema from a *mongoengine* or *mongokit* class.
2. Add a declarative schema generation syntax.
3. Add support for $where.

