# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MedicalTimeShift(models.Model):
    """Doctors time shift, different time slots"""
    _name = 'medical.time.shift'
    _description = "Medical Time Shift"
    _rec_name = 'name'

    name = fields.Char(string='Name', readonly=True,
                       help="name of the time shifts")
    shift_type = fields.Selection(
        selection=[('morning', 'Morning'), ('day', 'Day'),
                   ('evening', 'Evening'), ('night', 'Night')],
        string="Shift Type", help="Selection field for the shift type")
    start_time = fields.Float(string="Start Time", help="start time of time slot")
    end_time = fields.Float(string="End Time", help="End time of time slot")

    # NEW FIELDS
    slot_duration = fields.Selection([
        ('15', '15 Minutes'),
        ('30', '30 Minutes'),
        ('60', '1 Hour'),
    ], string="Slot Duration", default='30', required=True)

    max_appointments = fields.Integer(
        string="Max Appointments",
        default=10,
        help="Maximum appointments allowed in this shift per day"
    )

    working_days = fields.Many2many(
        'medical.working.day',
        string="Working Days",
        help="Days this shift is available"
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super(MedicalTimeShift, self).create(vals_list)
        res.name = f'{res.start_time} to {res.end_time}'
        return res

    @api.onchange('start_time', 'end_time')
    def _onchange_time(self):
        name = f'{self.start_time} to {self.end_time}'
        self.update({'name': name})
