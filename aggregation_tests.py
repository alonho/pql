from unittest import TestCase
from bson import SON
import pymongo
import pql

class PqlAggregationTest(TestCase):

    def compare(self, expression, expected):
        self.assertEqual(pql.AggregationParser().parse(expression), expected)

class PqlAggregationPipesTest(PqlAggregationTest):

    def test_match(self):
        self.assertEqual(pql.match('a == 1'), [{'$match': {'a': 1}}])
    
    def test_group(self):
        for group_func in pql.AggregationGroupParser.GROUP_FUNCTIONS:
            self.assertEqual(pql.group(_id='foo', total=group_func + '(bar)'),
                             [{'$group': {'_id': '$foo', 'total': {'$' + group_func: '$bar'}}}])

    def test_invalid_group(self):
        with self.assertRaises(pql.ParseError):
            pql.group(_id='foo', total='bar(1)')
        with self.assertRaises(pql.ParseError):
            pql.group(_id='foo', total='min(1, 2)')

    def test_project(self):
        self.assertEqual(pql.project(foo='bar', a='b + c'),
                         [{'$project': {'foo': '$bar', 'a': {'$add': ['$b', '$c']}}}])

    def test_skip(self):
        self.assertEqual(pql.skip(3), [{'$skip': 3}])

    def test_limit(self):
        self.assertEqual(pql.limit(2), [{'$limit': 2}])

    def test_unwind(self):
        self.assertEqual(pql.unwind('foo'), [{'$unwind': '$foo'}])

    def test_sort(self):
        self.assertEqual(pql.sort('a'), [{'$sort': SON([('a', pymongo.ASCENDING)])}])
        self.assertEqual(pql.sort(['a', '-b', '+c']),
                         [{'$sort': SON([('a', pymongo.ASCENDING),
                                         ('b', pymongo.DESCENDING),
                                         ('c', pymongo.ASCENDING)])}])

class PqlAggregationDataTypesTest(PqlAggregationTest):

    def test_bool(self):
        self.compare('True', True)
        self.compare('true', True)
        self.compare('False', False)
        self.compare('false', False)
        self.compare('None', None)
        self.compare('null', None)

class PqlAggregationSimpleProjectionTest(PqlAggregationTest):

    def test(self):
        self.compare('a', '$a')

    def test_nested(self):
        self.compare('a.b.c', '$a.b.c')

class PqlAggregationLogicTest(PqlAggregationTest):

    def test_and(self):
        self.compare('a and b', {'$and': ['$a', '$b']})

    def test_or(self):
        self.compare('a or b', {'$or': ['$a', '$b']})

    def test_not(self):
        self.compare('not a', {'$not': '$a'})

class PqlAggregationBoolTest(PqlAggregationTest):

    def test_cmp(self):
        self.compare('cmp(a, "bar")', {'$cmp': ['$a', 'bar']})

    def test_eq(self):
        self.compare('a == 0', {'$eq': ['$a', 0]})

    def test_gt(self):
        self.compare('a > 0', {'$gt': ['$a', 0]})

    def test_gte(self):
        self.compare('a >= 0', {'$gte': ['$a', 0]})

    def test_lt(self):
        self.compare('a < 0', {'$lt': ['$a', 0]})

    def test_lte(self):
        self.compare('a <= 0', {'$lte': ['$a', 0]})

    def test_ne(self):
        self.compare('a != 0', {'$ne': ['$a', 0]})

class PqlAggregationArithmicTest(PqlAggregationTest):
    
    def test_add(self):
        self.compare('a + 1', {'$add': ['$a', 1]})
        
    def test_divide(self):
        self.compare('a / 1', {'$divide': ['$a', 1]})

    def test_mod(self):
        self.compare('a % 1', {'$mod': ['$a', 1]})

    def test_multiply(self):
        self.compare('a * 1', {'$multiply': ['$a', 1]})

    def test_subtract(self):
        self.compare('a - 1', {'$subtract': ['$a', 1]})

class PqlAggregationStringTest(PqlAggregationTest):

    def test_concat(self):
        self.compare('concat("foo", "bar", b)', {'$concat': ['foo', 'bar', '$b']})

    def test_strcasecmp(self):
        self.compare('strcasecmp("foo", b)', {'$strcasecmp': ['foo', '$b']})

    def test_substr(self):
        self.compare('substr("foo", 1, 2)', {'$substr': ['foo', 1, 2]})

    def test_toLower(self):
        self.compare('toLower(a)', {'$toLower': ['$a']})

    def test_toUpper(self):
        self.compare('toUpper(a)', {'$toUpper': ['$a']})

class PqlAggregationDateTest(PqlAggregationTest):
    def test(self):
        for func in ['dayOfYear', 'dayOfMonth', 'dayOfWeek',
                     'year', 'month', 'week',
                     'hour', 'minute', 'second', 'millisecond']:
            self.compare('{0}(a)'.format(func), {'${0}'.format(func): ['$a']})

class PqlConditionTest(PqlAggregationTest):
    def test_if(self):
        self.compare('a if b > 3 else c', {'$cond': [{'$gt': ['$b', 3]}, '$a', '$c']})

    def test_if_null(self):
        self.compare('ifnull(a + b, 100)', {'$ifnull': [{'$add': ['$a', '$b']}, 100]})
    
class PqlAggregationSanityTest(PqlAggregationTest):
    def test(self):
        self.compare('a + b / c - 3 * 4 == 1',
                     {'$eq': [
                         {'$subtract': [{'$add': ['$a', {'$divide': ['$b', '$c']}]},
                                        {'$multiply': [3, 4]}]},
                         1]})

class PqlAggregationErrorsTest(PqlAggregationTest):
    def test_invalid_num_args(self):
        with self.assertRaises(pql.ParseError):
            self.compare('ifnull(1)', None)
        with self.assertRaises(pql.ParseError):
            self.compare('ifnull()', None)

    def test_invalid_func(self):
        with self.assertRaises(pql.ParseError):
            self.compare('foo(10)', None)

    def test_invalid_comparators(self):
        with self.assertRaises(pql.ParseError):
            self.compare('1 < a < 3', None)
