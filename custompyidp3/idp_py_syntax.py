# idp_py_syntax
import ast


def flatten(l, ltypes=(list, tuple)):
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)


class Formula(object):
    pass


def tuple_to_atom(tup):
    try:
        typing = tup[1] + "(" + ", ".join(map(str, tup[0])) + ")"
    except TypeError:
        typing = tup[1] + "(" + tup[0] + ")"
    if len(tup) >= 3 and len(tup[2]) >= 1:
        ifs = " & ".join(map(str, tup[2]))
        return typing + " & " + ifs
    else:
        return typing


class DefRule(Formula):

    def __init__(self, args, body):
        self.args = args
        self.body = body

    def __str__(self):
        return "(" + ", ".join(self.args) + ")" + " <- " + str(self.body) + "."


class AggregateFormula(Formula):

    def __init__(self, agg, vars, formula):
        self.agg = agg
        self.vars = vars
        self.formula = formula

    def __str__(self):
        var_tuple = flatten([x[0] for x in self.vars])
        it = (" ".join(var_tuple) + ": " +
              " & ".join(map(tuple_to_atom, self.vars)))
        if self.agg == "card":
            return self.agg + "{" + it + " }"
        return self.agg + "{" + it + " : " + str(self.formula) + "}"


class ArithmeticFormula(Formula):

    def __init__(self, symbol, children):
        self.symbol = symbol
        self.children = children

    def __str__(self):
        def add_pars(x):
            symbols = "+-*%/^"
            return "(" + x + ")" if any([(s in x) for s in symbols]) else x
        if self.symbol == "/":
            (l, r) = [add_pars(str(x)) for x in self.children]
            return "(" + l + "-" + l + "%" + r + ") / " + r
        else:
            return (" " + self.symbol + " ").join([add_pars(str(x)) for x in self.children])


class BooleanFormula(Formula):

    def __init__(self, symbol, children):
        self.symbol = symbol
        self.children = children

    def __str__(self):
        return (" " + self.symbol + " ").join(["(" + str(x) + ")" for x in self.children])


class UnaryFormula(Formula):

    def __init__(self, symb, child):
        self.child = child
        self.symb = symb

    def __str__(self):
        return self.symb + "(" + str(self.child) + ")"


class QuantifiedFormula(Formula):

    def __init__(self, kind, vars, formula):
        self.kind = kind
        self.vars = vars
        self.formula = formula

    def guard_sym(self):
        if self.kind == "!":
            return "=>"
        if self.kind == "?":
            return "&"

    def __str__(self):
        var_tuple = flatten([x[0] for x in self.vars])
        return (self.kind + " " + " ".join(var_tuple) + ": " +
                " & ".join(map(tuple_to_atom, self.vars)) +
                self.guard_sym() + " " + str(self.formula))


class Comparison(Formula):

    def __init__(self, symb, left, right):
        self.symb = symb
        self.left = left
        self.right = right

    def __str__(self):
        return str(self.left) + " " + self.symb + " " + str(self.right)


class FormulaBuilder(ast.NodeVisitor):

    def __init__(self):
        pass

    def generic_visit(self, node):
        result = flatten([self.visit(child)
                         for child in ast.iter_child_nodes(node)])
        return result

    def visit_BinOp(self, node):
        symb = self.visit(node.op)
        return ArithmeticFormula(symb, [self.visit(node.left), self.visit(node.right)])

    def visit_BoolOp(self, node):
        symb = self.visit(node.op)
        return BooleanFormula(symb, [self.visit(child) for child in node.values])

    def visit_Add(self, node): return "+"
    def visit_Sub(self, node): return "-"
    def visit_Mult(self, node): return "*"
    def visit_Div(self, node): return "/"
    def visit_Mod(self, node): return "%"
    def visit_Pow(self, node): return "^"

    def visit_Num(self, node):
        return str(node.n)

    def visit_And(self, node):
        return "&"

    def visit_Or(self, node):
        return "|"

    def visit_Not(self, node):
        return "~"

    def visit_Eq(self, node):
        return "="

    def visit_NotEq(self, node):
        return "~="

    def visit_Lt(self, node):
        return "<"

    def visit_Gt(self, node):
        return ">"

    def visit_LtE(self, node):
        return "=<"

    def visit_GtE(self, node):
        return ">="

    def visit_Compare(self, node):
        return Comparison(self.visit(node.ops[0]), self.visit(node.left), self.visit(node.comparators[0]))

    def visit_UnaryOp(self, node):
        symb = self.visit(node.op)
        return UnaryFormula(symb, self.visit(node.operand))

    def visit_Tuple(self, node):
        return tuple([self.visit(x) for x in node.elts])

    def visit_GeneratorExp(self, node):
        return self.visit_ListComp(node)

    def visit_ListComp(self, node):
        return ([(self.visit(gen.target), self.visit(gen.iter), [self.visit(an_if) for an_if in gen.ifs]) for gen in node.generators], self.visit(node.elt))

    def visit_Name(self, node):
        return node.id

    def visit_Lambda(self, node):
        return DefRule(self.visit(node.args), self.visit(node.body))

    def visit_Call(self, node):
        func = self.visit(node.func)
        if func == "any" or func == "all":
            symb = "?" if func == "any" else "!"
            return QuantifiedFormula(symb, *self.visit(node.args[0]))
        aggregates = {'sum': 'sum', 'len': 'card',
                      'product': 'prod', 'max': 'max', 'min': 'min'}
        if func in list(aggregates.keys()):
            return AggregateFormula(aggregates[func], *self.visit(node.args[0]))
        return str(func) + "(" + ", ".join(map(str, [self.visit(arg) for arg in node.args])) + ")"


def parse(string):
    import ast
    p = ast.parse(string)
    return FormulaBuilder().visit(p)[0]


def parse_formula(string):
    result = parse(string)
    return str(result)
