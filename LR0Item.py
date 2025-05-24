class LR0Item:
    def __init__(self, production, dot_pos=0):
        self.production = production
        self.dot_pos = dot_pos

    def __eq__(self, other):
        return self.production == other.production and self.dot_pos == other.dot_pos

    def __hash__(self):
        return hash((self.production, self.dot_pos))

    def next_symbol(self):
        if self.dot_pos < len(self.production[1]):
            return self.production[1][self.dot_pos]
        return None

    def is_reduce_item(self):
        return self.dot_pos == len(self.production[1])

    def advance(self):
        return LR0Item(self.production, self.dot_pos + 1)


class LR0Parser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.states, self.transitions, self.goto_table = self.build_automaton()
        self.action_table = self.build_action_table()

    def closure(self, items):
        closure = set(items)
        changed = True
        while changed:
            changed = False
            for item in list(closure):
                next_symbol = item.next_symbol()
                if next_symbol in self.grammar.non_terminals:
                    for prod in self.grammar.get_productions_for(next_symbol):
                        new_item = LR0Item(prod)
                        if new_item not in closure:
                            closure.add(new_item)
                            changed = True
        return frozenset(closure)

    def goto(self, items, symbol):
        new_items = set()
        for item in items:
            if item.next_symbol() == symbol:
                new_items.add(item.advance())
        return self.closure(new_items) if new_items else None

    def build_automaton(self):
        start_production = (self.grammar.start_symbol + "'", [self.grammar.start_symbol])
        start_item = LR0Item(start_production)
        start_state = self.closure({start_item})

        states = [start_state]
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

                if next_state not in states:
                    states.append(next_state)
                    unprocessed.append(next_state)

                transitions.append((states.index(current), symbol, states.index(next_state)))

                goto_key = (states.index(current), symbol)
                goto_table[goto_key] = states.index(next_state)

        return states, transitions, goto_table

    def build_action_table(self):
        action_table = {}

        for state_idx, state in enumerate(self.states):
            for item in state:
                if item.is_reduce_item():
                    if item.production[0] == self.grammar.start_symbol + "'":
                        action_table[(state_idx, '$')] = ('accept',)
                    else:
                        for terminal in self.grammar.terminals.union({'$'}):
                            action_table[(state_idx, terminal)] = ('reduce', item.production)
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