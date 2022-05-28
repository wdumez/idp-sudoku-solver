"""
This file contains all the IDP objects.
"""

import collections.abc as collections


class IDPObject(object):
    """
    'Abstract' class for all the IDP objects.
    Initialises idp.
    """

    def __init__(self, idp):
        self.idp = idp

    def accept(self, vis):
        return vis.visit(self)

# Vocabulary objects:


class IDPVocabularyObject(IDPObject):
    """
    Abstract class for all the objects that appear in a vocabulary.
    """

    def __eq__(self, other):
        """
        Two objects are equal is they have the same name.
        """
        return self.typedName() == other.typedName()

    def __init__(self, idp, name, typing, ct=False):
        super(IDPVocabularyObject, self).__init__(idp)
        self.name = name
        self.typing = typing
        self.ct = ct

    def in_theory(self):
        """
        Doesn't show up in a theory, so returns empty string.
        """
        return ""

    def in_vocabulary(self):
        return self.typedName()

    def in_structure(self):
        ct_str = '<ct>' if self.ct == True else ''
        return self.name + ct_str + ' = {' + self.show_contents() + '}'

    def typedName(self):
        return self.name + "(" + ", ".join(map(str, self.typing)) + ")"

    def show_tuple(self, tup):
        if isinstance(tup, tuple):
            return ', '.join(map(str, tup))
        # if the tup is already str, we need to encode it to avoid unicode
        # errors. str() would give an error here.
        else:
            return str(tup)

    def show_contents(self):
        return "; ".join([self.show_tuple(x) for x in self])

    def __len__(self):
        return len(self.to_set())

    def __contains__(self, x):
        return self.idp.normal_form(x) in self.to_set()

    def __iter__(self):
        # if (len(self.typing) > 1):
        #     return iter(self.product_of_types())
        # else:
        return iter(self.to_set())

    def product_of_types(self):
        import itertools
        types = [getattr(self.idp, x) for x in self.typing]
        return itertools.product(*types)


class IDPEnumeratedObject(IDPVocabularyObject):

    def __init__(self, idp, name, typing, enum, ct):
        super(IDPEnumeratedObject, self).__init__(idp, name, typing, ct)
        self._enumeration = self.idp.normal_form_enumeration(enum)

    def to_set(self):
        return set(self.enumeration)

    def changed(self):
        self.idp.dirty = True

    @property
    def enumeration(self):
        return self._enumeration

    @enumeration.setter
    def enumeration(self, enum):
        self._enumeration = enum
        self.changed()


class IDPUnknownObject(IDPEnumeratedObject):

    def in_structure(self):
        return ""

    @property
    def enumeration(self):
        self._enumeration = self.idp.fillIn(self.name)
        return self._enumeration


class IDPGeneratedObject(IDPVocabularyObject):

    def __init__(self, *args):
        super(IDPGeneratedObject, self).__init__(*args[:-1])
        self.implementation = args[-1]

    def product_of_types(self):
        import itertools
        types = [getattr(self.idp, x) for x in self.typing]
        return itertools.product(*types)

    @property
    def enumeration(self):
        return self.product_of_types()

    def to_set(self):
        return self.enumeration

# Functions


class IDPFunction(IDPVocabularyObject, collections.Mapping):

    def __init__(self, idp, name, types, return_type, partial=False, ct=False):
        IDPVocabularyObject.__init__(self, idp, name, types)
        self.return_type = return_type
        self.partial = partial

    def show_tuple(self, tup):
        return super(IDPFunction, self).show_tuple(tup) + "->" + self.idp.for_idp(self[tup])

    def typedName(self):
        return ("partial " if self.partial else '') + super(IDPFunction, self).typedName() + " : " + self.return_type

    def __iter__(self):
        sup_it = super(IDPFunction, self).__iter__()
        for x in sup_it:
            if self[x] is not None:
                yield x

    def __call__(self, *args):
        return self[args]


class IDPEnumeratedFunction(IDPFunction, IDPEnumeratedObject, collections.MutableMapping):

    def __init__(self, idp, name, args, rt, enum, partial=False, ct=False):
        IDPFunction.__init__(self, idp, name, args, rt, partial, ct)
        IDPEnumeratedObject.__init__(self, idp, name, args, enum, ct)
        # check for string

    def __setitem__(self, key, value):
        self.enumeration[self.idp.normal_form(
            key)] = self.idp.normal_form(value)
        self.changed()

    def __getitem__(self, key):
        result = self.enumeration[self.idp.normal_form(key)]
        if isinstance(getattr(self.idp, self.return_type), IDPIntType):
            return int(result)
        return result

    def __delitem__(self, key):
        del self.enumeration[self.idp.normal_form(key)]
        self.changed()


class IDPUnknownFunction(IDPEnumeratedFunction, IDPUnknownObject):

    def __init__(self, idp, name, args, rt, partial=False, ct=False):
        super(IDPUnknownFunction, self).__init__(
            idp, name, args, rt, {}, partial, ct)


class IDPEmptyConstantFunction(IDPEnumeratedFunction, IDPUnknownObject):

    def __init__(self, idp, name, args, rt, partial=False):
        super(IDPEmptyConstantFunction, self).__init__(
            idp, name, args, rt, {}, partial)

    def typedName(self):
        return self.name


