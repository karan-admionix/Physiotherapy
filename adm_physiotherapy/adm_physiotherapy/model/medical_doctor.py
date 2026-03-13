# -*- coding: utf-8 -*-

from datetime import date
from odoo import api, fields, models
from odoo.exceptions import UserError


class MedicalDoctor(models.Model):
    """Extension of hr.employee to add doctors of the Physiotherapy Management"""
    _inherit = 'hr.employee'

    job_position = fields.Char(
        string="Designation",
        help="Job position of the doctor"
    )

    specialised_in_id = fields.Many2one(
        'medical.specialist',
        string='Specialised In',
        help="Specialisation of the doctor"
    )

    dob = fields.Date(
        string="Date of Birth",
        required=False,
        help="DOB of the doctor"
    )

    doctor_age = fields.Integer(
        compute='_compute_doctor_age',
        store=True,
        string="Age",
        help="Age of the doctor"
    )

    sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string="Gender", help="Gender of the doctor")

    time_shift_ids = fields.Many2many(
        'medical.time.shift',
        'hr_employee_medical_time_shift_rel',
        'hr_employee_id',
        'medical_time_shift_id',
        string="Time Shift",
        help="Time shifts assigned to the doctor"
    )

    is_doctor = fields.Boolean(string="Is a Doctor")

    employee_type = fields.Selection([
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist'),
        ('other', 'Other')
    ], string='Employee Type', required=True, default='other')

    reg_no = fields.Char(string="Register No:")

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            phone = vals.get('mobile_phone') or vals.get('work_phone')

            if phone:
                existing_user = self.env['res.users'].search([
                    ('login', '=', phone)
                ])
                if existing_user:
                    raise UserError("Mobile number already exists for another user!")

            work_email = vals.get('work_email')
            if work_email:
                existing_user = self.env['res.users'].search([
                    ('login', '=', work_email)
                ])
                if existing_user:
                    raise UserError(
                        f"A user with email '{work_email}' already exists! "
                        f"Please use a different email or link to existing user '{existing_user.name}'."
                    )

        doctors = super(MedicalDoctor, self).create(vals_list)

        res_users_model = self.env['res.users']
        group_doctor = self.env.ref('adm_physiotherapy.group_medical_doctor')

        for doctor in doctors:

            phone = doctor.mobile_phone or doctor.work_phone

            if doctor.is_doctor and phone and not doctor.user_id:
                user_vals = {
                    'name': doctor.name,
                    'login': phone,
                    'employee_id': doctor.id,
                    'company_id': doctor.company_id.id,
                    'group_ids': [(4, group_doctor.id)],
                }

                create_user = res_users_model.sudo().create
                new_user = create_user(user_vals)

                doctor.user_id = new_user.id

        return doctors

    def unlink(self):

        for record in self:
            if record.user_id:
                record.user_id.write({'active': False})

        return super().unlink()

    def action_create_user(self):

        res_users_model = self.env['res.users']
        group_doctor = self.env.ref('adm_physiotherapy.group_medical_doctor')

        for doctor in self:

            phone = doctor.mobile_phone or doctor.work_phone

            if doctor.is_doctor and phone and not doctor.user_id:

                existing_user = res_users_model.search([('login', '=', phone)])
                if existing_user:
                    raise UserError("Mobile number already exists for another user!")

                if doctor.work_email:
                    existing_email = res_users_model.search([
                        ('login', '=', doctor.work_email)
                    ])
                    if existing_email:
                        raise UserError(
                            f"A user with email '{doctor.work_email}' already exists!"
                        )

                user_vals = {
                    'name': doctor.name,
                    'login': phone,
                    'employee_id': doctor.id,
                    'company_id': doctor.company_id.id,
                    'group_ids': [(4, group_doctor.id)],
                }

                create_user = res_users_model.sudo().create
                new_user = create_user(user_vals)

                doctor.user_id = new_user.id

    def write(self, vals):

        phone = vals.get('mobile_phone') or vals.get('work_phone')

        if phone:
            existing_user = self.env['res.users'].search([
                ('login', '=', phone),
                ('employee_id', 'not in', self.ids)
            ])
            if existing_user:
                raise UserError("Mobile number already exists for another user!")

        if 'work_email' in vals:
            existing_user = self.env['res.users'].search([
                ('login', '=', vals['work_email']),
                ('employee_id', 'not in', self.ids)
            ])
            if existing_user:
                raise UserError(
                    f"A user with email '{vals['work_email']}' already exists!"
                )

        return super(MedicalDoctor, self).write(vals)

    @api.depends('dob')
    def _compute_doctor_age(self):

        today = date.today()

        for record in self:
            if record.dob:
                record.doctor_age = today.year - record.dob.year - (
                        (today.month, today.day) < (record.dob.month, record.dob.day)
                )
            else:
                record.doctor_age = 0
