# CFSMGEN
cfsmgen.py is c source code generator.


## Using
There two ways to describe FSM:

- as python library
- write description in plain text

## As python library
Example:
```
# This is all you need
from cfsmgen import FSMDesc, fsm_generate_c_source, fsm_generate_image

# Create fsm description object with name 'fsmtest'
f = FSMDesc('fsmname')

# Add transitions
f.add_transition('BEGIN',  'default',      'FIRST')
f.add_transition('FIRST',  'condition_1', 'SECOND', ['action'])
f.add_transition('FIRST',  'condition_2', 'SECOND', ['action', 'action2'])
f.add_transition('SECOND', 'condition_3',  'FIRST', ['action3'])
f.add_transition('SECOND', 'condition_4', 'SECOND', ['action5'])
f.add_transition('SECOND', 'condition_4',  'THIRD', ['action6', 'action7'])
f.add_transition('THIRD',      'default',  'FIRST', ['action8', 'action9'])

# Generate fsmtest.c and fsmtest.h
target_dir = './fsmtest'
fsm_generate_c_source(f, 'fsmdata_t', target_dir)

# Generate fsmtest.dot and fsdmtest.png
fsm_generate_image(f, target_dir)

```

FSMDesc interface:

- add_transition(state, event, nextState, actions=[])
- get_name()
- get_states()
- get_state_names()
- get_events()
- get_event_names()
- get_actions()
- get_event_names_of_state(state)
- get_events_of_state(state)
- get_transition(state, event)
- to_graphwiz()
       
Functions:

- fsm_generate_c_source(fsmdesc, user_data = 'user_data_t', target_dir='./')
- fsm_generate_image(fsmdesc, target_dir='./'):


## Plain text description
Exmaple:

1. Write file with content
```
# file fsmtest.fsm
# FSM name and data type passed to callbacks
fsmname fsmdata_t;

#Comment
BEGIN default FIRST;

FIRST condition_1 SECOND action;
FIRST condition_2 SECOND action action2;

# Another comment
SECOND condition_3 FIRST action3 #Comment about action
                        action4
                        action5;
SECOND condition_4 SECOND
                        action5;
SECOND condition_4 THIRD
                        action6 action7;

THIRD default FIRST
    action8 action9;
```

2. Execute
```
cfsmgen.py fsmtest.fsm
```

3. See result
Header:
```
#ifndef FSMNAME_H
#define FSMNAME_H

#ifdef __cplusplus
extern "C" {
#endif

typedef enum fsmname_state {
    fsmname_BEGIN,
    fsmname_FIRST,
    fsmname_SECOND,
    fsmname_THIRD
} fsmname_state;
#define fsmname_state_count 4

extern const char* fsmname_state_names[4];


typedef struct fsmdata_t fsmdata_t;

typedef struct fsmname_ctx_t fsmname_ctx_t;

struct fsmname_ctx_t {
    fsmname_state state;
    fsmdata_t* data;
};

void action(fsmdata_t* data);
void action2(fsmdata_t* data);
void action3(fsmdata_t* data);
void action4(fsmdata_t* data);
void action5(fsmdata_t* data);
void action6(fsmdata_t* data);
void action7(fsmdata_t* data);
void action8(fsmdata_t* data);
void action9(fsmdata_t* data);
int fsmname_condition_1(const fsmdata_t* data);
int fsmname_condition_2(const fsmdata_t* data);
int fsmname_condition_3(const fsmdata_t* data);
int fsmname_condition_4(const fsmdata_t* data);


void fsmname_step(fsmname_ctx_t* ctx);

#ifdef __cplusplus
}
#endif

#endif
```

and source:
```
#include "fsmname_fsm.h"

const char* fsmname_state_names[] = {
    "BEGIN",
    "FIRST",
    "SECOND",
    "THIRD"
};

void fsmname_step(fsmname_ctx_t* ctx)
{
    const fsmname_state state = ctx->state;
    fsmdata_t* data = ctx->data;

    switch(state) {
    case fsmname_BEGIN: 
        ctx->state = fsmname_FIRST;
    break;
    case fsmname_FIRST: 
        if (fsmname_condition_1(data)) {
            action(data);
            ctx->state = fsmname_SECOND;
            break;
        }
        if (fsmname_condition_2(data)) {
            action(data);
            action2(data);
            ctx->state = fsmname_SECOND;
            break;
        }
    break;
    case fsmname_SECOND: 
        if (fsmname_condition_3(data)) {
            action3(data);
            action4(data);
            action5(data);
            ctx->state = fsmname_FIRST;
            break;
        }
        if (fsmname_condition_4(data)) {
            action6(data);
            action7(data);
            ctx->state = fsmname_THIRD;
            break;
        }
    break;
    case fsmname_THIRD: 
        action8(data);
        action9(data);
        ctx->state = fsmname_FIRST;
    break;
    }
}
```

