from unittest import TestCase
from pql.parser import parse

class TestParser(TestCase):

    def test_equals_and_hyphenated(self):
        self.assertEqual(parse('field-name == 1'), {'field-name': 1})

    def test_not_equals(self):
        self.assertEqual(parse('field != 1'), {'field': {'$ne': 1}})

    def test_or(self):
        self.assertEqual(parse('field == 1 or field == 2'),
                         {'$or': [{'field': 1}, {'field': 2}]})

    def test_not(self):
        self.assertEqual(parse('not field == 1'),
                         {'$not': {'field': 1}})

    def test_str(self):
        self.assertEqual(parse("field == null"), {'field': None})

    def test_bool(self):
        self.assertEqual(parse("field == true"), {'field': True})
        self.assertEqual(parse("field == false"), {'field': False})

    def test_logic_precedence(self):
        '''AND has higher precedence than OR'''
        self.assertEqual(parse('field == 1 or field == 2 and field == 3'),
                         {'$or': [{'field': 1}, {'$and': [{'field': 2}, {'field': 3}]}]})
        self.assertEqual(parse('field == 3 and field == 2 or field == 1'),
                         {'$or': [{'$and': [{'field': 3}, {'field': 2}]}, {'field': 1}]})

        '''NOT has higher precedence than both OR and AND'''
        self.assertEqual(parse('not field == 3 or not field == 2 and not field == 1'),
                         {'$or': [{'$not': {'field': 3}},
                                  {'$and': [{'$not': {'field': 2}},
                                            {'$not': {'field': 1}}]}]})

    def test_parens(self):
        self.assertEqual(parse('(field == 1 or field == 2) and field == 3'),
                         {'$and': [{'$or': [{'field': 1}, {'field': 2}]}, {'field': 3}]})

    def test_in_list(self):
        self.assertEqual(parse('field in ()'),
                         {'field': {'$in': []}})
        self.assertEqual(parse('field in (1)'),
                         {'field': {'$in': [1]}})
        self.assertEqual(parse('field in (1, 2)'),
                         {'field': {'$in': [1, 2]}})
        self.assertEqual(parse('field in (1, 2, 3)'),
                         {'field': {'$in': [1, 2, 3]}})

    def test_between(self):
        self.assertEqual(parse('1 < field < 3'),
                         {'field': {'$gt': 1, '$lt': 3}})
        self.assertEqual(parse('field between 1 and 3'),
                         {'field': {'$gte': 1, '$lte': 3}})

    def test_not_between(self):
        self.assertEqual(parse('field not between 1 and 3'),
                         {'field': {'$lt': 1, '$gt': 3}})

    def test_regexp(self):
        self.assertEqual(parse('field ~ "foo"'),
                         {'field': {'$regex': "foo"}})

    def test_call(self):
        self.assertEqual(parse('time == now()'), {})
        