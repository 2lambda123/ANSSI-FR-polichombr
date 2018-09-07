"""
    This file is part of Polichombr.

    (c) 2016 ANSSI-FR


    Description:
        AnalyzeIt task implementation.
"""

import os

def remove_blacklist_machoc(functions):
    blacklisted = [0x1a02300e,0xd3fa94a]
    for func in list(functions.keys()):
        if functions[func]["machoc"] in blacklisted:
            functions.pop(func)
    return functions
   

def parse_machoc_signatures(fname):
    """
        Returns a dict containing the functions and the hashes
    """
    # MACHOC report: we load the functions, hashes, etc.
    functions = {}
    if not os.path.exists(fname):
        return functions
    with open(fname) as infile:
        fdata = infile.read()
        items = fdata.split(";")
        for i in items:
            if ":" in i:
                subitems = i.split(":")
                machoc_h = int(subitems[0].strip(), 16)
                address = int(subitems[1].strip(), 16)
                functions[address] = dict(machoc=machoc_h, name="")
        #functions = remove_blacklist_machoc(functions)
        return functions