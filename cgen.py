#!/usr/bin/python3

def genFuncSignature(name, returnType, params):
    parameters = ', '.join(['{} {}'.format(Type, Name) for Name, Type in params]) 
    return '{} {}({})'.format(returnType, name, parameters)

def genFuncDecl(name, returnType, params):
    return genFuncSignature(name, returnType, params) + ';'

def genFuncImpl(name, returnType, params, body = ''):
    return '{}\n' \
           '{{\n' \
           '{}\n' \
           '}}\n'.format(genFuncSignature(name, returnType, params), body)


def genEnum(name, members):
    ret  = 'typedef enum {} {{\n'.format(name)
    ret += '    {}'.format(',\n    '.join(members))
    ret += '\n}} {};\n'.format(name)
    ret += '#define {}_count {}\n'.format(name, len(members))
    return ret

def genStringArray(name, strings):
    ret = 'const char* {}[] = {{\n'.format(name)
    ret += '    {}\n'.format(',\n    '.join(['"{}"'.format(s) for s in strings]))
    ret += '};\n'
    return ret

def genStructForwardDecl(name):
    ret = 'typedef struct {0} {0};\n'.format(name)
    return ret

def genStructDecl(name, members):
    ret = 'struct {} {{\n'.format(name)
    fields = ['    {} {}'.format(fieldtype, fieldname) for fieldname, fieldtype in members]
    ret += ';\n'.join(fields)
    ret += ';\n};\n'
    return ret



def cgenmain():
    p = [ ('a', 'int'), ('b', 'float')]
    print(genFuncDecl('foo', 'float', p))
    print(genFuncImpl('foo', 'float', p, 'printf("Hello, World!!!\\n");'))
    print(genEnum('states', ['begin', 'end', 'waitpz', 'prepare']))
    print(genStructDecl('bar', p))


if __name__ == '__main__':
    cgenmain()

