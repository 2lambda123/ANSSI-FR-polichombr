#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    This file is part of Polichombr.

    Organization : EDF-R&D-PERICLES-IRC
    Author : JCO
    Description: CallCFG task implementation.
    Date : 08/2018
"""

import os
import time

from polichombr import app
from polichombr.controllers.task import Task
from polichombr.controllers.callCFG import callCFGController, offset_callCFGController

from polichombr.analysis_tools.lib_callCFG.C_CFG import call_CFG


class task_callCFG(Task):

    """
    Generate callCFG form file.
    """

    def __init__(self, sample):
        super(task_callCFG, self).__init__()
        self.tmessage = "CALLCFG TASK %d :: " % (sample.id)
        self.sid = sample.id
        self.tstart = None
        self.storage_file = sample.storage_file
        self.offset_callCFG = sample.offset_callCFG

    def execute(self):
        self.tstart = int(time.time())
        app.logger.info(self.tmessage + "EXECUTE")
        self.fname = self.storage_file + '.sign'
        while not os.path.exists(self.fname): # Waiting Creation of Machoc file SHA256(file).bin.sign
            time.sleep(1)
            if int(time.time() - self.tstart) > 120:
                app.logger.info(self.tmessage + " Machoc file not found")
                return False

        self.process_call_CFG() #Generate callCFG
        return True


    def process_call_CFG(self):
        app.logger.info(self.tmessage + 'Process call CFG')

        inst_ccfg = call_CFG(self.storage_file, self.offset_callCFG, app, self.tmessage)
        self.offset, self.tuples, self.offset_tuples = inst_ccfg.process_cCFG()


    def apply_result(self):
        s_controller = callCFGController()
        s_controller_offset = offset_callCFGController()
        with app.app_context():
            app.logger.debug(self.tmessage + "APPLY_RESULT")
            s_controller.add_callCFG(self.sid, self.tuples, self.offset)
            s_controller_offset.add_multiple_offset_callCFG(self.sid, self.offset_tuples)


        app.logger.debug(self.tmessage + "END - TIME %i" %
                         (int(time.time()) - self.tstart))
        return True