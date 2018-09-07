#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    This file is part of Polichombr.

    Organization : EDF-R&D-PERICLES-IRC
    Author : JCO
    Description: Generation of call-CFG and compare call-CFG
    Date : 08/2018
"""

import argparse,sys,os,r2pipe,json
import mmh3
import datetime, hashlib
import pydot

from ccfg_analyzeitrb import parse_machoc_signatures


class call_CFG:
    def __init__(self, filename, offset, app=None, tmessage=""):
        """
            Constructor
        """

        #Logger
        self.tmessage = tmessage
        self.app = app

        self.function_analyzed = []
        self.tuple_ccfg_db = []
        self.tuple_offset = []
        self.array_all_machoc_func = []

        self.hashfile = filename
        self.fname = filename+'.sign'

        # Open binary
        self._print("Analyze radare2 : in progress ... ")
        self.r2_binary = r2pipe.open(filename, ['-2'])
        if not self.is_valid_file():
            self.kill("Not a valid binary file")
            return
        self.run_cmd_radare2('aaa')
        self._print("Analyze radare2 : OK               ")


        self.offset = str(offset) if offset != "" else str(self.get_entry_point())
        #Get machoc functions
        self.machoc_functions = parse_machoc_signatures(self.fname)


    def process_cCFG(self, compare_tuples={}):
        """
            Process C-CFG generation or comparaison
        """
        if len(compare_tuples):
            self._print("Mode comparaison C-CFG")
            #Generate new CFG with diff
            self.process_compare_call_CFG(compare_tuples)

        else:
            self._print("Mode génération C-CFG")
            self.process_call_CFG()

            tuples = "('"+"'),('".join(self.tuple_ccfg_db)+"')"

            return self.offset, tuples, self.tuple_offset


    def _print(self, message):
        if self.app != None:
            self.app.logger.debug(self.tmessage + message)
        else:
            print message

    def is_valid_file(self, instance_r2=None):
        """
            Check if file contains instructions
        """
        
        if instance_r2:
            result = instance_r2.cmd("iIj")
        else:
            result = self.r2_binary.cmd("iIj")

        res = json.loads(result.replace("\\", ""))
        return bool(res['havecode'])

    def kill(self, message,instance_r2=None):
        """ 
            Kill radare2 process 
        """
        
        self._print("[+] '"+self.filename+"' : "+message)
        if instance_r2:
            instance_r2.r2_binary.quit()
        else:
            self.r2_binary.quit()

    def get_entry_point(self):
        """ 
            Return entrypoint
        """
        
        try:
            ie = json.loads(self.run_cmd_radare2("iej"))
            ie = ie[0]['vaddr']
        except ValueError:
            return None
        return ie

    def get_function_code(self, offset, instance_r2=None):
        """ 
            Return instructions from function at specific offset 
        """
        
        # Go to specific offset
        self.run_cmd_radare2("s {}".format(offset), instance_r2)
        result = self.run_cmd_radare2("pdfj", instance_r2)
        
        return json.loads(result) if result else {}

    def get_function_block(self, offset, instance_r2=None):
        """ 
            Return blocks from current function 
        """
        
        self.run_cmd_radare2("s {}".format(offset), instance_r2)
        return json.loads(self.run_cmd_radare2("agj", instance_r2))

    def format_function_name(self, function_name):
        """
            Format function name
            Example : 'call qword sym.imp.KERNEL32.dll_GetSystemTimeAsFileTime' become '_GetSystemTimeAsFile (KERNEL32.dll)'
        """

        return function_name.replace('call','').replace('qword','').replace('[','').replace(']','').strip()

    def get_call_in_function(self,offset, instance_r2=None):
        """
            Return dict with call of function from specific
        """
        
        if instance_r2 == None:
            self._print("Function analyzed : "+str(offset))
        else:
            self._print("FILE2] Function analyzed : "+str(offset))


        all_call = {}
        function_call = []
        function_ucall = []


        fcode = self.get_function_code(offset, instance_r2)
        if fcode != {}:
            for instruction in fcode["ops"]:
                if instruction["type"] == "call":
                    assembly_code = instruction['disasm']
                    if '.dll' in assembly_code:
                        array = assembly_code.split('.dll')
                        dll_name = array[0].split('.')[-1]
                        function_name = array[1]+' ('+dll_name+'.dll)'
                        function_ucall.append(function_name)
                    else:
                        function_call.append(assembly_code.replace('call','').strip())
                elif instruction["type"] == "ucall":
                    assembly_code = instruction['disasm']
                    if '.dll' in assembly_code:
                        array = assembly_code.split('.dll')
                        dll_name = array[0].split('.')[-1]
                        function_name = array[1]+' ('+dll_name+'.dll)'
                        function_ucall.append(function_name)
                    else:
                        function_ucall.append(self.format_function_name(assembly_code))
        all_call["call"] = function_call 
        all_call["ucall"] = function_ucall 
        return all_call

    

    def get_machoke_from_function(self, function_offset, db_machoc_func, instance_r2=None):
        """ 
            Return machoc function from (SHA256).bin.sign file
        """
        
        offset = self.get_offset(function_offset, instance_r2)
        if offset == "":
            return ""

        if offset != None:
            key_to_search = int(offset[2:],16)
            try:
                element_dict = db_machoc_func[key_to_search]
                machoc = hex(element_dict["machoc"])[2:]
                self._print("Machoc of '{0}' : {1}".format(function_offset, machoc))
                return machoc
            except:
                self._print("Unable to find machoc hash of offset function : "+str(offset))
                return ""                


    def format_block_dot(self, function_offset, function_machoc, adresse_offset, diff=False):
        """ 
            Return block dot info from specific
        """
        
        color = "palegreen"
        if diff and function_machoc != "":
            if function_offset not in self.array_all_machoc_func and function_machoc not in self.array_all_machoc_func:

                color = "#ff4d4d"
        content = "\""+function_offset+"\"[fillcolor=\""+color+"\",color=\"black\", fontname=\"Courier\",label=\"|- "+"sub_"+adresse_offset[2:]+" ("+function_offset+") "+"\l  "+function_machoc+"\"]"
        return content+"\n"

    def format_edge_dot(self, function_offset1, function_called_offset2, diff=False):
        """
            Return edge dot info from specific
        """
        
        color = "#ff0000" if diff else "#00007f" 

        content = "\""+str(function_offset1)+"\" -> \""+str(function_called_offset2)+"\" [color=\""+color+"\"];"
        return content+"\n"

    def add_tuple(self, function_machoke1, function_machoke2, adresse_offset, adresse_offset2, offset_called_func):
        """
            Save t-uple analyzed
        """
        
        if str(function_machoke2).startswith('0x'):
            function_machoke2 = 'sub_'+function_machoke2[2:]

        #T-uples saved in DB offset_callCFG (with more details)
        if function_machoke1+','+function_machoke2 not in self.tuple_ccfg_db:
            self.tuple_offset.append([adresse_offset+','+adresse_offset2,function_machoke1+','+function_machoke2, "sub_"+adresse_offset[2:]+",sub_"+offset_called_func[2:]])

        #T-uples saved in DB callCFG
        self.tuple_ccfg_db.append(function_machoke1+','+function_machoke2)


    def run_cmd_radare2(self, cmd, instance_r2 = None):
        """
            Return radare2 result of command
        """
        
        if instance_r2:
            return instance_r2.cmd(cmd)
        else:
            return self.r2_binary.cmd(cmd)

    def generate_file(self, content, filename=None):
        """
            Generate dot and CFG files
            Save file in directory 'polichombr/storage/'
        """

        if filename == None:
            filename = self.hashfile
        remove_extension = filename.split('.')
        if len(remove_extension) > 1:
            base_filename = ".".join(remove_extension[:-1]).split("/")[-1]
        else:
            base_filename = ".".join(remove_extension).split("/")[-1]

        dot_filename = "polichombr/storage/"+base_filename+'.dot'
        png_filename = "polichombr/storage/"+base_filename+'.png'

        f = open(dot_filename,'wb')
        f.write(content)
        f.close()
        self._print("Dot file generated : "+dot_filename)

        
        (graph,) = pydot.graph_from_dot_file(dot_filename)
        graph.write_png(png_filename)
        self._print("PNG file generated : "+png_filename)

    def remove_duplicate(self, dict):
        """
            Return dict without duplicates values
        """

        ret = {}
        for key,value in dict.iteritems():
            if key not in ret.keys():
                ret[key] = value
        return ret



    def generate_dot_content_info(self, function_offset):
        """
            Return call CFG in dot format from specific
        """
        
        adresse_offset = self.get_offset(function_offset)
        function_call = self.get_call_in_function(function_offset)
        function_machoc = self.get_machoke_from_function(function_offset, self.machoc_functions)
        dot_content = self.format_block_dot(function_offset, function_machoc, adresse_offset)
        
        #UCALL
        for call_func in function_call["ucall"]:
            machoke_signature = ""
            offset_called_func = self.get_offset(call_func)
            dot_content += self.format_block_dot(call_func, machoke_signature, offset_called_func)
            dot_content += self.format_edge_dot(function_offset, call_func)
            func_name_array = call_func.split(' ')
            if len(func_name_array) == 1:
                func_name = func_name_array[0]
            else:
                func_name = func_name_array[1].replace('(','').replace(')','')+func_name_array[0]


            #self.add_tuple(function_machoc, func_name, adresse_offset,offset_called_func, offset_called_func)
            self.add_tuple(function_machoc, machoke_signature, adresse_offset,offset_called_func, offset_called_func)


        #CALL
        for call_func in function_call["call"]:
            machoke_signature = self.get_machoke_from_function(call_func, self.machoc_functions)
            offset_called_func = self.get_offset(call_func)
            #self.add_tuple(function_machoc, machoke_signature if machoke_signature != "" else call_func , adresse_offset,offset_called_func, offset_called_func)
            self.add_tuple(function_machoc, machoke_signature , adresse_offset,offset_called_func, offset_called_func)

            
            dot_content += self.format_block_dot(call_func, machoke_signature, offset_called_func)
            dot_content += self.format_edge_dot(function_offset, call_func)#, offset_called_func)  



            if call_func not in self.function_analyzed:
                self.function_analyzed.append(call_func)
                try:
                    dot_content += self.generate_dot_content_info(call_func)
                except:
                    pass

        return dot_content


    def generate_dot_info(self, function_offset):
        """
            Concatenate dot content file
        """

        dot_content = """digraph code {
    graph [bgcolor=azure fontsize=8 fontname="Courier" splines="ortho"];
    node [fillcolor=gray style=filled shape=box];
    edge [arrowhead="normal"];"""

        dot_content += self.generate_dot_content_info(function_offset)
    
        dot_content += "}"

        self.generate_file(dot_content)

#############################################################################
##############################      COMPARE    ##############################
#############################################################################


    def generate_dot_compare_info(self, function_offset,diff_tuples, second_filename):
        """
            Concatenate dot compare content file
        """

        dot_content = """digraph code {
    graph [bgcolor=azure fontsize=8 fontname="Courier" splines="ortho"];
    node [fillcolor=gray style=filled shape=box];
    edge [arrowhead="normal"];"""

        dot_content += self.generate_dot_content_compare_info(function_offset, diff_tuples)
    
        dot_content += "}"

        tmp_filename1 = self.hashfile.split('/')[-1].split('.')[0]
        tmp_filename2 = second_filename.split('/')[-1].split('.')[0]

        filename = tmp_filename1+"_"+tmp_filename2
        self.generate_file(dot_content, filename)

    def generate_dot_content_compare_info(self, function_offset, diff_tuples):
        """
            Return comapre call CFG in dot format from specific
        """

        adresse_offset = self.get_offset(function_offset)
        function_call = self.get_call_in_function(function_offset)
        function_machoc = self.get_machoke_from_function(function_offset, self.machoc_functions)
        
        dot_content = "" # Important !

        if function_offset not in self.function_analyzed:
            dot_content = self.format_block_dot(function_offset, function_machoc, adresse_offset, True)

        #UCALL
        for call_func in function_call["ucall"]:
            func_name_array = call_func.split(' ')
            if len(func_name_array) == 1:
                func_name = func_name_array[0]
            else:
                func_name = func_name_array[1].replace('(','').replace(')','')+func_name_array[0]
            
            tuple_tmp = function_machoc+","+func_name
            dot_content += self.format_block_dot(call_func, "", self.get_offset(call_func), True)
            dot_content += self.format_edge_dot(function_offset, call_func, tuple_tmp in diff_tuples)
            if tuple_tmp in diff_tuples:
                diff_tuples.remove(tuple_tmp)
        
        #CALL
        for call_func in function_call["call"]:
            machoke_signature = self.get_machoke_from_function(call_func, self.machoc_functions)
            if machoke_signature == "":
                tuple_tmp = function_machoc+","+call_func
            else:
                tuple_tmp = function_machoc+","+machoke_signature
            dot_content += self.format_block_dot(call_func, machoke_signature, self.get_offset(call_func), True)
            dot_content += self.format_edge_dot(function_offset, call_func, tuple_tmp in diff_tuples )  
            if tuple_tmp in diff_tuples:
                diff_tuples.remove(tuple_tmp)

            if call_func not in self.function_analyzed:
                self.function_analyzed.append(call_func)
                try:
                    dot_content += self.generate_dot_content_compare_info(call_func, diff_tuples)
                except:
                    pass

        return dot_content

    def process_get_all_machoc_functions(self, filename, offset, instance_r2):
        """
            Get machoc functions
        """

        machoc_functions = parse_machoc_signatures(filename+'.sign')
        return self.get_all_machoc_functions(offset, instance_r2, machoc_functions)

    def get_all_machoc_functions(self, offset, instance_r2, machoc_functions):
        """
            Get machoc functions from specific offset
        """

        all_machoc_func = []

        function_call = self.get_call_in_function(offset, instance_r2)
        function_machoc = self.get_machoke_from_function(offset, machoc_functions, instance_r2)
        

        if self.first_loop == False:
            all_machoc_func.append(function_machoc)
            self.first_loop = True

        for call_func in function_call["ucall"]:
            func_name_array = call_func.split(' ')
            if len(func_name_array) == 1:
                func_name = func_name_array[0]
            else:
                func_name = func_name_array[1].replace('(','').replace(')','')+func_name_array[0]
            all_machoc_func.append(func_name)

        for call_func in function_call["call"]:
            machoke_signature = self.get_machoke_from_function(call_func, machoc_functions, instance_r2)
            if machoke_signature == "":
                all_machoc_func.append(str(call_func))
            else:
                all_machoc_func.append(machoke_signature)
            if call_func not in self.all_machoc_function_analyzed:
                self.all_machoc_function_analyzed.append(call_func)
                try:
                    all_machoc_func.extend(self.get_all_machoc_functions(call_func, instance_r2, machoc_functions))
                except:
                    pass
        return all_machoc_func


    def init_r2_instance(self, filename):
        """
            Initialize radare2 instance with filename parameter
        """
        instance_r2 = r2pipe.open(filename, ['-2'])
        # Open binary
        if not self.is_valid_file(instance_r2):
            self.kill("Not a valid binary file", instance_r2)
            return
        self.run_cmd_radare2('aaa', instance_r2)
        return instance_r2


    def process_compare_call_CFG(self, compare_tuples):
        """
            Process callCFG from entrypoint offset
        """

        filename2,diff_tuples,file2_offset = compare_tuples
        instance_r2 = self.init_r2_instance(filename2)

        #Etape 1 : Get all machoc functions of file 2
        self.all_machoc_function_analyzed = []
        self.first_loop = False
        self.array_all_machoc_func = self.process_get_all_machoc_functions(filename2, file2_offset, instance_r2)
        self.function_analyzed = []

        #Etape2 : Compare file 1 and file 2
        self.generate_dot_compare_info(self.offset, diff_tuples, filename2)

#############################################################################
#############################################################################
#############################################################################

    def get_offset(self, func_name, instance_r2 = None):
        """
            Return offset from specific
        """

        result = self.run_cmd_radare2('s @ '+str(func_name), instance_r2)
        return result

    def process_call_CFG(self):
        """
            Process callCFG from entrypoint offset
        """

        self._print("Start offset : "+str(self.get_offset(self.offset)))
        self.generate_dot_info(self.offset)

    @staticmethod
    def is_good_offset_value(offset):
        """
            Check if offset is a good value 
            NOT USED YET
        """
        r2_tmp = r2pipe.open(filename, ['-2'])
        try:
            r2_tmp.cmd("s {}".format(offset))
            return True
        except:
            return False