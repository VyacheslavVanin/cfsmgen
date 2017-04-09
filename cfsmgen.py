#!/usr/bin/python
import cgen
import os
import sys
import re

def cprefix(prefix, name, postfix=''):
    ret = name
    if prefix:
        ret = prefix + '_' + ret
    if postfix:
        ret = ret + '_' + postfix
    return ret

def append_uniq(container, elem):
    if elem not in container:
        container.append(elem)

class TransitionDesc:
    def __init__(self, nextState, actions):
        self.next   = nextState
        self.actions = actions

    def __str__(self):
        action = self.actions or 'None'
        return self.next + ', ' + actions

    def __repr__(self):
        return '\'' + self.__str__() + '\''


class FSMDesc:
    def __init__(self, name):
        self.name        = name
        self.states      = []
        self.events      = []
        self.actions     = []
        self.transitions = {}

    def __str__(self):
        ret = 'states: {}\n'.format(self.states)
        ret += 'events: {}\n'.format(self.events)
        ret += 'transitions: {}\n'.format(self.transitions)
        return ret

    def add_transition(self, state, event, nextState, actions=[]):
        transition = TransitionDesc(nextState, actions or [])
        if state not in self.transitions:
            self.transitions[state] = {}
        append_uniq(self.states, state)
        append_uniq(self.states, nextState)
        append_uniq(self.events, event)
        if actions:
            for action in actions:
                append_uniq(self.actions, action)
        self.transitions[state][event] = transition
    
    def get_name(self):
        return self.name

    def get_states(self):
        return self.states

    def get_state_names(self):
        return [ cprefix(self.name, s) for s in self.states]

    def get_events(self):
        return self.events

    def get_event_names(self):
        return [ cprefix(self.name, s) for s in self.events if s != 'default']

    def get_actions(self):
        return self.actions

    def get_event_names_of_state(self, state):
        return [k for k in self.transitions[state].keys()] if state in self.transitions else []

    def get_events_of_state(self, state):
        return [cprefix(self.name, k) for k in self.transitions[state].keys()] if state in self.transitions else []

    def get_transition(self, state, event):
        if state not in self.transitions and \
           event not in self.transitions[state]:
            return None
        return self.transitions[state][event]

    def to_graphwiz(self):
        ret = 'digraph {} {{\n'.format(self.name)
        trs = self.transitions
        for start in trs.keys():
            for event in trs[start]:
                t = self.get_transition(start, event)
                end = t.next
                ret += '    {} -> {} [label="{}"];\n'.format(start,end,event)
        ret += '}'
        return ret


def fsm_generate_image(f, target_dir='./'):
    filename_dot = '{}/{}.dot'.format(target_dir, f.get_name())
    filename_png = '{}/{}.png'.format(target_dir, f.get_name())
    with open(filename_dot, 'w') as gv:
        gv.write(f.to_graphwiz())

    os.system('dot {} -Tpng -o {}'.format(filename_dot, filename_png))

    
