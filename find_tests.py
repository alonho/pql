from datetime import datetime
from unittest import TestCase
import bson
import pql

class BasePqlTestCase(TestCase):

    def compare(self, string, expected):
        print("{} | {}".format(string,expected))
        self.assertEqual(pql.find(string), expected)

class PqlSchemaLessTestCase(BasePqlTestCase):

    def test_hyphenated(self):
        self.compare('"foo-bar" == "spam"', {'foo-bar': 'spam'})

    def test_equal_int(self):
        self.compare('a == 1', {'a': 1})

    def test_not_equal_string(self):
        self.compare('a != "foo"', {'a': {'$ne': 'foo'}})

    def test_nested(self):
        self.compare('a.b == 1', {'a.b': 1})

    def test_and(self):
        self.compare('a == 1 and b == 2', {'$and': [{'a': 1}, {'b': 2}]})

    def test_or(self):
        self.compare('a == 1 or b == 2', {'$or': [{'a': 1}, {'b': 2}]})

    def test_not(self):
        self.compare('not a > 1', {'a': {'$not': {'$gt': 1}}})

    def test_algebra(self):
        for string, expected in [('a > 1', {'a': {'$gt': 1}}),
                                 ('a >= 1', {'a': {'$gte': 1}}),
                                 ('a < 1', {'a': {'$lt': 1}}),
                                 ('a <= 1', {'a': {'$lte': 1}})]:
            self.compare(string, expected)

    def test_bool(self):
        self.compare('a == True', {'a': True})
        self.compare('a == False', {'a': False})

    def test_none(self):
        self.compare('a == None', {'a': None})
        self.compare('a == null', {'a': None})

    def test_list(self):
        self.compare('a == [1, 2, 3]', {'a': [1, 2, 3]})

    def test_dict(self):
        self.compare('a == {"foo": 1}', {'a': {'foo': 1}})

    def test_in(self):
        self.compare('a in [1, 2, 3]', {'a': {'$in': [1, 2, 3]}})

        with self.assertRaises(pql.ParseError) as context:
            pql.find('a in (1)')

        self.assertIn('Invalid value type', str(context.exception))

    def test_not_in(self):
        self.compare('a not in [1, 2, 3]', {'a': {'$nin': [1, 2, 3]}})

        with self.assertRaises(pql.ParseError) as context:
            pql.find('a not in (1)')

        self.assertIn('Invalid value type', str(context.exception))

    def test_missing_func(self):
        with self.assertRaises(pql.ParseError) as context:
            pql.find('a == foo()')
        self.assertIn('Unsupported function', str(context.exception))

    def test_invalid_name(self):
        with self.assertRaises(pql.ParseError) as context:
            pql.find('a == foo')
        self.assertIn('Invalid name', str(context.exception))

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
        self.compare('a == date(10)', {'a': datetime.fromtimestamp(10)})
        self.compare('a == date("2012-3-4")', {'a': datetime(2012, 3, 4)})
        self.compare('a == date("2012-3-4 12:34:56.123")',
                     {'a': datetime(2012, 3, 4, 12, 34, 56, 123000)})

    def test_epoch(self):
        self.compare('a == epoch(10)', {'a': 10})
        self.compare('a == epoch("2012/1/1")', {'a': 1325372400.0})

    def test_epoch_utc(self):
        self.compare('a == epoch_utc(10)', {'a': 10})
        self.compare('a == epoch_utc("2012/1/1")', {'a': 1325376000.0})

    def test_id(self):
        self.compare('_id == id("abcdeabcdeabcdeabcdeabcd")',
                     {'_id': bson.ObjectId("abcdeabcdeabcdeabcdeabcd")})

    def test_near_legacy_coordinates(self):
        self.compare('location == near([1, 2], 10)',
                     {'location':
                      {'$near': [1,2],
                       '$maxDistance': 10}})

    def test_near_sphere_point(self):
        self.compare('location == nearSphere(Point(1, 2))',
                     {'location':
                      {'$nearSphere':
                       {'$geometry':
                        {'type': 'Point',
                         'coordinates': [1, 2]}}}})

    def test_near_point_with_max(self):
        self.compare('location == near(Point(1, 2), 10)',
                     {'location':
                      {'$near':
                       {'$geometry':
                        {'type': 'Point',
                         'coordinates': [1, 2]},
                        '$maxDistance': 10}}})

    def test_geo_within_polygon(self):
        polygon = [[1, 2], [3, 4], [5, 6]]
        self.compare('location == geoWithin(Polygon([{}, {}]))'.format(polygon, polygon),
                     {'location':
                      {'$geoWithin':
                       {'$geometry':
                        {'type': 'Polygon',
                         'coordinates': [polygon, polygon]}}}})

    def test_geo_intersects_line_string(self):
        self.compare('location == geoIntersects(LineString([[1, 2], [3, 4]]))',
                     {'location':
                      {'$geoIntersects':
                       {'$geometry':
                        {'type': 'LineString',
                         'coordinates': [[1, 2], [3, 4]]}}}})

    def test_center_within(self):
        for center_type in ['center', 'centerSphere']:
            self.compare('location == geoWithin({}([1, 2], 3))'.format(center_type),
                         {'location':
                          {'$geoWithin':
                           {'$' + center_type: [[1, 2], 3]}}})

    def test_polygon_and_box(self):
        for shape in ['box', 'polygon']:
            self.compare('location == geoWithin({}([[1, 2], [3, 4], [5, 6]]))'.format(shape),
                         {'location':
                          {'$geoWithin':
                           {'$' + shape: [[1, 2], [3, 4], [5, 6]]}}})

class PqlSchemaAwareTestCase(BasePqlTestCase):

    def compare(self, string, expected):
        print("{} | {}".format(string,expected))
        self.assertEqual(pql.find(string, schema={'a': pql.IntField(),
                                                  'd': pql.DateTimeField(),
                                                  'foo.bar': pql.ListField(pql.StringField())}), expected)

    def test_sanity(self):
        self.compare('a == 3', {'a': 3})

    def test_invalid_field(self):
        with self.assertRaises(pql.ParseError) as context:
            self.compare('b == 3', None)
        self.assertEqual(sorted(context.exception.options),
                         sorted(['a', 'd', 'foo.bar']))

    def test_type_error(self):
        with self.assertRaises(pql.ParseError):
            self.compare('a == "foo"', None)

    def test_invalid_function(self):
        with self.assertRaises(pql.ParseError) as context:
            self.compare('a == size(3)', None)
        self.assertIn('Unsupported function', str(context.exception))

    def test_invalid_date(self):
        with self.assertRaises(pql.ParseError) as context:
            self.compare('d == "foo"', None)
        self.assertIn('Error parsing date', str(context.exception))

    def test_date(self):
        self.compare('d > "2012-03-02"',
                     {'d': {'$gt': datetime(2012, 3, 2)}})

    def test_nested(self):
        self.compare('foo.bar == ["spam"]', {'foo.bar': ['spam']})
        #self.compare('foo.bar == "spam"', {'foo.bar': 'spam'}) # currently broken
