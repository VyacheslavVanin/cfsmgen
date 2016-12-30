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
        return [ cprefix(self.name, s) for s in self.states]

    def get_state_names(self):
        return self.states

    def get_events(self):
        return [ cprefix(self.name, s) for s in self.events]

    def get_event_names(self):
        return self.events

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

    
def fsm_generate_c_source(fsmdesc):
    fsmname = fsmdesc.get_name()
    states  = fsmdesc.get_states()
    events  = fsmdesc.get_events()
    actions = fsmdesc.get_actions()
    state_names = fsmdesc.get_state_names()
    event_names = fsmdesc.get_event_names()

    fsmCtxName    = cprefix(fsmname, 'ctx', 't')
    fsmDataName   = cprefix(fsmname, 'data', 't')
    stateEnumName = cprefix(fsmname, 'state')
    eventEnumName = cprefix(fsmname, 'event')
    stateStringsNames = cprefix(fsmname, 'state_names')
    eventStringsNames = cprefix(fsmname, 'event_names')
    pfsmCtxName   = fsmCtxName + '*'
    pfsmDataName  = fsmDataName + '*'   
    cpfsmDataName  = 'const ' + fsmDataName + '*'   

    stepFuncName  = cprefix(fsmname, 'step') 

    with open(fsmname + '_fsm.h', 'w') as header:
        header.write('\n\n')
        header.write(cgen.genEnum(stateEnumName, states))
        header.write('\n')
        header.write(cgen.genStringArray(stateStringsNames, state_names))
        header.write('\n')

        header.write(cgen.genStructDecl(fsmDataName, [('dummy', 'int')]))
        header.write('\n')
        header.write(cgen.genStructDecl(fsmCtxName, [('state', stateEnumName),
                                              ('data', fsmDataName)]));
        header.write('\n')

        for action in actions:
            header.write(cgen.genFuncDecl(action, 'void', [('data', pfsmDataName)]))
            header.write('\n')

        header.write(cgen.genFuncDecl(stepFuncName, 'void', [('ctx', pfsmCtxName)]))
        header.write('\n\n')

    with open(fsmname + '_fsm.c', 'w') as source:
        source.write('#include "{}_fsm.h"\n\n'.format(fsmname))

        #generate dummy action-function implementations
        for action in actions:
            source.write(cgen.genFuncImpl(action, 'void', [('data', pfsmDataName)],
                                   '/* TODO: Add impementation here... */'))
            source.write('\n')

        for event in events:
            source.write(cgen.genFuncImpl(event, 'int', [('data', cpfsmDataName)],
                               '    /* TODO: Add impementation here... */\n' \
                               '    return 0;'))
            source.write('\n')

        #generate body of step function
        body  = 'const {} state = ctx->state;\n'.format(stateEnumName)
        body += '{} data = &ctx->data;\n'.format(pfsmDataName )
        body += 'switch(state) {\n'
        for s, sname in zip(states, state_names):
            body += 'case {}: \n'.format(s)
            for e in fsmdesc.get_event_names_of_state(sname):
                t = fsmdesc.get_transition(sname, e)
                event     = cprefix(fsmname, e)
                nextstate = cprefix(fsmname, t.next)
                action    = t.action
                body +='    if ({}(data)) {{\n'.format(event)
                body +='        {}(data);\n'.format(action) if action else ''
                body +='        ctx->state = {};\n'.format(nextstate)
                body +='        break;\n' \
                       '    }\n'
            body += 'break;\n'
        body += '}\n'
        source.write(cgen.genFuncImpl(stepFuncName,
                                      'void', [('ctx', pfsmCtxName)], body))




def cfsm_main():
    f = FSMDesc('fsmtest')
    f.add_transition('init', 'ev1', 'st1', 'action1')

    f.add_transition('st1', 'ev1', 'st1', 'action1')
    f.add_transition('st1', 'ev2', 'st2', 'action2')
    f.add_transition('st1', 'ev3', 'st3', 'action3')

    f.add_transition('st2', 'ev1', 'st1', 'action1')

    f.add_transition('st3', 'ev1', 'st1')

    fsm_generate_c_source(f)

    filename = '{}_fsm'.format(f.get_name())
    filenamedot = filename + '.dot'
    with open(filenamedot, 'w') as gv:
        gv.write(f.to_graphwiz())

    filenamepng = filename + '.png'
    os.system('dot {} -Tpng -o {}'.format(filenamedot, filenamepng))



if __name__ == '__main__':
    cfsm_main()

