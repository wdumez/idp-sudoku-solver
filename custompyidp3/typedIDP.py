from functools import reduce
from custompyidp3.idp_py_syntax import parse_formula
from custompyidp3.idpobjects import *

IDP_LOCATION = "~/idp/usr/local/bin/idp"  # The path to your idp installation.


class Block(object):
    """
    An abstract superclass for the editable blocks.
    Should never be explicitly instantiated, but there's no elegant way to
    enforce abstraction in python3.
    These editable blocks consist of:
    * Theory;
    * Structure;
    * Vocabulary;
    * Term.

    There is no Main block, see further.

    :raises NotImplementedError: some of the methods need to be implemented
        by the subclass.
    """

    def __init__(self, name):
        """
        Initialize the name of the Block (Example: Vocabulary "V")

        :param name: the name of the Block
        :type name: str
        """
        self.name = name

    def show(self, objects=None):
        """
        Function to fully generate a Block in IDP-interpretable string.
        Every block consists of a header, a begin section, a section containing
        objects, and an end.

        The only Block without an 'objects' variable is the Term block.

        :param objects: TODO
        :type objects: TODO
        :returns: the block in IDP-form.
        :rtype: str
        """
        if (objects is None):
            return self.header() + self.begin() + self.content() + self.end()
        return self.header() + self.begin() + self.content(objects) \
            + self.end()

    def begin(self):
        """
        Generates the beginning of a Blockstring.
        This is just an opening bracket and enter for all blocktypes.

        :returns: the begin of a block in IDP-form.
        :rtype: str
        """
        return " {\n"

    def method(self):
        """
        :returns: todo
        :rtype: str
        """
        return "in_" + self.__class__.__name__.lower()

    def content(self, objects):
        """
        Creates the actual content of the block, based on what it contains.

        :param objects: TODO
        :type objects: TODO
        :returns: the content of the objects in IDP-form.
        :rtype: str
        """
        def types_first(x):
            return (1 if isinstance(x, IDPType) else 2)

        def content_for(x):
            m = getattr(x, self.method())
            return m()
        return "\n".join(map(content_for, sorted(objects, key=types_first)))

    def end(self):
        """
        The ending of a Blockstring.
        This is the same for all the blocktypes.
        Consists of a closing bracket and a couple of enters.

        :returns: the ending of a block in IDP-form.
        :rtype: str
        """
        return "\n} \n"

    def header(self):
        """
        The default header raises an error if it isn't overwritten.

        :raises NotImplementedError: if it's not overwritten.
        """
        raise NotImplementedError("Abstract method")


class Theory(Block):
    """
    A class for the Theory block, which is a subclass of Block.
    It changes the voc-attribute, and overwrites the header.

    :inherits Block:
    """

    def __init__(self, name, voc):
        """
        Set the name of the Theory (e.g. 'T'),
        and the name of the Vocabulary (e.g. 'V') it uses.
        These are both needed to form the header.

        :param name: the name of the Theory
        :param voc: the name of the Vocabulary
        :returns: str
        """
        super(Theory, self).__init__(name)
        self.voc = voc

    def header(self):
        """
        The specific header for a Theory,
        the only variables are the Theoryname and the Vocabularyname.

        For Theory T and Vocabulary V, the string looks like:
            'theory T: V '

        :returns: the header of the Theory, in IDP-form.
        :rtype: str
        """
        return "theory " + self.name + " : " + self.voc


class Structure(Block):
    """
    A class for the Structure block, which is a subclass of Block.
    It adds the voc-attribute, and overwrites the header.

    :inherits Block:
    """

    def __init__(self, name, voc):
        """
        Initialize the name of the Structure (e.g. 'S'),
        and set the name of the Vocabulary (e.g. 'V).

        :param name: the name of the Structure
        :type name: str
        :param voc: the name of the Vocabulary
        :type voc: str
        """
        super(Structure, self).__init__(name)
        self.voc = voc

    def header(self):
        """
        Generates the specific header for a Structure.

        :returns: the header, in IDP-form.
        :rtype: str
        """

        return "structure " + self.name + " : " + self.voc