def fsm_generate_c_source(fsmdesc, user_data = 'user_data_t', target_dir='./'):
    fsmname = fsmdesc.get_name()
    states  = fsmdesc.get_states()
    events  = fsmdesc.get_events()
    actions = fsmdesc.get_actions()
    state_names = fsmdesc.get_state_names()
    event_names = fsmdesc.get_event_names()

    fsmCtxName    = cprefix(fsmname, 'ctx', 't')
    fsmDataName   = user_data or cprefix(fsmname, 'data', 't')
    stateEnumName = cprefix(fsmname, 'state')
    eventEnumName = cprefix(fsmname, 'event')
    stateStringsNames = cprefix(fsmname, 'state_names')
    eventStringsNames = cprefix(fsmname, 'event_names')
    pfsmCtxName   = fsmCtxName + '*'
    pfsmDataName  = fsmDataName + '*'   
    cpfsmDataName  = 'const ' + fsmDataName + '*'   

    stepFuncName  = cprefix(fsmname, 'step') 

    header_filename = '{}/{}_fsm.h'.format(target_dir, fsmname)
    source_filename = '{}/{}_fsm.c'.format(target_dir, fsmname)
    os.makedirs(target_dir, exist_ok=True)

    with open(header_filename, 'w') as header:
        # include guard
        header.write('#ifndef {0}_H\n' \
                     '#define {0}_H\n\n'.format(fsmname.upper()))

        header.write('#ifdef __cplusplus\n')
        header.write('extern "C" {\n')
        header.write('#endif\n\n')

        # enum states
        header.write(cgen.genEnum(stateEnumName, state_names))
        header.write('\n')

        # state names declarations
        header.write('extern const char* {}[{}];\n\n'.format(stateStringsNames,
                                                             len(state_names)))
        header.write('\n')

        # Forward declare user data
        header.write(cgen.genStructForwardDecl(fsmDataName))
        header.write('\n')


        # declare fsm context structure
        header.write(cgen.genStructForwardDecl(fsmCtxName))
        header.write('\n')

        header.write(cgen.genStructDecl(fsmCtxName, [('state', stateEnumName),
                                              ('data', pfsmDataName)]));
        header.write('\n')


        # generate action declarations
        for action in actions:
            header.write(cgen.genFuncDecl(action, 'void', [('data', pfsmDataName)]))
            header.write('\n')

        # generate event declarations
        for event in event_names:
            header.write(cgen.genFuncDecl(event, 'int', [('data', cpfsmDataName)]))
            header.write('\n')

        header.write('\n\n')

        # generate fsm step function declaration
        header.write(cgen.genFuncDecl(stepFuncName, 'void', [('ctx', pfsmCtxName)]))
        header.write('\n\n')

        header.write('#ifdef __cplusplus\n')
        header.write('}\n')
        header.write('#endif\n\n')

        header.write('#endif\n')


    with open(source_filename, 'w') as source:
        source.write('#include "{}_fsm.h"\n\n'.format(fsmname))

        # state names definitions
        source.write(cgen.genStringArray(stateStringsNames, states))
        source.write('\n')

        #generate body of step function
        body  = '    const {} state = ctx->state;\n'.format(stateEnumName)
        body += '    {} data = ctx->data;\n\n'.format(pfsmDataName )
        body += '    switch(state) {\n'
        for s, sname in zip(states, state_names):
            body += '    case {}: \n'.format(sname)
            eventlist = fsmdesc.get_event_names_of_state(s)
            for e in eventlist:
                if e == 'default':
                    continue
                t = fsmdesc.get_transition(s, e)
                event     = cprefix(fsmname, e)
                nextstate = cprefix(fsmname, t.next)
                actions    = t.actions
                body +='        if ({}(data)) {{\n'.format(event)
                for action in actions:
                    body +='            {}(data);\n'.format(action)
                body +='            ctx->state = {};\n'.format(nextstate) if sname != nextstate else ''
                body +='            break;\n' \
                       '        }\n'
            if 'default' in eventlist:
                t = fsmdesc.get_transition(s, 'default')
                nextstate = cprefix(fsmname, t.next)
                actions    = t.actions
                for action in actions:
                    body +='        {}(data);\n'.format(action)
                body +='        ctx->state = {};\n'.format(nextstate) if sname != nextstate else ''
            body += '    break;\n'

        body += '    }'
        source.write(cgen.genFuncImpl(stepFuncName,
                                      'void', [('ctx', pfsmCtxName)], body))


def name_valid(name):
    # TODO: implement this. Should test if name is valid 'C' variable name
    return True
    
def names_valid(names):
    for name in names:
        if not name_valid(name):
            return False
    return True


def parse_to_transition_lines(source):
    def spitlist(l, condition):
        sublist = []
        ret = []
        for x in l:
            if not condition(x):
                sublist.append(x)
            elif sublist:
                ret.append(sublist)
                sublist = []
        return ret

    splitter = re.compile(r'(\w+|#.+|;)')
    tokens = splitter.findall(source)
    tokens_wo_comments = [t for t in tokens if not t.startswith('#')]
    return spitlist(tokens_wo_comments, lambda x: x == ';')


def parse_text(filename):
    source = open(filename, 'r').read()
    transitions_lines = parse_to_transition_lines(source)

    #first line - name of fsm, user data type
    name, user_data = transitions_lines[0]
    transitions_lines = transitions_lines[1:]

    ret = FSMDesc(name)
    for transition_words in transitions_lines:
        state, event, nextstate = transition_words[0:3]
        actions = transition_words[3:]
        if names_valid([state, event, nextstate] + actions):
            ret.add_transition(state, event, nextstate, actions)
    
    return (ret, user_data)


def print_help():
    print('cfsmgen - c source generator for FSM.\n'
          'usage:\n'
          '    cfsmgen.py infile.fsm [OPTIONS]\n\n'
          'fsm file format (example):\n\n'
          '# Comments after \'#\' character till the end of line\n'
          '# First non-comment line must be two words:\n'
          '#    - first - name of FSM to generate.\n'
          '#      Used for generated file names, variable and enums prefixes etc.\n'
          '#    - second - user data type name. Used to pass user data to callbacks.\n'
          'fsmname user_data_struct_t;\n\n'
          '# Then define transitions using folowing format:\n'
          '# INITIAL_STATE_NAME condition_name TARGET_STATE_NAME [action_name_1 action_name_2]; \n'
          '# For example:\n'
          'unpressed is_button_pressed pressed onButtonPress;\n\n'
          '# Or for multiple actions (onButtonClick, incrementClickCounter)\n'
          'pressed is_button_released unpressed onButtonClick incrementClickCounter;\n\n'
          )
    

def cfsmmain():
    args = sys.argv
    argc = len(args)
    if argc < 2:
        print_help()
        return

    if args[2] in ['-h', '--help']:
        print_help()
        return

    filename = args[1]
    fsm, user_data = parse_text(filename)
    fsm_generate_c_source(fsm, user_data)
    fsm_generate_image(fsm)

if __name__ == '__main__':
    cfsmmain()
