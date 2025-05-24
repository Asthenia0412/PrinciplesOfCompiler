from LR1Item import LR1Item
class LALR1Parser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.first = self.compute_first()
        self.states, self.transitions, self.goto_table = self.build_automaton()
        self.action_table = self.build_action_table()

    def compute_first(self):
        first = {nt: set() for nt in self.grammar.non_terminals}

        changed = True
        while changed:
            changed = False
            for nt in self.grammar.non_terminals:
                for prod in self.grammar.get_productions_for(nt):
                    for symbol in prod[1]:
                        if symbol in self.grammar.terminals:
                            if symbol not in first[nt]:
                                first[nt].add(symbol)
                                changed = True
                            break
                        elif symbol in self.grammar.non_terminals:
                            added = len(first[nt])
                            first[nt].update(first[symbol] - {'ε'})
                            if added != len(first[nt]):
                                changed = True
                            if 'ε' not in first[symbol]:
                                break
                    else:
                        if 'ε' not in first[nt]:
                            first[nt].add('ε')
                            changed = True
        return first

    def closure(self, items):
        closure = set(items)
        changed = True
        while changed:
            changed = False
            for item in list(closure):
                next_symbol = item.next_symbol()
                if next_symbol in self.grammar.non_terminals:
                    beta = item.production[1][item.dot_pos + 1:]
                    lookaheads = self.compute_lookaheads(beta, item.lookahead)

                    for prod in self.grammar.get_productions_for(next_symbol):
                        for lookahead in lookaheads:
                            new_item = LR1Item(prod, 0, lookahead)
                            if new_item not in closure:
                                closure.add(new_item)
                                changed = True
        return frozenset(closure)

    def compute_lookaheads(self, beta, lookahead):
        if not beta:
            return {lookahead}

        first_beta = set()
        for symbol in beta:
            if symbol in self.grammar.terminals:
                first_beta.add(symbol)
                return first_beta
            else:
                first_beta.update(self.first[symbol] - {'ε'})
                if 'ε' not in self.first[symbol]:
                    return first_beta
        first_beta.add(lookahead)
        return first_beta

    def goto(self, items, symbol):
        new_items = set()
        for item in items:
            if item.next_symbol() == symbol:
                new_items.add(item.advance())
        return self.closure(new_items) if new_items else None

    def build_automaton(self):
        # First build LR(1) automaton
        start_production = (self.grammar.start_symbol + "'", [self.grammar.start_symbol])
        start_item = LR1Item(start_production, 0, '$')
        start_state = self.closure({start_item})

        lr1_states = [start_state]
        transitions = []
        goto_table = {}

        unprocessed = [start_state]

        while unprocessed:
            current = unprocessed.pop()

            symbols = set()
            for item in current:
                next_sym = item.next_symbol()
                if next_sym is not None:
                    symbols.add(next_sym)

            for symbol in symbols:
                next_state = self.goto(current, symbol)

                if next_state not in lr1_states:
                    lr1_states.append(next_state)
                    unprocessed.append(next_state)

                transitions.append((lr1_states.index(current), symbol, lr1_states.index(next_state)))

                goto_key = (lr1_states.index(current), symbol)
                goto_table[goto_key] = lr1_states.index(next_state)

        # Now merge states with the same core (LR0 items)
        cores = {}
        for i, state in enumerate(lr1_states):
            core = frozenset((item.production, item.dot_pos) for item in state)
            if core not in cores:
                cores[core] = []
            cores[core].append(i)

        # Create mapping from LR1 state to LALR state
        state_mapping = {}
        lalr_states = []
        for core, state_indices in cores.items():
            # Merge all LR1 states with this core
            merged_items = set()
            for idx in state_indices:
                merged_items.update(lr1_states[idx])
                state_mapping[idx] = len(lalr_states)
            lalr_states.append(frozenset(merged_items))

        # Update transitions and goto table
        new_transitions = []
        new_goto_table = {}
        for src, symbol, dest in transitions:
            new_src = state_mapping[src]
            new_dest = state_mapping[dest]
            new_transitions.append((new_src, symbol, new_dest))
            new_goto_table[(new_src, symbol)] = new_dest

        return lalr_states, new_transitions, new_goto_table

    def build_action_table(self):
        action_table = {}

        for state_idx, state in enumerate(self.states):
            for item in state:
                if item.is_reduce_item():
                    if item.production[0] == self.grammar.start_symbol + "'":
                        action_table[(state_idx, '$')] = ('accept',)
                    else:
                        action_key = (state_idx, item.lookahead)
                        if action_key in action_table:
                            existing_action = action_table[action_key]
                            if existing_action[0] != 'reduce' or existing_action[1] != item.production:
                                raise ValueError("Grammar is not LALR(1)")
                        action_table[action_key] = ('reduce', item.production)
                else:
                    next_sym = item.next_symbol()
                    if next_sym in self.grammar.terminals:
                        goto_key = (state_idx, next_sym)
                        if goto_key in self.goto_table:
                            action_table[goto_key] = ('shift', self.goto_table[goto_key])

        return action_table

    def parse(self, input_tokens):
        input_tokens = input_tokens + ['$']
        stack = [0]
        pos = 0

        while True:
            state = stack[-1]
            current_token = input_tokens[pos]

            action_key = (state, current_token)
            if action_key not in self.action_table:
                raise SyntaxError(f"No action for state {state} on {current_token}")

            action = self.action_table[action_key]

            if action[0] == 'shift':
                stack.append(current_token)
                stack.append(action[1])
                pos += 1
            elif action[0] == 'reduce':
                production = action[1]
                for _ in range(2 * len(production[1])):
                    stack.pop()

                state = stack[-1]
                stack.append(production[0])
                goto_key = (state, production[0])
                if goto_key not in self.goto_table:
                    raise SyntaxError(f"No goto for state {state} on {production[0]}")
                stack.append(self.goto_table[goto_key])
            elif action[0] == 'accept':
                return True
            else:
                raise SyntaxError("Invalid action")