"""
The parser:
1. gets and expression
2. parses it
3. handles all boolean logic
4. delegates operator and rvalue parsing to the OperatorMap

SchemaFreeOperatorMap

  supports all mongo operators for all fields.

SchemaAwareOperatorMap

  1. verifies fields exist.
  2. verifies operators are applied to fields of correct type.

currently unsupported:
1. $where - kind of intentionally against injections
2. geospatial
"""
import ast
import bson
from datetime import datetime
FULL_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S,%f'
DATE_AND_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMATS = [FULL_DATETIME_FORMAT,
                    DATE_AND_TIME_FORMAT,
                    DATE_FORMAT]
def parse_date(node):
    string = node.s
    for datetime_format in DATETIME_FORMATS:
        try:
            return datetime.strptime(string, datetime_format)
        except ValueError:
            pass
    raise ParseError('Unexpected date format.',
                     col_offset=node.col_offset,
                     options=DATETIME_FORMATS)

class AstHandler(object):

    def get_options(self):
        return [f.replace('handle_', '') for f in dir(self) if f.startswith('handle_')]
    
    def resolve(self, thing):
        thing_name = thing.__class__.__name__
        try:
            handler = getattr(self, 'handle_' + thing_name)
        except AttributeError:
            raise ParseError('Unsupported syntax ({0}).'.format(thing_name,
                                                              self.get_options()),
                             col_offset=thing.col_offset if hasattr(thing, 'col_offset') else None,
                             options=self.get_options())
        return handler

    def handle(self, thing):
        return self.resolve(thing)(thing)
        
class ParseError(Exception):
    def __init__(self, message, col_offset, options=[]):
        super(ParseError, self).__init__(message)
        self.message = message
        self.col_offset = col_offset
        self.options = options
    def __str__(self):
        if self.options:
            return '{0} options: {1}'.format(self.message, self.options)
        return self.message
        
class Parser(AstHandler):
    def __init__(self, operator_map):
        self._operator_map = operator_map

    def get_options(self):
        return self._operator_map.get_options()
        
    def parse(self, string):
        ex = ast.parse(string, mode='eval')
        return self.handle(ex.body)

    def handle_BoolOp(self, op):
        return {self.handle(op.op): list(map(self.handle, op.values))}

    def handle_And(self, op):
        '''and'''
        return '$and'

    def handle_Or(self, op):
        '''or'''
        return '$or'

    def handle_UnaryOp(self, op):
        operator = self.handle(op.operand)
        if not isinstance(operator, dict):
            raise ParseError("Cannot use 'not' on a value, requires an expression")
        elif len(operator) > 1:
            raise ParseError("Invalid expression used in conjunction with 'not'")
        return {operator.keys()[0]: {self.handle(op.op): operator.values()[0]}}

    def handle_Not(self, not_node):
        '''not'''
        return '$not'
        
    def handle_Compare(self, compare):
        if len(compare.comparators) != 1:
            raise ParseError('Invalid number of comparators: {0}',
                             col_offset=compare.comparators[1].col_offset)
        return self._operator_map.handle(left=compare.left,
                                         operator=compare.ops[0],
                                         right=compare.comparators[0])

class SchemaFreeParser(Parser):
    def __init__(self):
        super(SchemaFreeParser, self).__init__(SchemaFreeOperatorMap())

class SchemaAwareParser(Parser):
    def __init__(self, *a, **k):
        super(SchemaAwareParser, self).__init__(SchemaAwareOperatorMap(*a, **k))

class FieldName(AstHandler):        
    def handle_Name(self, name):
        return name.id
    def handle_Attribute(self, attr):
        return '{0}.{1}'.format(self.handle(attr.value), attr.attr)

class OperatorMap(object):
    def resolve_field(self, node):
        return FieldName().handle(node)
    def handle(self, operator, left, right):
        field = self.resolve_field(left)
        return {field: self.resolve_type(field).handle_operator_and_right(operator, right)}

class SchemaFreeOperatorMap(OperatorMap):
    def get_options(self):
        return None
    def resolve_type(self, field):
        return GenericField()

class SchemaAwareOperatorMap(OperatorMap):
    def __init__(self, field_to_type):
        self._field_to_type = field_to_type
    def resolve_field(self, node):
        field = super(SchemaAwareOperatorMap, self).resolve_field(node)
        if field not in self._field_to_type:
            raise ParseError('Field not found: {0}.'.format(field),
                             col_offset=node.col_offset,
                             options=self._field_to_type.keys())
        return field

    def resolve_type(self, field):
        return self._field_to_type[field]
        
#---Function-Handlers---#
        
