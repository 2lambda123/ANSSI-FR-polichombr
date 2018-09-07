"""
    This file is part of Polichombr.

    Organization : EDF-R&D-PERICLES-IRC
    Author : JCO
    Description: Managers for all the actions about call-CFG, associated with callCFG models
    Date : 08/2018
"""
from polichombr import app
from polichombr import db
from polichombr.models.callCFG import callCFG, offset_callCFG



class callCFGController(object):

    """
        Wrapper to the callCFG model. 
    """

    def __init__(self):
        pass


    @staticmethod
    def add_callCFG(sample_id, func_tuples, entrypoint_offset):
        """
            Adds a callCFG
        """
        model_callCFG = callCFG()
        model_callCFG.sample_id = sample_id
        model_callCFG.func_tuples = func_tuples
        model_callCFG.offset_entrypoint = entrypoint_offset
        db.session.add(model_callCFG)
        db.session.commit()
        return True

    @staticmethod
    def get_all(sid = None):
        """
        Get all callcfg
        """
        if sid != None:
            return callCFG.query.filter(callCFG.sample_id != sid).all()
        else:
            return callCFG.query.all()

    @staticmethod
    def get_by_id(sample_id):
        """
        Get callCFG by its sample id.
        """
        result = callCFG.query.filter_by(sample_id=sample_id).all()
        return result[0] if len(result) > 0 else None

    @staticmethod
    def delete(callCFG):
        """
        Removes callCFG from database.
        """
        db.session.delete(callCFG)
        db.session.commit()
        return

class offset_callCFGController(object):

    """
        Wrapper to the offset_callCFG model. 
    """

    def __init__(self):
        pass

    @staticmethod
    def add_offset_callCFG( sample_id, element, do_commit=True):
        """
            Adds an offset_callCFG
        """

        offset_func, func_tuples, func_name = element

        model_offset_callCFG = offset_callCFG()
        model_offset_callCFG.id = '{0},{1}'.format(sample_id, func_tuples)
        model_offset_callCFG.sample_id = sample_id
        model_offset_callCFG.offset_func = offset_func
        model_offset_callCFG.func_name = func_name

        db.session.add(model_offset_callCFG)

        if do_commit:
            db.session.commit()



    def add_multiple_offset_callCFG(self, sample_id, tuples):
        """
            Adds multiple offset_callCFG
        """
        for element in tuples:
            self.add_offset_callCFG(sample_id, element, do_commit = False)
        db.session.commit()
        return True


    @staticmethod
    def get_by_sample_id(sample_id):
        """
        Get offset_callCFG by its sample id.
        """
        result = offset_callCFG.query.filter_by(sample_id=sample_id).all()
        return result

    @staticmethod
    def get_by_id(id):
        """
        Get offset_callCFG by its sample id.
        """
        result = offset_callCFG.query.filter_by(id=id).all()
        return result[0]


    @staticmethod
    def delete(offset_callCFG, do_commit=True):
        """
        Removes offset_callCFG from database.
        """
        db.session.delete(offset_callCFG)
        if do_commit:
            db.session.commit()
        return

    def delete_multiple_offset_callCFG(self, all_offset_callCFG):
        """
            Delete multiple offset_callCFG
        """
        for element in all_offset_callCFG:
            self.delete(element, do_commit = False)
        db.session.commit()
        return True
