"""
    This file is part of Polichombr.

    Organization : EDF-R&D-PERICLES-IRC
    Author : JCO
    Description: Models to implement callCFG and offset_callCFG objects
    Date : 08/2018
"""

from datetime import datetime

from polichombr import db, ma


class callCFG(db.Model):

    """
      callCFG DB Model
    """
    __tablename__ = 'callCFG'

    id = db.Column(db.Integer(), primary_key=True)
    sample_id = db.Column(db.Integer(), db.ForeignKey('sample.id'))
    func_tuples = db.Column(db.String())
    offset_entrypoint = db.Column(db.String())
    creation_date = db.Column(db.DateTime())

    def __init__(self):
        self.creation_date = datetime.now()

class callCFGSchema(ma.ModelSchema):
    """
    Schema representation.
    """
    class Meta(object):
        fields = ('id',
                  'sample_id',
                  'func_tuples',
                  'offset_entrypoint',
                  'creation_date')


class offset_callCFG(db.Model):
    """
      offset calLCFF DB Model
    """

    __tablename__ = 'offset_callCFG'

    id = db.Column(db.String(), primary_key=True)
    sample_id = db.Column(db.Integer(), db.ForeignKey('sample.id'))
    offset_func = db.Column(db.String())
    func_name = db.Column(db.String())
    creation_date = db.Column(db.DateTime())

    def __init__(self):
        self.creation_date = datetime.now()

class offset_callCFGSchema(ma.ModelSchema):
    """
    Schema representation.
    """
    class Meta(object):
        fields = ('id',
                  'sample_id',
                  'offset_func',
                  'func_name',
                  'creation_date')
