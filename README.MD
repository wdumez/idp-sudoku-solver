# Explaining Sudokus using a Knowledge Base System

This repository contains the source code written during my Master's Thesis.

The `detailed-zebratutor-explanations` folder contains the full explanations
for the explanations which were partially shown in the thesis for the
Detailed ZebraTutor method.

The file `requirements.txt` contains the required modules to
run this application using Python 3.10. You can install these
with `python -m pip install -r requirements.txt`.

This code assumes you have the IDP executable located at `~/idp/usr/local/bin/idp`. If this is not the case, you should update the constructor of `SudokuKB` to point to the correct location instead.

For info on running the solver and explainer, use:

`python run_solver.py --help`
and
`python run_explainer.py ---help`