class Vocabulary(Block):
    """
    A class for the Vocabulary block, which is a subclass of Block.
    It overwrites the header.
    Uses Block's __init__ method.
    """

    def header(self):
        """
        Generates the specific header for a Vocabulary.

        :returns: the header, in IDP-form.
        :rtype: str
        """
        return "vocabulary " + self.name


class Term(Block):
    """
    A class for the Term block, which is a subclass of Block.
    It adds a term attribute,
    (a string containing the content of the Term block)
    and overwrites the header and the content methods.
    """

    def __init__(self, term, voc='V'):
        """
        Initializes the Term. It sets the Block name as 't',
        the Vocabularyname as 'V' and the term as parameter term.

        :param term: the term already in IDP format
        :type term: string
        :param voc: (optional) the name of the voc, defaults to 'V'
        :type voc: str
        """
        super(Term, self).__init__('t')  # Term is always called t.
        self.term = term
        self.vocname = voc

    def header(self):
        """
        The specific header for a Term.

        :returns: the Termblock turned into IDP format
        :rtype: str
        """
        return "term " + self.name + " : " + self.vocname

    def content(self):
        """
        Term has a specific content,
        which is just the self.term (cause it's already in IDP format).
        This is between two linefeeds.

        :returns: the termcontent as it was initialized (self.term)
        :rtype: str
        """
        return "\n"+self.term+"\n"


def subclasses(cls):
    """
    TODO: describe
    """
    return reduce(lambda x, y: x + y, [subclasses(x) + [x] for x in
                                       cls.__subclasses__()], [])


