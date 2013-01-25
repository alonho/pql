from datetime import datetime
from unittest import TestCase
from mql import SchemaFreeParser, ParseError

class MqlTestCase(TestCase):

    def setUp(self):
        self.parser = SchemaFreeParser()

    def test_equal_int(self):
        self.assertEqual(self.parser.parse('a == 1'), {'a': 1})

    def test_equal_string(self):
        self.assertEqual(self.parser.parse('a == "foo"'), {'a': 'foo'})

    def test_nested(self):
        self.assertEqual(self.parser.parse('a.b == 1'), {'a.b': 1})
        
    def test_and(self):
        self.assertEqual(self.parser.parse('a == 1 and b == 2'),
                         {'$and': [{'a': 1}, {'b': 2}]})

    def test_or(self):
        self.assertEqual(self.parser.parse('a == 1 or b == 2'),
                         {'$or': [{'a': 1}, {'b': 2}]})

    def test_not(self):
        self.assertEqual(self.parser.parse('not a == 1'), {'$not': {'a': 1}})

    def test_algebra(self):
        for string, expected in [('a > 1', {'a': {'$gt': 1}}),
                                 ('a >= 1', {'a': {'$gte': 1}}),
                                 ('a < 1', {'a': {'$lt': 1}}),
                                 ('a <= 1', {'a': {'$lte': 1}})]:
            self.assertEqual(self.parser.parse(string), expected)

    def test_bool(self):
        self.assertEqual(self.parser.parse('a == True'), {'a': True})
        self.assertEqual(self.parser.parse('a == False'), {'a': False})

    def test_list(self):
        self.assertEqual(self.parser.parse('a == [1, 2, 3]'), {'a': [1, 2, 3]})

    def test_dict(self):
        self.assertEqual(self.parser.parse('a == {"foo": 1}'), {'a': {'foo': 1}})

    def test_in(self):
        self.assertEqual(self.parser.parse('a in [1, 2, 3]'), {'a': {'$in': [1, 2, 3]}})

    def test_not_in(self):
        self.assertEqual(self.parser.parse('a not in [1, 2, 3]'), {'a': {'$nin': [1, 2, 3]}})

    def test_missing_func(self):
        with self.assertRaises(ParseError) as context:
            self.parser.parse('a == foo()')
        self.assertIn('Unsupported function', str(context.exception))

    def test_exists(self):
        self.assertEqual(self.parser.parse('a == exists(True)'), {'a': {'$exists': True}})

    def test_type(self):
        self.assertEqual(self.parser.parse('a == type(3)'), {'a': {'$type': 3}})

    def test_regex(self):
        self.assertEqual(self.parser.parse('a == regex("foo")'), {'a': {'$regex': 'foo'}})
        self.assertEqual(self.parser.parse('a == regex("foo", "i")'),
                         {'a': {'$regex': 'foo', '$options': 'i'}})

    def test_mod(self):
        self.assertEqual(self.parser.parse('a == mod(10, 3)'), {'a': {'$mod': [10, 3]}})

    def test_size(self):
        self.assertEqual(self.parser.parse('a == size(4)'), {'a': {'$size': 4}})

    def test_all(self):
        self.assertEqual(self.parser.parse('a == all([1, 2, 3])'), {'a': {'$all': [1, 2, 3]}})
    def test_match(self):
        self.assertEqual(self.parser.parse('a == match({"foo": "bar"})'),
                         {'a': {'$elemMatch': {'foo': 'bar'}}})

    def test_date(self):
        self.assertEqual(self.parser.parse('a == date("2012-3-4")'),
                         {'a': datetime(2012, 3, 4)})
        self.assertEqual(self.parser.parse('a == date("2012-3-4 12:34:56,123")'),
                         {'a': datetime(2012, 3, 4, 12, 34, 56, 123000)})
