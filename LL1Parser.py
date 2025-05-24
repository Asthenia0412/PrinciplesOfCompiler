
class LL1Parser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.first = self.compute_first()
        self.follow = self.compute_follow()
        self.parse_table = self.build_parse_table()

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

    def compute_follow(self):
        follow = {nt: set() for nt in self.grammar.non_terminals}
        follow[self.grammar.start_symbol].add('$')

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
                                    follow[nt].update(self.first[next_symbol] - {'ε'})
                                    if added != len(follow[nt]):
                                        changed = True
                                    if 'ε' not in self.first[next_symbol]:
                                        break
                                    next_pos += 1
                            else:
                                added = len(follow[nt])
                                follow[nt].update(follow[prod[0]])
                                if added != len(follow[nt]):
                                    changed = True
        return follow

    def build_parse_table(self):
        table = {}
        for nt in self.grammar.non_terminals:
            table[nt] = {}
            for prod in self.grammar.get_productions_for(nt):
                first_alpha = self.compute_string_first(prod[1])
                for terminal in first_alpha - {'ε'}:
                    if terminal in table[nt]:
                        raise ValueError("Grammar is not LL(1)")
                    table[nt][terminal] = prod
                if 'ε' in first_alpha:
                    for terminal in self.follow[nt]:
                        if terminal in table[nt]:
                            raise ValueError("Grammar is not LL(1)")
                        table[nt][terminal] = prod
        return table

    def compute_string_first(self, symbols):
        result = set()
        for symbol in symbols:
            if symbol in self.grammar.terminals:
                result.add(symbol)
                return result
            else:
                result.update(self.first[symbol] - {'ε'})
                if 'ε' not in self.first[symbol]:
                    return result
        result.add('ε')
        return result

    def parse(self, input_tokens):
        input_tokens = input_tokens + ['$']
        stack = ['$', self.grammar.start_symbol]
        pos = 0

        while stack:
            top = stack[-1]
            current_token = input_tokens[pos]

            if top in self.grammar.terminals or top == '$':
                if top == current_token:
                    stack.pop()
                    pos += 1
                else:
                    raise SyntaxError(f"Expected {top}, got {current_token}")
            elif top in self.grammar.non_terminals:
                if current_token in self.parse_table[top]:
                    production = self.parse_table[top][current_token]
                    stack.pop()
                    if production[1] != ['ε']:
                        stack.extend(reversed(production[1]))
                else:
                    raise SyntaxError(f"No production for {top} on {current_token}")
            else:
                raise SyntaxError(f"Invalid symbol {top} on stack")

        if pos != len(input_tokens):
            raise SyntaxError("Input not fully consumed")