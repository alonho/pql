from datetime import datetime
from unittest import TestCase
import pql

class BasePqlTestCase(TestCase):

    def compare(self, string, expected):
        #print string, '|', expected
        self.assertEqual(self.parser.parse(string), expected)
        
class PqlSchemaLessTestCase(BasePqlTestCase):

    def setUp(self):
        self.parser = pql.SchemaFreeParser()
        
    def test_equal_int(self):
        self.compare('a == 1', {'a': 1})

    def test_equal_string(self):
        self.compare('a == "foo"', {'a': 'foo'})

    def test_nested(self):
        self.compare('a.b == 1', {'a.b': 1})
        
    def test_and(self):
        self.compare('a == 1 and b == 2', {'$and': [{'a': 1}, {'b': 2}]})

    def test_or(self):
        self.compare('a == 1 or b == 2', {'$or': [{'a': 1}, {'b': 2}]})

    def test_not(self):
        self.compare('not a == 1', {'$not': {'a': 1}})

    def test_algebra(self):
        for string, expected in [('a > 1', {'a': {'$gt': 1}}),
                                 ('a >= 1', {'a': {'$gte': 1}}),
                                 ('a < 1', {'a': {'$lt': 1}}),
                                 ('a <= 1', {'a': {'$lte': 1}})]:
            self.compare(string, expected)

    def test_bool(self):
        self.compare('a == True', {'a': True})
        self.compare('a == False', {'a': False})

    def test_list(self):
        self.compare('a == [1, 2, 3]', {'a': [1, 2, 3]})

    def test_dict(self):
        self.compare('a == {"foo": 1}', {'a': {'foo': 1}})

    def test_in(self):
        self.compare('a in [1, 2, 3]', {'a': {'$in': [1, 2, 3]}})

    def test_not_in(self):
        self.compare('a not in [1, 2, 3]', {'a': {'$nin': [1, 2, 3]}})

    def test_missing_func(self):
        with self.assertRaises(pql.ParseError) as context:
            self.parser.parse('a == foo()')
        self.assertIn('Unsupported function', str(context.exception))

    def test_exists(self):
        self.compare('a == exists(True)', {'a': {'$exists': True}})

    def test_type(self):
        self.compare('a == type(3)', {'a': {'$type': 3}})

    def test_regex(self):
        self.compare('a == regex("foo")', {'a': {'$regex': 'foo'}})
        self.compare('a == regex("foo", "i")', {'a': {'$regex': 'foo', '$options': 'i'}})

    def test_mod(self):
        self.compare('a == mod(10, 3)', {'a': {'$mod': [10, 3]}})

    def test_size(self):
        self.compare('a == size(4)', {'a': {'$size': 4}})

    def test_all(self):
        self.compare('a == all([1, 2, 3])', {'a': {'$all': [1, 2, 3]}})
    def test_match(self):
        self.compare('a == match({"foo": "bar"})', {'a': {'$elemMatch': {'foo': 'bar'}}})

    def test_date(self):
        self.compare('a == date("2012-3-4")', {'a': datetime(2012, 3, 4)})
        self.compare('a == date("2012-3-4 12:34:56,123")',
                     {'a': datetime(2012, 3, 4, 12, 34, 56, 123000)})

class PqlSchemaAwareTestCase(BasePqlTestCase):

    def setUp(self):
        self.parser = pql.SchemaAwareParser({'a': pql.IntField(),
                                             'd': pql.DateTimeField(),
                                             'foo.bar': pql.ListField(pql.StringField())})

    def test_sanity(self):
        self.compare('a == 3', {'a': 3})

    def test_invalid_field(self):
        with self.assertRaises(pql.ParseError) as context:
            self.parser.parse('b == 3')
        self.assertEqual(sorted(context.exception.options),
                         sorted(['a', 'd', 'foo.bar']))

    def test_type_error(self):
        with self.assertRaises(pql.ParseError):
            self.parser.parse('a == "foo"')

    def test_invalid_function(self):
        with self.assertRaises(pql.ParseError) as context:
            self.parser.parse('a == size(3)')
        self.assertIn('Unsupported function', str(context.exception))

    def test_invalid_date(self):
        with self.assertRaises(pql.ParseError) as context:
            self.parser.parse('d == "foo"')
        self.assertIn('Unexpected date format', str(context.exception))

    def test_date(self):
        self.compare('d > "2012-03-02"',
                     {'d': {'$gt': datetime(2012, 3, 2)}})

    def test_nested(self):
        self.compare('foo.bar == ["spam"]', {'foo.bar': ['spam']})
        self.compare('foo.bar == "spam"', {'foo.bar': 'spam'})