"""
The parser:
1. gets and expression
2. parses it
3. handles all boolean logic
4. delegates operator parsing to the OperatorMap

SchemaFreeOperatorMap

  supports all mongo operators for all fields.

SchemaAwareOperatorMap

  1. verifies fields exist.
  2. verifies operators are applied to fields of correct type.


currently unsupported:
1. $where
2. geospatial
"""
import ast
from datetime import datetime
def parse_date(string):
    try:
        return datetime.strptime(string, "%Y-%m-%d %H:%M:%S,%f")
    except ValueError:
        try:
            return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.strptime(string, "%Y-%m-%d")

class AstHandler(object):
    def get_options(self):
        return None
    
    def resolve(self, thing):
        thing_name = thing.__class__.__name__
        try:
            handler = getattr(self, 'handle_' + thing_name)
        except AttributeError:
            raise ParseError('Unsupported syntax ({})'.format(thing_name),
                             col_offset=thing.col_offset,
                             options=self.get_options())
        return handler

    def handle(self, thing):
        return self.resolve(thing)(thing)
        
class ParseError(Exception):
    def __init__(self, message, col_offset, options=[]):
        super(ParseError, self).__init__(message)
        self.col_offset = col_offset
        self.options = options
        
class Parser(AstHandler):
    def __init__(self, operator_map):
        self._operator_map = operator_map

    def get_options(self):
        return self._operand_map.get_options()
        
    def parse(self, string):
        ex = ast.parse(string, mode='eval')
        return self.handle(ex.body)

    def handle_BoolOp(self, op):
        return {self.handle(op.op): map(self.handle, op.values)}

    def handle_And(self, op):
        return '$and'

    def handle_Or(self, op):
        return '$or'

    def handle_UnaryOp(self, op):
        return {self.handle(op.op): self.handle(op.operand)}

    def handle_Not(self, not_node):
        return '$not'
        
    def handle_Compare(self, compare):
        if len(compare.comparators) != 1:
            raise ParseError('Invalid number of comparators: {}',
                             col_offset=compare.comparators[1].col_offset)
        return self._operator_map.handle(left=compare.left,
                                         operator=compare.ops[0],
                                         right=compare.comparators[0])

class SchemaFreeParser(Parser):
    def __init__(self):
        super(SchemaFreeParser, self).__init__(SchemaFreeOperatorMap())
        
class FieldName(AstHandler):
    def __init__(self, fields=None):
        self._fields = fields

    def get_options(self):
        return self._fields
        
    def handle_Name(self, name):
        if self._fields is not None and name.id not in self._fields:
            raise ParseError('Field not found: {}'.format(name.id),
                             col_offset=name.col_offset,
                             options=self.get_options())
        return name.id
            
    def handle_Attribute(self, attr):
        return '{}.{}'.format(self.handle(attr.value), attr.attr)

class OperatorMap(object):
    def get_options(self):
        raise None

    def handle(self, operator, left, right):
        raise NotImplementedError()

class SchemaFreeOperatorMap(OperatorMap):
    def __init__(self):
        self._field_handler = FieldName()
        self._field_type = GenericField()

    def handle(self, operator, left, right):
        field = self._field_handler.handle(left)
        return {field: self._field_type.handle_operator_and_right(operator, right)}

#---Function-Handlers---#
        
class Func(object):

    def parse_arg(self, node, index, field, default=None):
        if index > len(node.args) - 1:
            if default is None:
                raise ParseError('Missing argument in {}'.format(node.func.id),
                                 col_offset=node.col_offset)
            else:
                return default
        return field.handle(node.args[index])
    
    def get_options(self):
        return [f.replace('handle_', '') for f in dir(self) if f.startswith('handle_')]
    
    def handle(self, node):
        try:
            handler = getattr(self, 'handle_' + node.func.id)
        except AttributeError:
            raise ParseError('Unsupported function ({})'.format(node.func.id),
                             col_offset=node.col_offset,
                             options=self.get_options())
        return handler(node)
    
    def handle_exists(self, node):
        return {'$exists':  self.parse_arg(node, 0, BoolField())}

    def handle_type(self, node):
        return {'$type':  self.parse_arg(node, 0, IntField())}

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

class GenericFunc(StringFunc, IntFunc, ListFunc):

    def handle_date(self, node):
        return parse_date(self.parse_arg(node, 0, StringField()))

#---Field-Types---#

class Field(AstHandler):
    def handle_operator_and_right(self, operator, right):
        return self.resolve(operator)(right)
    def handle_In(self, right):
        return {'$in': map(self.handle, right.elts)}

class AlgebricField(Field):
    def handle_Eq(self, right):
        return self.handle(right)
    def handle_Gt(self, right):
        return {'$gt': self.handle(right)}
    def handle_Lt(self,right):
        return {'$lt': self.handle(right)}
    def handle_GtE(self, right):
        return {'$gte': self.handle(right)}
    def handle_LtE(self, right):
        return {'$lte': self.handle(right)}

class StringField(AlgebricField):
    def handle_Str(self, node):
        return node.s
    def handle_Call(self, node):
        return StringFunc().handle(node)

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
        
class ListField(Field):
    def handle_List(self, node):
        return [PrimitiveField().handle(element) for element in node.elts]
    def handle_Call(self, node):
        return ListFunc().handle(node)

class DictField(Field):
    def handle_Dict(self, node):
        return {StringField().handle(key): PrimitiveField().handle(value)
                for key, value in zip(node.keys, node.values)}

class DateTimeField(Field):
    def handle_Str(self, node):
        return parse_date(node.s)

class GenericField(IntField, BoolField, StringField, ListField, DictField):
    def handle_Call(self, node):
        return GenericFunc().handle(node)
