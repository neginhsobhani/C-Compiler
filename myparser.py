import sys

import ply.yacc as yacc
import ply.lex as lex
import copy
import code_generator
keywords = {
    'program': 'PROGRAM',
    'var': 'VAR',
    'int': 'INT',
    'begin': 'BEGIN',
    'end': 'END',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'print': 'PRINT',
    'and': 'AND',
    'or': 'OR',
    'mod': 'MOD',
    'not': 'NOT'
}

tokens = [
             'TRUE', 'FALSE',
             'PLUS', 'MINUS',
             'TIMES', 'DIVIDE',
             'INTEGER', 'ID',
             'EQUAL', 'LESS', 'LESSEQ', 'MORE', 'MOREEQ', 'NOTEQ',
             'SEM', 'COLON', 'COMMA', 'LPAREN', 'RPAREN',
             'ASSIGN', 'UMINUS'
         ] + list(keywords.values())

# Tokens
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_TRUE = r'true'
t_FALSE = r'false'
t_PLUS = r'\+'
t_MINUS = r'\-'
t_DIVIDE = r'\/'
t_TIMES = r'\*'
t_EQUAL = r'\='
t_LESS = r'\<'
t_LESSEQ = r'\<='
t_NOTEQ = r'\<>'
t_MORE = r'\>'
t_MOREEQ = r'\>='
t_SEM = r'\;'
t_COLON = r'\:'
t_COMMA = r'\,'
t_ASSIGN = r'\:='
t_UMINUS = r'\-'

# Ignored characters
t_ignore = " \t\n"


# Tokens


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = keywords.get(t.value, 'ID')  # Check for reserved words
    return t


def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()

# Parsing rules
precedence = (
    ('right', 'OR'),
    ('right', 'AND'),
    ('right', 'NOT'),
    ('right', 'PLUS', 'MINUS'),
    ('right', 'TIMES', 'DIVIDE'),
    ('nonassoc', 'MOD'),  # Nonassociative operators
    ('right', 'UMINUS'),
)

# dictionary of names
names = {}
temps = []
quadruples = []
next_available_label = 0


def backpatch(l: list, i: int):
    for line_number in l:
        prv_tuple = quadruples[line_number - 1]
        new_tuple = (prv_tuple[0], i)
        quadruples[line_number - 1] = new_tuple


def nextinstr():
    return len(quadruples) + 1


def p_marker(t):
    'marker : '
    t[0] = nextinstr()


class N:
    def __init__(self, nextlist):
        self.nextlist = nextlist
        quadruples.append(('goto',))


def p_N(t):
    'N : '
    t[0] = N([nextinstr()])
    pass


# Expression class


class E:
    def __init__(self, t, f):
        self.truelist = t
        self.falselist = f
        self.addr = ""

    def __str__(self):
        return self.addr


class Statement:
    def __init__(self, nextlist):
        self.nextlist = nextlist


def p_expression_integer(t):
    '''expression : INTEGER'''
    t[0] = E([], [])
    t[0].addr = str(t[1])


def p_expression_id(t):
    '''expression : ID'''
    t[0] = E([], [])
    t[0].addr = t[1]


def p_expression_plus(t):
    '''expression : expression PLUS expression'''
    t[0] = E([], [])
    t[0].addr = 'temp_int_' + str(len(temps) + 1)
    temps.append(t[0].addr)
    quadruples.append((str(t[0]) + ' = ' + str(t[1]) + ' + ' + str(t[3]),))


def p_expression_minus(t):
    '''expression : expression MINUS expression'''
    t[0] = E([], [])
    t[0].addr = 'temp_int_' + str(len(temps) + 1)
    temps.append(t[0].addr)
    quadruples.append((str(t[0]) + ' = ' + str(t[1]) + ' - ' + str(t[3]),))


def p_expression_times(t):
    """expression : expression TIMES expression"""
    t[0] = E([], [])
    t[0].addr = 'temp_int_' + str(len(temps) + 1)
    temps.append(t[0].addr)
    quadruples.append((str(t[0]) + ' = ' + str(t[1]) + ' * ' + str(t[3]),))


def p_expression_div(t):
    """expression : expression DIVIDE expression"""
    t[0] = E([], [])
    t[0].addr = 'temp_int_' + str(len(temps) + 1)
    temps.append(t[0].addr)
    quadruples.append((str(t[0]) + ' = ' + str(t[1]) + ' / ' + str(t[3]),))


def p_expression_mod(t):
    """expression : expression MOD expression"""
    t[0] = E([], [])
    t[0].addr = 'temp_int_' + str(len(temps) + 1)
    temps.append(t[0].addr)
    quadruples.append((str(t[0]) + ' = ' + str(t[1]) + ' % ' + str(t[3]),))


def p_expression_uminus(t):
    '''expression : MINUS expression %prec UMINUS'''
    t[0] = E([], [])
    t[0].addr = "-" + str(t[2].addr)


def p_expression_relop(t):
    '''expression : expression LESS expression
                | expression EQUAL expression
                | expression MORE expression
                | expression NOTEQ expression
                | expression LESSEQ expression
                | expression MOREEQ expression'''
    t[0] = E([nextinstr()], [nextinstr() + 1])
    t[0].addr = str(t[1]) + t[2] + str(t[3])
    quadruples.append(
        ('if ' + '(' + str(t[1]) + ' ' + t[2] + ' ' + str(t[3]) + ')' + ' goto',))
    quadruples.append(('goto',))


