from odoo import models, fields


class HrEmployeePublic(models.Model):
    # Extend hr.employee.public to add physiotherapy-specific fields
    _inherit = "hr.employee.public"

    job_position = fields.Char(string="Designation")
    specialised_in_id = fields.Many2one("medical.specialist", string="Specialised In")
    dob = fields.Date(string="Date of Birth")
    doctor_age = fields.Integer(string="Age")
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")

    # Available time shifts assigned to this employee/doctor
    time_shift_ids = fields.Many2many(
        'medical.time.shift',
        'hr_employee_medical_time_shift_rel',
        'hr_employee_id',
        'medical_time_shift_id',
        string="Time Shift"
    )

    is_doctor = fields.Boolean(string="Is a Doctor")
    employee_type = fields.Selection([
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist'),
        ('other', 'Other')
    ], string="Employee Type")
    reg_no = fields.Char(string="Register No:")
