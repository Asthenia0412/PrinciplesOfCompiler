class SLR1Parser(LR0Parser):
    def build_action_table(self):
        action_table = {}
        follow = self.compute_follow()

        for state_idx, state in enumerate(self.states):
            for item in state:
                if item.is_reduce_item():
                    if item.production[0] == self.grammar.start_symbol + "'":
                        action_table[(state_idx, '$')] = ('accept',)
                    else:
                        for terminal in follow[item.production[0]]:
                            action_key = (state_idx, terminal)
                            if action_key in action_table:
                                raise ValueError("Grammar is not SLR(1)")
                            action_table[action_key] = ('reduce', item.production)
                else:
                    next_sym = item.next_symbol()
                    if next_sym in self.grammar.terminals:
                        goto_key = (state_idx, next_sym)
                        if goto_key in self.goto_table:
                            action_table[goto_key] = ('shift', self.goto_table[goto_key])

        return action_table

    def compute_follow(self):
        follow = {nt: set() for nt in self.grammar.non_terminals}
        follow[self.grammar.start_symbol].add('$')

        first = self.compute_first()

        changed = True
        while changed:
            changed = False
            for nt in self.grammar.non_terminals:
                for prod in self.grammar.productions:
                    rhs = prod[1]
                    for i, symbol in enumerate(rhs):
                        if symbol == nt:
                            next_pos = i + 1
                            while next_pos < len(rhs):
                                next_symbol = rhs[next_pos]
                                if next_symbol in self.grammar.terminals:
                                    if next_symbol not in follow[nt]:
                                        follow[nt].add(next_symbol)
                                        changed = True
                                    break
                                else:
                                    added = len(follow[nt])
                                    follow[nt].update(first[next_symbol] - {'ε'})
                                    if added != len(follow[nt]):
                                        changed = True
                                    if 'ε' not in first[next_symbol]:
                                        break
                                    next_pos += 1
                            else:
                                added = len(follow[nt])
                                follow[nt].update(follow[prod[0]])
                                if added != len(follow[nt]):
                                    changed = True
        return follow

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