# -*- coding: utf-8 -*-

from odoo import models, fields


class MedicalWorkingDay(models.Model):
    _name = 'medical.working.day'
    _description = 'Medical Working Day'
    _order = 'sequence'

    name = fields.Char(string='Day', required=True)
    sequence = fields.Integer(default=10)
    code = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='Day Code', required=True)
