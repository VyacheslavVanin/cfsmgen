#!/usr/bin/python
import cgen

def cprefix(prefix, name, postfix=''):
    ret = name
    if prefix:
        ret = prefix + '_' + ret
    if postfix:
        ret = ret + '_' + postfix
    return ret

class TransitionDesc:
    def __init__(self, nextState, action):
        self.next   = nextState
        self.action = action

    def __str__(self):
        return self.next + ', ' + self.action

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

    def add_transition(self, state, event, nextState, action):
        transition = TransitionDesc(nextState, action)
        if state not in self.transitions:
            self.transitions[state] = {}
        if state not in self.states:
            self.states.append(state)
        if nextState not in self.states:
            self.states.append(nextState)
        if event not in self.events:
            self.events.append(event)
        if action not in self.actions:
            self.actions.append(action)
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
        if state not in self.transitions:
            return None
        if event not in self.transitions[state]:
            return None
        return self.transitions[state][event]



def main():
    f = FSMDesc('fsmtest')
    f.add_transition('init', 'ev1', 'st1', 'action1')
    f.add_transition('st1', 'ev1', 'st1', 'action1')
    f.add_transition('st1', 'ev2', 'st2', 'action2')
    f.add_transition('st1', 'ev3', 'st3', 'action3')
    f.add_transition('st2', 'ev1', 'st1', 'action4')
    f.add_transition('st3', 'ev1', 'st1', 'action4')

    fsmname = f.get_name()
    states  = f.get_states()
    events  = f.get_events()
    actions = f.get_actions()
    state_names = f.get_state_names()
    event_names = f.get_event_names()

    fsmCtxName    = cprefix(fsmname, 'ctx', 't')
    fsmDataName   = cprefix(fsmname, 'data', 't')
    stateEnumName = cprefix(fsmname, 'state')
    eventEnumName = cprefix(fsmname, 'event')
    stateStringsNames = cprefix(fsmname, 'state_names')
    eventStringsNames = cprefix(fsmname, 'event_names')
    pfsmCtxName   = fsmCtxName + '*'
    pfsmDataName  = fsmDataName + '*'   

    stepFuncName  = cprefix(fsmname, 'step') 

    with open(fsmname + '_fsm.h', 'w') as header:
        header.write('\n\n')
        header.write(cgen.genEnum(stateEnumName, states))
        header.write('\n')
        header.write(cgen.genEnum(eventEnumName, events))
        header.write('\n')
        header.write(cgen.genStringArray(stateStringsNames, state_names))
        header.write('\n')
        header.write(cgen.genStringArray(eventStringsNames, event_names))
        header.write('\n')

        header.write(cgen.genStructDecl(fsmDataName, [('dummy', 'int')]))
        header.write('\n')
        header.write(cgen.genStructDecl(fsmCtxName, [('state', stateEnumName),
                                              ('data', fsmDataName)]));
        header.write('\n')

        for action in actions:
            header.write(cgen.genFuncDecl(action, 'void', [('data', pfsmDataName)]))
            header.write('\n')

        header.write(cgen.genFuncDecl(stepFuncName, 'void', [('ctx', pfsmCtxName),
                                                      ('event', eventEnumName)]))
        header.write('\n\n')

    with open(fsmname + '_fsm.c', 'w') as source:
        source.write('#include "{}_fsm.h"\n\n'.format(fsmname))
        for action in actions:
            source.write(cgen.genFuncImpl(action, 'void', [('data', pfsmDataName)],
                                   '/* TODO: Add impementation here... */'))
            source.write('\n')

        #generate body of step function
        body  = 'const ' + stateEnumName + ' state = ctx->state;\n'
        body += pfsmDataName + ' data = &ctx->data;\n'
        body += 'switch(state) {\n'
        for s,sname in zip(states, state_names):
            body += 'case {}:{{ \n'.format(s)
            body += '    switch(event) {\n'
            for e in f.get_event_names_of_state(sname):
                t = f.get_transition(sname, e)
                nextstate = t.next
                action    = t.action
                body += '    case ' + cprefix(fsmname, e) + ': '
                body += action + '(data); ctx->state = ' + cprefix(fsmname, nextstate) + '; '
                body += 'break;\n'
            body += '    default: break;}\n'
            body += 'break;}\n'
        body += '}'
        source.write(cgen.genFuncImpl(stepFuncName, 'void', [('ctx', pfsmCtxName),
                                                      ('event', eventEnumName)],
                               body))


if __name__ == '__main__':
    main()

