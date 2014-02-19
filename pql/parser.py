from ply import lex, yacc

tokens = [
    'EQUALS',
    'LARGER',
    'SMALLER',
    'LARGER_EQUAL',
    'SMALLER_EQUAL',
    'NOT_EQUAL',
    'NUMBER',
    'FIELD',
    'STRING',
    'BOOL',
    'AND',
    'OR',
    'NOT',
    'NULL',
    'LPAREN',
    'RPAREN',
    'IN',
    'COMMA',
    'BETWEEN',
    'TILDA'
]

t_ignore  = ' \t'

def t_BETWEEN(t):
    r'between'
    return t

def t_TILDA(t):
    '~'
    return t

def t_COMMA(t):
    ','
    return t

def t_LPAREN(t):
    '\('
    return t

def t_RPAREN(t):
    '\)'
    return t
    
def t_NULL(t):
    'null'
    t.value = None
    return t

def t_BOOL(t):
    'false|true'
    t.value = t.value == 'true'
    return t

def t_AND(t):
    'and'
    return t

def t_OR(t):
    'or'
    return t

def t_NOT(t):
    'not'
    return t

def t_IN(t):
    'in'
    return t

def t_LARGER(t):
    '>'
    return t

def t_SMALLER(t):
    '<'
    return t

def t_LARGER_EQUAL(t):
    '>='
    return t

def t_SMALLER_EQUAL(t):
    '<='
    return t

def t_NOT_EQUAL(t):
    '!='
    return t

def t_EQUALS(t):
    '=='
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING(t):
    r'[\'"](.*?)[\'"]'
    t.value = t.value[1:-1]
    return t

def t_FIELD(t):
    r'[^$][0-9a-zA-Z-_]+' # everything that doesn't start with a $
    return t

def t_error(t):
    raise Exception('Lexer error: {}'.format(t))
    
def p_error(p):
    raise Exception('Parser error: {}'.format(p))
    
lexer = lex.lex()

operator_map = {'!=': '$ne', '>': '$gt', '<': '$lt', '>=': '$gte', '<=': '$lte'}
reverse_operator_map = {'!=': '$ne', '>': '$lt', '<': '$gt', '>=': '$lte', '<=': '$gte'}

def p_parens(p):
    'predicate : LPAREN predicate RPAREN'
    p[0] = p[2]

def p_not_between(p):
    'predicate : field NOT BETWEEN value AND value'
    p[0] = {p[1]: {'$lt': p[4], '$gt': p[6]}}

def p_between(p):
    'predicate : field BETWEEN value AND value'
    p[0] = {p[1]: {'$gte': p[3], '$lte': p[5]}}

def p_binary(p):
    'predicate : field operator value'
    p[0] = {p[1]: {operator_map[p[2]]: p[3]}}

def p_binary_multi(p):
    'predicate : value operator field operator value'
    p[0] = {p[3]: {operator_map[p[4]]: p[5], reverse_operator_map[p[2]]: p[1]}}
    
def p_equals(p):
    'predicate : field EQUALS value'
    p[0] = {p[1]: p[3]}

def p_not(p):
    'predicate : NOT predicate'
    p[0] = {'$not': p[2]}

def p_and(p):
    '''predicate : predicate AND predicate
                 | predicate OR predicate'''
    p[0] = {'$' + p[2]: [p[1], p[3]]}

def p_in(p):
    '''predicate : field IN value'''
    p[0] = {p[1]: {'$in': p[3]}}

def p_operator(p):
    '''operator : LARGER
                | SMALLER
                | LARGER_EQUAL
                | SMALLER_EQUAL
                | NOT_EQUAL'''
    p[0] = p[1]

def p_field(p):
    'field : FIELD'
    p[0] = p[1]

def p_value(p):
    '''value : NUMBER
             | STRING
             | NULL
             | BOOL
             | list
             | call'''
    p[0] = p[1]

def p_list(p):
    'list : LPAREN comma_delimited_values RPAREN'
    p[0] = p[2]

def p_list_empty(p):
    'list : LPAREN RPAREN'
    p[0] = []
    
def p_list_item(p):
    'comma_delimited_values : value'
    p[0] = [p[1]]

def p_list_comma_items(p):
    'comma_delimited_values : comma_delimited_values COMMA value'
    p[0] = p[1] + [p[3]]

def p_regex(p):
    'predicate : field TILDA value'
    p[0] = {p[1]: {'$regex': p[3]}}

def p_call(p):
    'call : FIELD list'
    import pdb;pdb.set_trace()

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'NOT'),
    ('left', 'BETWEEN'),
)

parser = yacc.yacc()

def parse(string):
    lexer.input(string)
    print list(lexer)
    return parser.parse(string, debug=1)