class IDPValueConstantFunction(IDPEnumeratedFunction, IDPUnknownObject):

    def __init__(self, idp, name, args, rt, enumeration, partial=False):
        self._content = enumeration
        super().__init__(idp, name, args, rt, {}, partial)

    def in_structure(self):
        return self.name + " = " + str(self._content)


class IDPGeneratedFunction(IDPFunction, IDPGeneratedObject):

    def __init__(self, idp, name, args, rt, impl, partial=False):
        IDPFunction.__init__(self, idp, name, args, rt, partial)
        IDPGeneratedObject.__init__(self, idp, name, args, impl)

    def __getitem__(self, key):
        args = list(map(self.idp.object_for_name, key))
        try:
            res = self.implementation(args)
        except AttributeError:
            if len(key) == 1:
                res = self.implementation(args[0])
        return self.idp.normal_form(res)


# class IDPGeneratedPartialFunction(IDPPartialFunction, IDPGeneratedFunction):

#     def __getitem__(self, key):
#         res = super(IDPGeneratedPartialFunction, self).__getitem__(key)
#         if self.idp.assign_name(None) == res:
#             return None
#         else:
#             return res

# Predicates

class IDPPredicate(IDPVocabularyObject, collections.Set):

    def __call__(self, *args):
        return self.idp.normal_form(args) in self


class IDPUnknownPredicate(IDPPredicate, IDPUnknownObject):

    def __init__(self, idp, name, types):
        IDPPredicate.__init__(self, idp, name, types)


class IDPEnumeratedPredicate(IDPPredicate, IDPEnumeratedObject, collections.MutableSet):

    def add(self, x):
        self.enumeration.append(self.idp.normal_form(x))
        self.changed()

    def discard(self, x):
        self.enumeration.discard(x)
        self.changed()


class IDPGeneratedPredicate(IDPPredicate, IDPGeneratedObject):

    pass


class IDPType(IDPEnumeratedPredicate):

    def __init__(self, idp, name, enum, ct=False):
        super(IDPType, self).__init__(idp, name, [], enum, ct)

    def typedName(self):
        return self.name

    def in_vocabulary(self):
        return "type " + self.name

   # def isIntType(self):
    #    x = self.enum[0]
     #   return int(x) == x


class IDPIntType(IDPType):

    def in_vocabulary(self):
        return super(IDPIntType, self).in_vocabulary() + " isa int"


class IDPIntRangeType(IDPIntType):

    def in_vocabulary(self):
        return ("type {} = {{{}}} isa int"
                .format(super(IDPType, self).in_vocabulary(),
                        self.show_contents()))

    def show_contents(self):
        return "".join(self._enumeration)

    def in_structure(self):
        return ""


class IDPFloatType(IDPType):

    def in_vocabulary(self):
        return super(IDPFloatType, self).in_vocabulary() + "isa float"


class IDPFloatRangeType(IDPFloatType):

    def in_vocabulary(self):
        return ("type {} = {{{}}} isa float"
                .format(super(IDPType, self).in_vocabulary(),
                        self.show_contents()))

    def show_contents(self):
        return "".join(self._enumeration)

    def in_structure(self):
        return ""


class IDPConstructedType(IDPType):

    def in_vocabulary(self):
        return super(IDPConstructedType, self).in_vocabulary() +\
            " constructed from {" + self.show_constructed_from() + "}"

    def show_constructed_from(self):
        content = ", ".join(self._enumeration)
        return content

    # No need for anything in struct
    def in_structure(self):
        return ""


class IDPSpecialType(IDPType):

    def in_vocabulary(self):
        return super().in_vocabulary() + " isa " + "".join(self._enumeration)

    # No need for anything in struct
    def in_structure(self):
        return ""

# Theory objects


class IDPTheoryObject(IDPObject):

    def in_structure(self):
        return ""

    def in_vocabulary(self):
        return ""

    def in_theory(self):
        raise NotImplementedError(
            "All theory objects should implement the 'in_theory' method")


class IDPConstraint(IDPTheoryObject):

    def __init__(self, idp, formula):
        super(IDPConstraint, self).__init__(idp)
        self.formula = formula

    def in_theory(self):
        if self.formula[-1] != ".":
            return self.formula + "."
        else:
            return self.formula


class IDPRule(IDPTheoryObject):

    def __init__(self, idp, head_pred, vars_, body):
        super(IDPRule, self).__init__(idp)
        self.head_pred = head_pred
        self.vars = vars_
        self.body = body

    def in_theory(self):
        return "!" + " ".join(self.vars) + ": " + self.head_pred + "(" + (", ").join(self.vars) + ") <- " + self.body + "."


class IDPRuleStr(IDPTheoryObject):

    def __init__(self, idp, string):
        super(IDPRuleStr, self).__init__(idp)
        self.rule = string

    def in_theory(self):
        return self.rule


class IDPDefinition(IDPTheoryObject):

    def __init__(self, idp, rule_list):
        super(IDPDefinition, self).__init__(idp)
        self.rules = []
        for rule in rule_list:
            if isinstance(rule, str):
                self.rules.append(rule)
            else:
                self.rules.append(rule.in_theory())

    def in_theory(self):
        theory_str = "{\n" + "\n".join([x for x in self.rules])
        if theory_str[-1] != ".":
            theory_str += "."
        return theory_str + "\n}"