def p_expression_or(t):
    '''expression : expression OR marker expression'''
    backpatch(t[1].falselist, t[3])
    truelist = t[1].truelist + t[4].truelist
    falselist = t[4].falselist
    t[0] = E(truelist, falselist)


def p_expression_and(t):
    'expression : expression AND marker expression'
    backpatch(t[1].truelist, t[3])
    truelist = t[4].truelist
    falselist = t[4].falselist + t[1].falselist
    t[0] = E(truelist, falselist)


def p_expression_unot(t):
    'expression : NOT expression'
    t[0] = E(t[2].falselist, t[2].truelist)


def p_expression_group(t):
    'expression : LPAREN expression RPAREN'
    t[0] = copy.deepcopy(t[2])
    t[0].addr = '(' + str(t[2]) + ')'


def p_statement_assign(t):
    """statement : ID ASSIGN expression"""
    quadruples.append((str(t[1]) + ' = ' + str(t[3]),))
    t[0] = Statement([])


def p_statement_ifthen(t):
    """statement : IF expression THEN marker statement"""
    backpatch(t[2].truelist, t[4])
    if t[5].nextlist == None:
        nextlist = t[2].falselist
    else:
        nextlist = t[2].falselist + t[5].nextlist
    t[0] = Statement(nextlist)


def p_statement_ifthenelse(t):
    """statement : IF expression THEN marker statement N ELSE marker statement"""
    backpatch(t[2].truelist, t[4])
    backpatch(t[2].falselist, t[8])
    temp = t[5].nextlist + t[6].nextlist
    nextlist = temp + t[9].nextlist
    t[0] = Statement(nextlist)


def p_statement_while(t):
    """statement : WHILE marker expression DO marker statement"""
    backpatch(t[6].nextlist, t[2])
    backpatch(t[3].truelist, t[5])
    nextlist = t[3].falselist
    t[0] = Statement(nextlist)
    quadruples.append(('goto', t[2]))


def p_statement_compound(t):
    """statement : compoundStatement"""
    # t[0] = t[1]
    t[0] = Statement([])


def p_statement_print(t):
    """statement : PRINT LPAREN expression RPAREN"""
    quadruples.append(('printf("%d\\n",' + str(t[3]) + ")",))
    t[0] = Statement([])


class StatementList:
    def __init__(self, nextlist):
        self.nextlist = nextlist


def p_statementList_stmliststm(t):
    """statementList : statementList SEM marker statement"""
    backpatch(t[1].nextlist, t[3])
    nextlist = t[4].nextlist
    t[0] = StatementList(nextlist)


def p_statementList_stm(t):
    """statementList : statement"""
    nextlist = t[1].nextlist
    t[0] = StatementList(nextlist)


class CompoundStatement:
    def __init__(self, nextlist):
        self.nextlist = nextlist


def p_compoundStatement_beginend(t):
    """compoundStatement : BEGIN statementList END"""
    nextlist = t[2].nextlist
    # print(nextlist, quadruples[-1], len(quadruples))
    backpatch(t[2].nextlist, nextinstr())
    t[0] = CompoundStatement(nextlist)
    quadruples.append(('endblock',))


def p_type_int(t):
    """type : INT"""
    t[0] = t[1]


def p_idList_id(t):
    """idList : ID"""
    t[0] = t[1]


def p_idList_idid(t):
    """idList : idList COMMA ID"""
    t[0] = str(t[1]) + ',' + str(t[3])


def p_declarationList_idList_type(t):
    '''declarationList : idList COLON type'''
    t[0] = t[1]
    for n in str(t[1]).split(','):
        if t[3] in names:
            names[t[3]].append(n)
        else:
            names[t[3]] = [n]


def p_declarationList_decidtype(t):
    """declarationList : declarationList SEM idList COLON type"""
    t[0] = t[1]
    for n in str(t[3]).split(','):
        if t[5] in names:
            names[t[5]].append(n)
        else:
            names[t[5]] = [n]


def p_declarations_var(t):
    """declarations : VAR declarationList"""
    t[0] = t[2]


def p_declarations_empty(t):
    """declarations : """
    pass


def p_program(t):
    """program : PROGRAM ID declarations compoundStatement"""
    pass


def p_error(t):
    print("Syntax error at '%s'" % t.value)


parser = yacc.yacc(start="program")

while True:
    try:
        i = input('calc > ')
        s = ''
        # print("-> Enter the code you want to compile")
        # print("->> Then type *compile* in the last line and press enter in order to start compiling\n")
        # # reading the input
        # for line in sys.stdin:
        #     if '*compile*' == line.rstrip():
        #         break
        #     s += str(line)
        if i == 'compile':
            f = open('test.txt', 'r')
            lines = f.readlines()
            for line in lines:
                s += str(line)

    except EOFError:
        break
    r = parser.parse(s)
    counter = 0
    for q in quadruples:
        counter += 1
        if counter == len(quadruples) - 1:
            break
        else:
            print('{}. {}'.format(counter, q))
    code_generator.c_code_generator(quadruples, names, temps)
    quadruples.clear()
