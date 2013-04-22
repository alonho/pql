from tests import BasePqlTestCase
from pql import ParseError
from pql.aggregation import AggregationParser

class PqlAggregationTest(BasePqlTestCase):
    
    def setUp(self):
        self.parser = AggregationParser()

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
        self.compare('toLower(a)', {'$toLower': '$a'})

    def test_toUpper(self):
        self.compare('toUpper(a)', {'$toUpper': '$a'})

class PqlAggregationDateTest(PqlAggregationTest):
    def test(self):
        for func in ['dayOfYear', 'dayOfMonth', 'dayOfWeek',
                     'year', 'month', 'week',
                     'hour', 'minute', 'second', 'millisecond']:
            self.compare('{}(a)'.format(func), {'${}'.format(func): '$a'})

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
        self.parser.parse('ifnull(1, 2)')
        with self.assertRaises(ParseError):
            self.parser.parse('ifnull(1)')
        with self.assertRaises(ParseError):
            self.parser.parse('ifnull()')

    def test_invalid_func(self):
        with self.assertRaises(ParseError):
            self.parser.parse('foo(10)')

    def test_invalid_comparators(self):
        with self.assertRaises(ParseError):
            self.parser.parse('1 < a < 3')