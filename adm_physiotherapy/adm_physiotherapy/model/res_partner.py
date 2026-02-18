from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ROLE FLAGS

    is_patient = fields.Boolean(
        string="Is a Patient",
        default=False,
        index=True
    )

    is_physio = fields.Boolean(
        string="Is a Physiotherapist",
        default=False
    )

    # PATIENT FIELDS

    patient_code = fields.Char(
        string="Patient ID",
        copy=False,
        index=True,
        readonly=True
    )

    date_of_birth = fields.Date(string="Date of Birth")

    age = fields.Integer(
        string="Age",
        compute="_compute_age",
        store=True
    )

    gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ],
        string="Gender"
    )

    blood_group = fields.Selection(
        [
            ('a+', 'A+'), ('a-', 'A-'),
            ('b+', 'B+'), ('b-', 'B-'),
            ('o+', 'O+'), ('o-', 'O-'),
            ('ab+', 'AB+'), ('ab-', 'AB-'),
        ],
        string="Blood Group"
    )

    medical_history = fields.Text(string="Medical History")
    allergies = fields.Text(string="Allergies")
    emergency_contact = fields.Char(string="Emergency Contact")
    emergency_phone = fields.Char(string="Emergency Phone")

    # PHYSIOTHERAPIST FIELDS

    specialization = fields.Char(string="Specialization")
    license_number = fields.Char(string="License Number")
    qualification = fields.Char(string="Qualification")
    experience_years = fields.Integer(string="Years of Experience")
    consultation_fee = fields.Float(string="Consultation Fee")

    # REQUIRED for monetary widget (ODOO 19)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )

    # SMART COUNTS

    appointment_count = fields.Integer(
        compute="_compute_appointment_count"
    )

    prescription_count = fields.Integer(
        compute="_compute_prescription_count"
    )

    bill_count = fields.Integer(
        compute="_compute_bill_count"
    )

    # COMPUTE METHODS

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = date.today()
        for rec in self:
            rec.age = (
                relativedelta(today, rec.date_of_birth).years
                if rec.date_of_birth else 0
            )

    def _compute_appointment_count(self):
        Appointment = self.env.get('physio.appointment')
        for rec in self:
            rec.appointment_count = Appointment.search_count([
                ('patient_id', '=', rec.id)
            ]) if Appointment and rec.is_patient else 0

    def _compute_prescription_count(self):
        Prescription = self.env.get('physio.prescription')
        for rec in self:
            rec.prescription_count = Prescription.search_count([
                ('patient_id', '=', rec.id)
            ]) if Prescription and rec.is_patient else 0

    def _compute_bill_count(self):
        Billing = self.env.get('physio.billing')
        for rec in self:
            rec.bill_count = Billing.search_count([
                ('patient_id', '=', rec.id)
            ]) if Billing and rec.is_patient else 0

    # CREATE / WRITE

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_patient') and not vals.get('patient_code'):
                vals['patient_code'] = self.env['ir.sequence'].next_by_code(
                    'physio.patient'
                )
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if vals.get('is_patient'):
            for rec in self:
                if not rec.patient_code:
                    rec.patient_code = self.env['ir.sequence'].next_by_code(
                        'physio.patient'
                    )
        return res

    # ONCHANGE

    @api.onchange('is_patient')
    def _onchange_is_patient(self):
        if self.is_patient:
            self.customer_rank = 1

    @api.onchange('is_physio')
    def _onchange_is_physio(self):
        if self.is_physio:
            self.supplier_rank = 1

    # ACTIONS (USED BY XML)

    def action_open_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Appointments'),
            'res_model': 'physio.appointment',
            'view_mode': 'list,form,calendar',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_open_prescriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Prescriptions'),
            'res_model': 'physio.prescription',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_open_bills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bills'),
            'res_model': 'physio.billing',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    # CONSTRAINTS

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        for rec in self:
            if rec.date_of_birth and rec.date_of_birth > fields.Date.today():
                raise ValidationError(_("Date of birth cannot be in the future."))