class IDP(object):
    """
    A class containing everything needed to 'use' the IDP system.
    It allows adding and removing new constraints, functions, relations, ...
    which it can then convert into a usable IDP script.
    This script can be piped into the idp executable,
    whose path is supplied in the init.
    The output can then be decoded and turned back into
    Pythonic data structures. This allows for a full interface in Python,
    and theoretically no much knowledge of IDP is needed.
    Although, it is possible (and in my opinion preferred) to supply most
    of the idpobjects already in IDP format, which requires IDP knowledges but
    removes the danger of converting Python to IDP.
    """

    def __init__(self, executable=IDP_LOCATION):
        """
        Initializes an IDP object.

        :param executable: path to the IDP executables, defaults to
        IDP_LOCATION
        :type executable: str
        """
        # Init a bunch of dictionary variables.
        self.__dict__['executable'] = executable
        self.__dict__['idpobjects'] = {}
        self.__dict__['wanted'] = []
        self.__dict__['object_names'] = {}
        self.__dict__['cache'] = None
        self.__dict__['dirty'] = True
        self.init_options()

    def init_options(self):
        """
        This method initialises all the options.
        They all start as None-values (safe for xsb and nbrmodels)
        """
        self._options_dict = {"verbosity_grounding": None,
                              "verbosity_solving": None,
                              "verbosity_propagation": None,
                              "verbosity_symmetrybreaking": None,
                              "verbosity_approxdef": None,
                              "verbosity_functiondetection": None,
                              "verbosity_calculatedefinitions": None,
                              "nbmodels": 1,
                              "trace": None,
                              "cpsupport": None,
                              "cpgroundatoms": None,
                              "functiondetection": None,
                              "skolemize": None,
                              "tseitindelay": None,
                              "satdelay": None,
                              "symmetrybreaking": None,
                              "groundwithbounds": None,
                              "longestbrang": None,
                              "nrpropsteps": None,
                              "relativepropsteps": None,
                              "language": None,
                              "longnames": None,
                              "provercommand": None,
                              "proversupportsTFA": None,
                              "assumeconsiostentinput": None,
                              "xsb": "true",
                              "timeout": None,
                              "memoryout": None,
                              "mxtimeout": None,
                              "mxmemoryout": None,
                              "seed": None,
                              "approxdef": None,
                              "randomvaluechoice": None}

    @staticmethod
    def split_pred_name(pred_name):
        """
        Static method to split a predicate.
        Splits a predicate in two parts: the name of the predicate, and the
        type it holds.

        :example:
            Foo(bar,baz)
            would be split in "Foo" and "[bar, baz]"

        """
        pred_name = pred_name.strip()
        if not pred_name.endswith(")"):  # in the case of a Constant
            pred_name += "()"
        name, args = pred_name.split("(")
        arglist = args.strip(')').split(",")
        return name, arglist

    @staticmethod
    def split_func_name(func_name):
        """
        Static method to split a function.
        Splits a Function name into two parts: the function, and the Type it
        maps on (the return_type).

        :example:

            Foo(bar): baz
            would be split in "Foo(bar)" and "baz".

        """
        try:
            func, return_type = func_name.split(":")
            name, arglist = IDP.split_pred_name(func)
            return name, arglist, return_type.strip()
        except ValueError:
            # When making a constant with no return_type.
            return func_name, None, None

    def Predicate(self, typed_name, enumeration=None, ct=False):
        """
        Adds a predicate.
        It can either be empty, or already (partially) filled.

        :param typed_name: name of the predicate in IDP format
        :type typed_name: str
        :param enumeration: an x-dimensional array containing the data.
        :param ct: boolean to indicate whether the enumeration denotes only certainly true tuples.
        x needs to equal to the amount of variables there are in the
        IDP formatted predicate
        :type enumeration: list of str, int, float, ...
        :returns: the Predicate in a datastructure
        :rtype: IDPEnumeratedPredicate or IDPUnknownPredicate

        Example::
            Predicate("IconicDuo(Character,Character)", [["Harry","Sally"],
            ["Bonny","Clyde"]]
        would result in::
            "IconicDuo(Charachter,Character) = {(Harry,Sally); (Bonny,Clyde)}"
        """

        name, arglist = self.split_pred_name(typed_name)
        if enumeration is not None:
            # Predicate with value.
            res = IDPEnumeratedPredicate(self, name, arglist, enumeration, ct)
        else:
            # Empty predicate.
            res = IDPUnknownPredicate(self, name, arglist)
        self.know(res)

    def Type(self, name, enumeration, constructed_from=False, isa=None):
        """
        Adds a type. The type can be int or stringbased.
        The enumeration needs to be supplied as a list, or a tuple.
        As for right now, string should be supplied with extra quotation marks.

        The int can be supplied as a list of ints or as a tuple of ints.
        A tuple can be used to set a range of values, and will be translated as
        such.

        :example:

            Type(Example, (0,10)) -> Example = {0..10}
            Type(Example, list(range(0,10))) -> Example = (0, 1, 2, 3, 4, 5, 6,
            7, 8, 9, 10}

        :param name: the name of the Type
        :param enumeration: a one-dimensional list containing all possible
        values of the Type.
        :param constructed_from: allows the Type to have 'constructed_from'.
        TODO: Add this!
        :type name: str
        :type enumeration: list of int, string, float, ...
        :type constructed_from: list of int, string, float, ...
        :returns: IDPIntType or IDPType object

        """
        if isa is True:
            if __debug__:
                print("ISA made")
            res = IDPSpecialType(self, name, enumeration)
        elif constructed_from is True:
            res = IDPConstructedType(self, name, enumeration)
        elif isinstance(enumeration, tuple) and len(enumeration) == 2:
            range_str = "{}..{}".format(enumeration[0], enumeration[1])
            if all([isinstance(x, float) for x in enumeration]):
                res = IDPFloatRangeType(self, name, range_str)
            else:
                res = IDPIntRangeType(self, name, range_str)

        elif len(enumeration) > 0 and all([isinstance(x, float) for x in
                                          enumeration]):
            res = IDPFloatType(self, name, enumeration)
        elif len(enumeration) > 0 and all([isinstance(x, int) for x in
                                          enumeration]):
            res = IDPIntType(self, name, enumeration)
        else:
            res = IDPType(self, name, enumeration)
        return self.know(res)

    # There's 2 types of constraints: the ones that are already in IDP format,
    # and the ones that aren't
    def Constraint(self, formula, already_IDP=False):
        """
        Adds a constraint.
        There are two types of constraint:
            1. Constraints with formula in the Python form;
            2. Constraints with formula in the IDP form.

        In the second case, the formula doesn't need to be parsed
        into the IDP form. This is a 'safer' way of programming,
        but it requires more knowledge of the IDP system.
        In the first case, the Python form needs to be parsed into
        the IDP form. This is done by passing it on to the
        parse_formula function.

        :param formula: the formula in either Python or IDP form
        :param already_IDP: a bool to flag what form the formula is in
        :type formula: str
        :type already_IDP: bool
        :returns: an IDP object
        :rtype: IDPConstraint

        """
        idp_formula = formula if already_IDP else parse_formula(formula)
        res = IDPConstraint(self, idp_formula)
        return self.know(res)

    def Function(self, typed_name, enumeration=None, partial=False):
        """
        Adds a function. This function is either:
            * Empty;
            * Completely filled;
            * Partial (not advised).

        :param typed_name: the name of the function, in IDP format
        :param enumeration: dictionary containing the values of the function
        :param partial: flag to make partial function (not advised)
        :type typed_name: str
        :type enumeration: dictionary
        :partial: bool
        :returns: an IDPEnumeratedFunction or IDPUnkownFunction object

        Example:

            Function("Weight(Penalty): Number", [penalty1:5, penalty2:15, penalty3:30])
        would be formatted to:

            Weight(Penalty) = {penalty1->5, penalty2->15, penalty3->30}

        """
        func, arg_list, return_type = self.split_func_name(typed_name)
        if arg_list is None and return_type is None:
            res = IDPEmptyConstantFunction(self, func, arg_list, return_type,
                                           partial=partial)
        elif isinstance(enumeration, str) or isinstance(enumeration, int):
            res = IDPValueConstantFunction(self, func, arg_list, return_type,
                                           enumeration, partial=partial)
        elif enumeration is not None:
            res = IDPEnumeratedFunction(self, func, arg_list, return_type,
                                        enumeration, partial=partial)
        else:
            res = IDPUnknownFunction(self, func, arg_list, return_type,
                                     partial=partial, ct=False)
        return self.know(res)

    def Constant(self, typed_name, enumeration=None):
        """
        Adds a constant.

        :param typed_name: the name of the constant, in IDP format.
        :param enumeration: this is currently not used. TODO: FIX!
        :type typed_name: str
        :param enumeration: list of values
        :returns: the constant itself
        :rtype: Function
        """
        # if enumeration != None:
        #     enum2 = { (): enumarion }
        # return self.Function(typed_name, enum2)
        return self.Function(typed_name, enumeration)

    def GeneratedFunction(self, typed_name, impl):
        """
        TODO: Document this! >:(
        """
        func, arg_list, return_type = self.split_func_name(typed_name)
        res = IDPGeneratedFunction(self, func, arg_list, return_type, impl)
        return self.know(res)

    def GeneratedPartialFunction(self, typed_name, impl):
        """
        TODO: Document this! >:(
        """
        func, arg_list, return_type = self.split_func_name(typed_name)
        res = IDPGeneratedPartialFunction(self, func, arg_list, return_type,
                                          impl)
        return self.know(res)

    def Define(self, *args):
        """
        Method to make a definition.
        It can be called as "Define(Head,Body)" for a definition with only one
        rule, or it could be called as "Define([(H1,B1), (H2,B2), ...])" for
        definitions with multiple rules.
        As last argument, a "already_idp" flag could be passed.
        This function is a bit experimental, best to format it as IDP and use
        the 'already_idp' flag.

        :param head: the head of the rule
        :param body: the body of the rule
        :param already_idp: flag of whether it's in the correct form or not
        :type head: str
        :type body: str
        type already_idp: bool

        OR

        :param list: tuples of heads and bodies
        :type list: list of tuples
        :returns: the definition in IDP form
        :rtype: IDPDefinition
        """
        already_idp = isinstance(args[-1], bool)
        if (already_idp):
            self.append(IDPDefinition(self, [args[0]]))
            return
        if len(args) == 2:  # Called as "Define(Head,Body)"
            args = [tuple(args)]
        elif len(args) == 1:  # Called as "Define([(H1,B1)...])"
            args = args[0]
        rules = []
        for (head, body) in args:
            if not head.endswith(")"):
                head = head = "()"
            idp_form = body if already_idp else parse_formula(body)
            pred, types = head.split("(")
            types = types.rstrip(")").split(",")
            self.Predicate(pred + "(" + ','.join(types) + ")")
            idp_form = parse_formula(body)
            rules.append(IDPRuleStr(self, pred + idp_form))
        self.append(IDPDefinition(self, rules))

    # Format the contents of one of our IDPObjects to a str for IDP
    def for_idp(self, thing):
        if isinstance(thing, str):
            return "\"{:s}\"".format(thing)
        return str(thing)

    def assign_name(self, object_):
        if isinstance(object_, (int, str, bool, float)):  # Primitive type
            return object_
        name = "o" + str(id(object_))
        self.object_names[name] = object_
        return name

    # Normal forms for everything that comes from the Python world
    # to an IDPObject.
    def normal_form(self, tup):
        if isinstance(tup, tuple):
            if len(tup) == 1:
                return self.normal_form(tup[0])
            else:
                return tuple(map(self.normal_form, tup))
        return self.assign_name(tup)

    def normal_form_enumeration(self, enum):
        if isinstance(enum, dict):
            return {self.normal_form(x): self.normal_form(enum[x]) for x in enum}
        else:
            return [self.normal_form(x) for x in enum]

    def object_for_name(self, name):
        return self.object_names[name]

    # Adds objects into the idpobjects dictionary.
    # Objects can't share the same name.
    # If it's an IDPUnknownObject, also add it to the wanted list.
    def append(self, p):
        """
        Adds objects into the idpobjecst dictionary. These objects are:
            * IDPPredicate, IDPUnknownPredicate
            * IDPType, IDPInt
            * IDPUnknownFunction, IDPEnumeratedFunction
            * Function
            * IDPGeneratedFunction
            * IDPGeneratedPartialFunction
            * IDPDefinition

        :param p: one of the above listed objects
        :type p: see above
        """
        if isinstance(p, IDPUnknownObject) or isinstance(p, IDPEnumeratedPredicate):
            self.wanted.append(p)
        try:
            name = p.name
        except AttributeError:
            name = id(p)
        self.idpobjects[name] = p
        self.dirty = True

    def know(self, p):
        """
        Adds objects into the idpobject dictionary, and returns the object.
        These objects are:
            * IDPPredicate, IDPUnknownPredicate
            * IDPType, IDPInt
            * IDPUnknownFunction, IDPEnumeratedFunction
            * Function
            * IDPGeneratedFunction
            * IDPGeneratedPartialFunction
            * IDPDefinition

        :param p: one of the above listed objects
        :type p: see above
        :returns: the object which was added to the dictionary
        """
        self.append(p)
        return p

    def forget(self, old):
        """
        Delete an object from the idpobjects dictionary,
        and also from the wanted list if it was found there.

        :param old: the idpobject to remove
        :type old: an idpobject
        """
        del self.idpobjects[old.name]
        if old in self.wanted:
            self.wanted.remove(old)

    # Switch an old class for a new one.
    def renew(self, old, new):
        old_class = old.__class__
        old_tn = old.typedName()
        self.know(old_class(old.typedName, new))

    def __str__(self):
        """
        The __str__ magic method will convert the Theory, Structure and
        Vocabulary Blocks into IDP format.
        By adding a Main afterwards (and optionally a Term), we can create a
        full IDP script. See the modelexpand_script method for an example.

        :returns: The 3 main blocks string-ified in IDP format.
        :rtype: str
        """
        # This will join all the blocks in the self.blocks list with "\n"
        return "\n".join([bl.show(list(self.idpobjects.values())) for bl
                          in self.blocks])

    def modelexpand_script(self):
        """
        Generates the IDP-ready script for basic modelgeneration.
        Works by adding a Main block to all the other blocks.
        More specifically: a Main block containing the 'generate' IDP function.

        :returns: A fullfledged IDP-readable script for modelgeneration.
        :rtype: str
        """
        mainblock_expand_models = ("allsols = modelexpand(T,S)\n"
                                   "print(allsols[1])\n")
        for i in range(2, self._options_dict['nbmodels']+1):
            mainblock_expand_models += "print('next:')\n" + \
                "print(allsols[{:d}])\n".format(i)
        return str(self) + "\n" + IDP.mainblock_start + \
            self.generate_options() + mainblock_expand_models + "}\n"

    def minimize_script(self, termblock):
        """
        Generates the script for basic minimization of a term.
        Works by adding a Term and a Main block to the other blocks.
        More specifically: a Main block containing the 'minimize' function.
        The Term block needs to be called 't' and needs to use Vocabulary 'V'
        for it to work. By default a voc is always called V, so this is no
        problem.

        :returns: A script readable by IDP for term minimization.
        :rtype: str
        """
        mainblock_minimize_models = ("allsols = minimize(T,S,t)\n"
                                     "print(allsols[1])\n")
        for i in range(2, self._options_dict['nbmodels']+1):
            mainblock_minimize_models += "print('next:')\n" + \
                "print(allsols[{:d}])\n".format(i)

        return str(self) + "\n" + termblock.show() + "\n" + \
            IDP.mainblock_start + self.generate_options() + \
            mainblock_minimize_models + "\n}"

    def customScript(self, main, term=""):
        """
        Generates a .idp file with a custom main.
        Works by adding a custom Mainblock to the other blocks.
        Optionally, a term to minimize can also be added.
        The Term needs to be preformatted Term string.

        :returns: A custom script readable by IDP.
        :rtype: str
        :raises: ValueError when the supplied term isn't str
        """

        if not isinstance(term, str):
            raise ValueError("Term needs to be str!")

        if term != "":
            termblock = Term(term)
            term_str = termblock.show()
        else:
            term_str = term

        return str(self) + "\n" + term_str + "\n" + main + "\n"

    def generate_options(self):
        returnval = ""
        for key, val in self._options_dict.items():
            if val is not None:
                returnval += "    stdoptions.{:s} = {:s}\n".format(key.replace("_", "."),
                                                                   str(val))
        return returnval

    def check_sat_script(self):
        """
        Generates .idp file to check if the model is satisfiable.

        :returns: A script readable by IDP.
        :rtype: str
        """
        return str(self) + "\n" + IDP.mainblock_start + \
            self.generate_options() + IDP.mainblock_check_sat + "\n"

    def fillIn(self, pred):
        if self.dirty:
            self.refresh()
        return self.cache[pred]

    def __setattr__(self, name, val):
        # Creat the options dictionary
        if name == "_options_dict":
            super().__setattr__(name, val)

        # Check if it's an idp object
        if name not in self.idpobjects:
            # If it's not an IDP object, check if it's in __dict__
            if name in self.__dict__:
                # Set the value in dict
                self.__dict__[name] = val
                return  # Internal workings

            # If it's not in __dict__, check if it's in options
            if name in self._options_dict:
                self._options_dict[name] = val
                return
    #   if name not in self.idpobjects:
            # If it's in neither, it doesn't exist
            else:
                raise ValueError("Please declare " + name +
                                 " before assigning to it."
                                 "\nIf you're trying to"
                                 " set an option, check your spelling, or it"
                                 " might not exist. \nCheck the documentation"
                                 " for a list of the supported options.")
        old = getattr(self, name)
        old_class = old.__class__
        old_typ_name = old.typedName()
        self.forget(old)
        if issubclass(old_class, IDPType):
            return self.Type(old_typ_name, val)
        if issubclass(old_class, IDPPredicate):
            return self.Predicate(old_typ_name, val)
        if issubclass(old_class, IDPFunction):
            return self.Function(old_typ_name, val)
        raise ValueError("Failed to update " + str(old))

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError
        name = name.strip()
        try:
            if name == "string":
                return
            return self.idpobjects[name]
        except (KeyError):
            return self._options_dict[name]

    def refresh(self):
        """
        Run the IDPsystem's modelgeneration and read its output.
        Works by piping to input to the IDP executable, and reading the output.
        Once this command has been run, the idp object should have new
        attributes in the same name of the constants/functions/relations/...,
        which should be readable in Python.

        For example, a function called 'Group' should now be accessible by
        fetching the 'Group' attribute of the IDP object.
        :Example:

        grouparray = IDP.Group

        """
        from subprocess import Popen, PIPE, STDOUT
        import os
        if __debug__:
            print("SENT TO IDP:")
            print(self.modelexpand_script())
            print("END OF IDP INPUT")
            f = open('IDPscript.idp', 'w')
            f.write(self.modelexpand_script())
            f.close()
            print("SENT TO IDP:")
        idp = Popen(self.executable, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        # input is the generated idp file
        out, err = idp.communicate(input=(self.modelexpand_script()).encode())
        out = out.decode()
        err = err.decode()  # python3: communicate only works with byte objects
        if err and __debug__:
            print("IDP Error Message:")
            print(err)
        if __debug__:
            print("GOT OUTPUT:")
            print(out)
            print("END OF IDP OUTPUT")
        out = out.split("next:")
        from custompyidp3.idp_parse_out import idp_parse
        sol_list = []
        for model in out:
            if model.strip() == "nil":
                if __debug__:
                    print("UNSATISFIABLE!")
                solution = {'satisfiable': False}
            else:
                if __debug__:
                    print("SATISFIABLE")
                solution = idp_parse(model, [x.name for x in self.wanted])
                solution['satisfiable'] = True
            self.dirty = False
            sol_list.append(solution)
        return sol_list

    def model_expand(self):
        return self.refresh()

    def printunsatcore(self, timeout: int = 0):
        """Call printunsatcore on the IDP object and return the unsat core.
        The call will end early after `timeout` seconds
        (default: 0 = no timeout).
        """
        import subprocess as sp
        main_block = 'procedure main() { ' +\
            f'stdoptions.timeout = {timeout} ' +\
            'printunsatcore(T,S,V)' +\
            '}'
        script = self.customScript(main_block)
        process = sp.Popen([self.executable],
                           stdin=sp.PIPE,
                           stdout=sp.PIPE,
                           stderr=sp.PIPE)
        out, dummy_err = process.communicate(input=script.encode())
        core = out.decode().strip()
        return core

    def minimize(self, term, ssh=False, remote_idp_location=None,
                 known_hosts_location=None, address=None, username=None,
                 password=None):
        """
        Run the IDPsystem's minimize and read its output.
        Works by piping to input to the IDP executable, and reading the output.
        Once this command has been run, the idp object should have new
        attributes in the same name of the constants/functions/relations/...,
        which should be readable in Python.

        For example, a function called 'Group' should now be accessible by
        fetching the 'Group' attribute of the IDP object.

        :param term: the content of the term block, in IDP-form
        :type term: str
        :param ssh: Can be used to run IDP over SSH
        :type term: bool

        """
        from subprocess import Popen, PIPE, STDOUT, check_output
        import os

        termblock = Term(term)  # create a termblock, to minimize term
        script = self.minimize_script(termblock)

        if __debug__:
            # write it to a file if debug
            f = open('IDPscript.idp', 'w')
            f.write(script)
            f.close()
            print("SENT TO IDP:")
            print(script)
            print("END OF IDP INPUT")
        if not ssh:
            idp = Popen(self.executable, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            out, err = idp.communicate(input=str(script).encode())
            out = out.decode()  # python3: communicate only works with byte objects
            err = err.decode()
        else:
            from custompyidp3.communicator import communicator
            print("USING COMMUNICATOR")
            comm = communicator()
            comm.remote_idp_location = remote_idp_location
            comm.known_hosts_location = known_hosts_location
            comm.address = address
            comm.username = username
            comm.password = password
            out = comm.communicate()
            if not out:
                return
            err = ""
        if err and __debug__:
            print("IDP Error Message:")
            print(err)
        if __debug__:
            print("GOT OUTPUT:")
            print(out)
            print("END OF IDP OUTPUT")
        from custompyidp3.idp_parse_out import idp_parse
        sol_list = []
        out = out.split("next:")
        for model in out:
            if model.strip() == "nil":
                if __debug__:
                    print("UNSATISFIABLE!")
                solution = {'satisfiable': False}
            else:
                solution = idp_parse(model, [x.name for x in self.wanted])
                solution['satisfiable'] = True
            self.dirty = False
            sol_list.append(solution)
        return sol_list

    def check_sat(self):
        """
        Checks the satisfiability of the current IDP system.
        """
        from subprocess import Popen, PIPE, STDOUT
        import os
        script = str(self)

        if __debug__:
            print("CHECK SAT:")
            print(script)
            print("END OF CHECK SAT")

        idp = Popen(self.executable, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = idp.communicate(input=self.check_sat_script().encode())
        out = out.decode()
        err = err.decode()

        if __debug__:
            print(("err:" + err))
            print(("out:" + out))
        #  Check wether the output is true or false
        if out.find("true") != -1:
            return True
        else:
            return False

    mainblock_start = "procedure main(){\n"

    # a constant string to define a mainblock which checks SAT
    mainblock_check_sat = """
    print(sat(T,S))
    }"""

    fill_in_pred = """procedure main(){
    stdoptions.nbmodels = 1
    allsols = modelexpand(T,S)
    if #allsols ~= 1 then
    print("something is terribly wrong")
    else
    print(allsols[1])
    end
        }"""

    # an array containing all the blocks and their names
    blocks = [Vocabulary("V"), Theory("T", "V"), Structure("S", "V")]

    def Property(self, typing):
        f = self.Function(typing)
        return property(lambda x: f[x])

    def PartialProperty(self, typing):
        f = self.Function(typing, partial=True)

        def upd(self, tar):
            f[self] = tar
        return property(lambda x: f[x], upd)

    def KnownProperty(self, typing):
        f = self.Function(typing, dict(), partial=True)

        def upd(self, tar):
            f[self] = tar
        return property(lambda x: f[x], upd)

    # def compare(self, enum1, enum2):
    #     template = "{0:14}|{1:14}|{2:14}"
    #     print(template.format("key", "enum1", "enum2"))
    #     print("-------------------------------------")
    #     ding = set(enum1.items()) - set(enum2.items())
    #     for tup in ding:
    #         key = tup[0]
    #         print(template.format(str(key), str(enum1[key]),
    #                               str(enum2[key])))
    #     return

    def compare(self, *args):
        if len(args) == 1:
            args = args[0]
        header = "{0:14}".format("key")
        keylist = {}
        for i, enum1 in enumerate(args):
            print(enum1)
            header += "|{0:14}".format("enum" + str(i+1))
            for j, enum2 in enumerate(args):
                if j < i:
                    pass
                    diff = set(enum1.items()) - set(enum2.items())
                    print(diff)
                    for tup in diff:
                        keylist[tup[0]] = []

        print(header)
        for key in keylist:
            line = "{0:14}".format(key)
            for i, enum in enumerate(args):
                keylist[key].append(enum[key])
                line += "|{0:14}".format(enum[key])
            print(line)
        return keylist


def type(idp):
    def foo(cls):
        clsname = cls.__name__
        for name, method in cls.__dict__.items():
            if hasattr(method, "_idp_return_type"):
                rt = getattr(method, "_idp_return_type")
                if isinstance(rt, str):
                    rt_name = rt
                else:
                    rt_name = rt.__name__
                typed_name = name + "(" + clsname + ")" + " : " + rt_name
                if hasattr(method, "_partial"):
                    idp.GeneratedPartialFunction(typed_name, method)
                else:
                    idp.GeneratedFunction(typed_name, method)

        class Sub(cls):
            def __init__(self, *args, **kw):
                super(Sub, self).__init__(*args, **kw)
                type_ = getattr(idp, clsname)
                type_.add(idp.assign_name(self))
        Sub.__name__ = clsname + "!"
        Sub.__module__ = cls.__module__
        idp.Type(cls.__name__, set([]))
        return Sub
    return foo


def function_to(target):
    def wrapper(func):
        func._idp_return_type = target
        return func
    return wrapper


def partial_function_to(target):
    def wrapper(func):
        func._idp_return_type = target
        func._partial = True
        return func
    return wrapper


def idp_property(typing):
    return property(lambda x: x)
