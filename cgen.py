#!/usr/bin/python3

def genFuncSignature(name, returnType, params):
    ret = ''
    ret += returnType + ' ' + name + '('
    paramss = [Type + ' ' + Name for Name, Type in params]
    ret += ', '.join(paramss)
    ret += ')'
    return ret

def genFuncDecl(name, returnType, params):
    return genFuncSignature(name, returnType, params) + ';'

def genFuncImpl(name, returnType, params, body = ''):
    return genFuncSignature(name, returnType, params) + '{\n' + body + '\n}\n'


def genEnum(name, members):
    ret = 'typedef enum ' + name + ' {\n    '
    ret += ',\n    '.join(members)
    ret += '\n} ' + name + ';\n'
    ret += '#define ' + name + '_count ' + str(len(members)) + '\n'
    return ret

def genStringArray(name, strings):
    ret = 'const char* ' + name + '[] = {\n    \"'
    ret += '\",\n    \"'.join(strings)
    ret += '\"\n};\n'
    return ret


def genStructDecl(name, members):
    ret = 'typedef struct ' + name + ' {\n'
    fields = [ '    ' + fieldtype + ' ' + fieldname for fieldname, fieldtype in members]
    ret += ';\n'.join(fields)
    ret += ';\n} ' + name + ';\n'
    return ret



def cgenmain():
    p = [ ('a', 'int'), ('b', 'float')]
    print(genFuncDecl('foo', 'float', p))
    print(genFuncImpl('foo', 'float', p, 'printf("Hello, World!!!\\n");'))
    print(genEnum('states', ['begin', 'end', 'waitpz', 'prepare']))
    print(genStructDecl('bar', p))


if __name__ == '__main__':
    cgenmain()