class Func(AstHandler):

    def get_arg(self, node, index):
        if index > len(node.args) - 1:
            raise ParseError('Missing argument in {0}.'.format(node.func.id),
                             col_offset=node.col_offset)
        return node.args[index]
    
    def parse_arg(self, node, index, field):
        return field.handle(self.get_arg(node, index))
        
    def handle(self, node):
        try:
            handler = getattr(self, 'handle_' + node.func.id)
        except AttributeError:
            raise ParseError('Unsupported function ({0}).'.format(node.func.id),
                             col_offset=node.col_offset,
                             options=self.get_options())
        return handler(node)
    
    def handle_exists(self, node):
        return {'$exists': self.parse_arg(node, 0, BoolField())}

    def handle_type(self, node):
        return {'$type': self.parse_arg(node, 0, IntField())}

class StringFunc(Func):
    def handle_regex(self, node):
        result = {'$regex': self.parse_arg(node, 0, StringField())}
        try:
            result['$options'] = self.parse_arg(node, 1, StringField())
        except ParseError:
            pass
        return result

class IntFunc(Func):
    def handle_mod(self, node):
        return {'$mod': [self.parse_arg(node, 0, IntField()),
                         self.parse_arg(node, 1, IntField())]}
        
class ListFunc(Func):
    def handle_size(self, node):
        return {'$size': self.parse_arg(node, 0, IntField())}

    def handle_all(self, node):
        return {'$all': self.parse_arg(node, 0, ListField())}

    def handle_match(self, node):
        return {'$elemMatch': self.parse_arg(node, 0, DictField())}

class DateTimeFunc(Func):
    def handle_date(self, node):
        return parse_date(self.get_arg(node, 0))

class IdFunc(Func):
    def handle_id(self, node):
        return self.parse_arg(node, 0, IdField())

class GenericFunc(StringFunc, IntFunc, ListFunc, DateTimeFunc, IdFunc):
    pass

#---Operators---#

class Operator(AstHandler):
    def __init__(self, field):
        self.field = field
    def handle_Eq(self, node):
        '''=='''
        return self.field.handle(node)
    def handle_NotEq(self, node):
        '''!='''
        return {'$ne': self.field.handle(node)}
    def handle_In(self, node):
        '''in''' 
        return {'$in': list(map(self.field.handle, node.elts))}
    def handle_NotIn(self, node):
        '''not in'''
        return {'$nin': list(map(self.field.handle, node.elts))}
    
class AlgebricOperator(Operator):
    def handle_Gt(self, node):
        '''>'''
        return {'$gt': self.field.handle(node)}
    def handle_Lt(self,node):
        '''<'''
        return {'$lt': self.field.handle(node)}
    def handle_GtE(self, node):
        '''>='''
        return {'$gte': self.field.handle(node)}
    def handle_LtE(self, node):
        '''<='''
        return {'$lte': self.field.handle(node)}

#---Field-Types---#

class Field(AstHandler):
    OP_CLASS = Operator
    def handle_operator_and_right(self, operator, right):
        return self.OP_CLASS(self).resolve(operator)(right)

class AlgebricField(Field):
    OP_CLASS = AlgebricOperator

class StringField(AlgebricField):
    def handle_Call(self, node):
        return StringFunc().handle(node)
    def handle_Str(self, node):
        return node.s

class IntField(AlgebricField):
    def handle_Num(self, node):
        return node.n
    def handle_Call(self, node):
        return IntFunc().handle(node)
        
class BoolField(Field):
    def handle_Name(self, node):
        flag = node.id
        assert flag in ['False', 'True']
        return flag == 'True'

class PrimitiveField(StringField, IntField, BoolField):
    pass
        
class _ListField(Field):
    def __init__(self, field=PrimitiveField()):
        self._field = field
    def handle_List(self, node):
        return list(map(self._field.handle, node.elts))
    def handle_Call(self, node):
        return ListFunc().handle(node)
def ListField(field=PrimitiveField()):
    class ListField(_ListField, field.__class__):
        pass
    return ListField(field)

class DictField(Field):
    def __init__(self, field=PrimitiveField()):
        self._field = field
    def handle_Dict(self, node):
        return dict((StringField().handle(key), self._field.handle(value))
                    for key, value in zip(node.keys, node.values))

class DateTimeField(AlgebricField):
    def handle_Str(self, node):
        return parse_date(node)
    def handle_Call(self, node):
        return DateTimeFunc().handle(node)

class IdField(AlgebricField):
    def handle_Str(self, node):
        return bson.ObjectId(node.s)
    def handle_Call(self, node):
        return IdFunc().handle(node)

class GenericField(IntField, BoolField, StringField, _ListField, DictField):
    def handle_Call(self, node):
        return GenericFunc().handle(node)
