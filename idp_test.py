"""https://pyidp3.readthedocs.io/en/latest/examples.html
This is a very simple and small test.
If this test fails, there's something extremely wrong.
It defines 3 variables, that each are either True or False.
"""
from pathlib import Path
from custompyidp3.typedIDP import IDP


HOME = str(Path.home())
idp = IDP(HOME+"/idp/usr/local/bin/idp")
idp.nbmodels = 10
idp.xsb = "true"

idp.Constant("P")
idp.Constant("Q")
idp.Constant("R")
idp.Type('ID', enumeration=(1, 2), isa='int')
idp.Type('Age', enumeration=(1, 5), isa='int')
idp.Function('age(ID) : Age')

idp.Constraint("(P => Q) <=> (P <= R).", True)

# idp.check_sat()
idp.model_expand()

print('Test succeeded.')
