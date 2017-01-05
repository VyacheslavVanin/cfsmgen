#!/usr/bin/python
import cgen
import os

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
    def __init__(self, nextState, action):
        self.next   = nextState
        self.action = action

    def __str__(self):
        action = self.action or 'None'
        return self.next + ', ' + action

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

    def add_transition(self, state, event, nextState, action=None):
        transition = TransitionDesc(nextState, action)
        if state not in self.transitions:
            self.transitions[state] = {}
        append_uniq(self.states, state)
        append_uniq(self.states, nextState)
        append_uniq(self.events, event)
        if action:
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

        header.write('#ifdef __cplusplus\n')
        header.write('extern "C" {\n')
        header.write('#endif\n\n')

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
                action    = t.action
                body +='        if ({}(data)) {{\n'.format(event)
                body +='            {}(data);\n'.format(action) if action else ''
                body +='            ctx->state = {};\n'.format(nextstate) if sname != nextstate else ''
                body +='            break;\n' \
                       '        }\n'
            if 'default' in eventlist:
                t = fsmdesc.get_transition(s, 'default')
                nextstate = cprefix(fsmname, t.next)
                action    = t.action
                body +='        {}(data);\n'.format(action) if action else ''
                body +='        ctx->state = {};\n'.format(nextstate) if sname != nextstate else ''
            body += '    break;\n'

        body += '    }'
        source.write(cgen.genFuncImpl(stepFuncName,
                                      'void', [('ctx', pfsmCtxName)], body))


def name_valid(name):
    return True
    
def names_valid(names):
    for name in names:
        if not name_valid(name):
            return False
    return True


def parse_text(filename):
    ret = FSMDesc()

    lines = []
    with open(filename, 'r') as f:
        lines = f.readlines()

    #first line - name of fsm, user data type
    firstlinewords = lines[0].split()
    transitions_lines = lines[1:]

    name, user_data = firstlinewords[0:2]
    for t in transitions_lines:
        transition_words = [w.strip() for w in t.split()]
        num_words = len(transition_words)
        state, event, nextstate, action = (None, None, None, None)
        if num_words >= 4:
            state, event, nextstate, action = transition_words[0:4]
            if names_valid([state, event, nextstate, action]):
                ret.add_transition(state, event, nextstate, action)
        elif num_words == 3:
            state, event, nextstate = transition_words[0:3]
            if names_valid([state, event, nextstate]):
                ret.add_transition(state, event, nextstate)
    
    return ret
