from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date


class ResPartner(models.Model):
    # Extend res.partner to support Patient and Physiotherapist roles
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

    # Required for monetary widget to work correctly
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )

    # SMART COUNTS

    appointment_count = fields.Integer(
        compute="_compute_appointment_count"
    )

    appointment_ids = fields.One2many(
        'medical.appointment',
        'patient_id',
        string='Appointments'
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
        # Only count appointments for patients
        for rec in self:
            rec.appointment_count = self.env['medical.appointment'].search_count([
                ('patient_id', '=', rec.id)
            ]) if rec.is_patient else 0

    def _compute_prescription_count(self):
        # Only count prescriptions for patients
        for rec in self:
            rec.prescription_count = self.env['medical.prescription'].search_count([
                ('patient_id', '=', rec.id)
            ]) if rec.is_patient else 0

    def _compute_bill_count(self):
        # Only count treatment invoices for patients
        for rec in self:
            rec.bill_count = self.env['account.move'].search_count([
                ('partner_id', '=', rec.id),
                ('move_type', '=', 'out_invoice'),
                ('is_treatment_invoice', '=', True),
            ]) if rec.is_patient else 0

    # CREATE / WRITE

    @api.model_create_multi
    def create(self, vals_list):
        # Auto-assign patient code sequence on creation
        for vals in vals_list:
            if vals.get('is_patient') and not vals.get('patient_code'):
                vals['patient_code'] = self.env['ir.sequence'].next_by_code(
                    'medical.patient'
                )
        records = super().create(vals_list)
        for rec in records:
            if rec.is_patient:
                rec._assign_portal_user()
        return records

    def write(self, vals):
        res = super().write(vals)
        # Re-assign portal user if patient flag or email is updated
        if vals.get('is_patient') or vals.get('email'):
            for rec in self:
                if rec.is_patient:
                    rec._assign_portal_user()
        return res

    @api.constrains('is_patient', 'email')
    def _check_patient_email(self):
        # Patient must have an email to receive portal access
        for rec in self:
            if rec.is_patient and not rec.email:
                raise ValidationError(
                    _("Patient '%s' must have an email address.") % rec.name
                )

    # ONCHANGE

    @api.onchange('is_patient')
    def _onchange_is_patient(self):
        # Mark as customer when flagged as patient
        if self.is_patient:
            self.customer_rank = 1

    @api.onchange('is_physio')
    def _onchange_is_physio(self):
        # Mark as supplier when flagged as physiotherapist
        if self.is_physio:
            self.supplier_rank = 1

    # ACTIONS (USED BY XML)

    def action_open_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Appointments'),
            'res_model': 'medical.appointment',
            'view_mode': 'list,form,calendar',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_open_prescriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Prescriptions'),
            'res_model': 'medical.prescription',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_open_bills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bills'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id), ('move_type', '=', 'out_invoice')],
            'context': {'default_patient_id': self.id},
        }

    def _assign_portal_user(self):
        # Create or update portal user linked to this patient partner
        self.ensure_one()

        if not self.email:
            return

        portal_group = self.env.ref('base.group_portal')

        existing_user = self.env['res.users'].sudo().search([
            ('partner_id', '=', self.id),
        ], limit=1)

        if existing_user:
            # Add portal group to existing user if not already assigned
            existing_user.sudo().write({
                'group_ids': [(4, portal_group.id)]
            })
            return

        self.env['res.users'].sudo().create({
            'name': self.name,
            'login': self.email,
            'partner_id': self.id,
            'group_ids': [(6, 0, [portal_group.id])],
        })

    # CONSTRAINTS

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        for rec in self:
            if rec.date_of_birth and rec.date_of_birth > fields.Date.today():
                raise ValidationError(_("Date of birth cannot be in the future."))
