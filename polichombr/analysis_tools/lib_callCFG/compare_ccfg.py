#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    This file is part of Polichombr.

    Organization : EDF-R&D-PERICLES-IRC
    Author : JCO
    Description: Comparaison between callCFG 
    Date : 08/2018
"""

import sqlite3 as lite
import hashlib,os, argparse, collections, copy, hashlib, datetime
from ast import literal_eval

from polichombr.controllers.callCFG import callCFGController, offset_callCFGController
from polichombr import api

from C_CFG import *

class compare_ccfg():
    def __init__(self, sample_id):
    	"""
            Constructor
        """

        self.sample_id = sample_id

        self.ctrl_callCFG = callCFGController()
        self.ctrl_offset_callCFG = offset_callCFGController()

    def _print(self, message):
        """
            Print and log message
        """
        #self.app.logger.info(self.tmessage + message)
        print message


    def compare_tuples(self, tuples_file1, tuples_file2):
        """
            Return A_union_B and A_inter_B
        """
        diff_tuples = []

        tuples_file1 = list(literal_eval(tuples_file1))
        tuples_file2 = list(literal_eval(tuples_file2))

        # Calculate (tuples_file1 U tuples_file2)
        all_tuples = list()
        all_tuples.extend(tuples_file1)
        all_tuples.extend(tuples_file2)
        total_element = len(all_tuples)

        # Get common element
        count = 0
        for tuple_element in tuples_file1:
            if tuple_element in tuples_file2:
                tuples_file2.remove(tuple_element)
                count += 1
            else:
                diff_tuples.append(tuple_element)

        a_union_b = float(total_element-count)  # A_union_B
        a_inter_b = float(count)                # A_inter_B
        return a_inter_b, a_union_b, diff_tuples


    def process_all_comparaison(self):
        """
            Process comparaison with all objects in database
        """

        ccfg_obj1 = self.ctrl_callCFG.get_by_id(self.sample_id)
        if ccfg_obj1 == None:
            return
        all_ccfg_obj = self.ctrl_callCFG.get_all(self.sample_id)

        dict_result = {}

        for ccfg_obj2 in all_ccfg_obj:
            # Cast result into object callCFG_db
            dict_result[ccfg_obj2.sample_id] = self.process_comparaison(ccfg_obj1, ccfg_obj2)

        return dict_result

    def get_png_comparaison(self, sample_id_2):
        """
            Generate compare call-CFG PNG
        """


        ccfg_obj1 = self.ctrl_callCFG.get_by_id(self.sample_id)
        ccfg_obj2 = self.ctrl_callCFG.get_by_id(sample_id_2)
        if ccfg_obj1 == None or ccfg_obj2 == None:
            return

        self.process_comparaison(ccfg_obj1, ccfg_obj2, True)



    def process_comparaison(self, ccfg_obj1, ccfg_obj2, png=False):
        """
            Process comparaison between ccfg_obj1 and ccfg_obj2 parameters
        """
        
        #Calculate difference pourcent with Jaccard Distance 
        a_inter_b, a_union_b, diff_tuples_1 = self.compare_tuples(ccfg_obj1.func_tuples, ccfg_obj2.func_tuples) #Get elements IN file1 and NOT IN file2
        a_inter_b, a_union_b, diff_tuples_2 = self.compare_tuples(ccfg_obj2.func_tuples, ccfg_obj1.func_tuples) #Get elements IN file2 and NOT IN file1

        pourcent =  (a_inter_b / a_union_b) * 100


        #Print result when Jaccard Distance >= 80%
        result_diff = {}
        if pourcent >= 80:
            result_diff = self.get_differences(diff_tuples_1, diff_tuples_2, ccfg_obj1.sample_id, ccfg_obj2.sample_id)

        #Generate new call_CFG with differences
        if png:
            sample_1 = api.get_elem_by_type("sample", ccfg_obj1.sample_id)
            sample_2 = api.get_elem_by_type("sample", ccfg_obj2.sample_id)

            c_cfg_inst = call_CFG(sample_1.storage_file, ccfg_obj1.offset_entrypoint)
            

            tuples_file_2 = sample_2.storage_file, diff_tuples_1, ccfg_obj2.offset_entrypoint
            c_cfg_inst.process_cCFG(tuples_file_2)

        else:
            return pourcent, a_inter_b, a_union_b, result_diff


    def get_differences(self, diff_tuples_1, diff_tuples_2, sample_id_1, sample_id_2):
        """
            Print offset of call's differences between file1 and file2
        """
        
        #Elements IN 'filename1' and NOT IN 'filename2'
        diff_plus = []      
        for value in diff_tuples_1:
            tmp_dict = {}
            id_row = "{0},{1}".format(sample_id_1, value)
            row_inst = self.ctrl_offset_callCFG.get_by_id(id_row)

            if row_inst != None:
                sample_id, machoc1, machoc2 = row_inst.id.split(',')
                parent_func, child_func = row_inst.func_name.split(',')
                offset_parent, offset_child = row_inst.offset_func.split(',')
                
                tmp_dict["parent_func"] = parent_func
                tmp_dict["offset_parent"] = offset_parent
                tmp_dict["child_func"] = child_func
                tmp_dict["offset_child"] = offset_child
                tmp_dict["machoc1"] = machoc1
                tmp_dict["machoc2"] = machoc2
                diff_plus.append(tmp_dict)

        
        #Elements IN 'filename2' and NOT IN 'filename1'
        diff_minus = []
        for value in diff_tuples_2:

            tmp_dict_2 = {}

            id_row = "{0},{1}".format(sample_id_2, value)
            row_inst = self.ctrl_offset_callCFG.get_by_id(id_row)
            
            if row_inst !=None:
                sample_id, machoc1, machoc2 = row_inst.id.split(',')
                parent_func, child_func = row_inst.func_name.split(',')
                offset_parent, offset_child = row_inst.offset_func.split(',')
                
                tmp_dict_2["parent_func"] = parent_func
                tmp_dict_2["offset_parent"] = offset_parent
                tmp_dict_2["child_func"] = child_func
                tmp_dict_2["offset_child"] = offset_child
                tmp_dict_2["machoc1"] = machoc1
                tmp_dict_2["machoc2"] = machoc2
                diff_minus.append(tmp_dict_2)
        print "\n"
        return diff_plus, diff_minus