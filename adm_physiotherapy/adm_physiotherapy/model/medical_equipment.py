from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MedicalEquipment(models.Model):
    _name = 'medical.equipment'
    _description = 'Medical Equipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'


    # BASIC IDENTIFICATION

    # name = fields.Char(
    #     string="Equipment Reference",
    #     required=True,
    #     copy=False,
    #     readonly=True,
    #     default=lambda self: 'New'
    # )

    product_id = fields.Many2one(
        'product.product',
        string="Equipment Product",
        required=True,
        domain="[('product_tmpl_id.is_medical_product','=',True),"
               " ('product_tmpl_id.medical_product_type','=','equipment')]",
        tracking=True,
    )

    serial_lot_id = fields.Many2one(
        'stock.lot',
        string="Serial Number",
        required=True,
        domain="[('product_id','=',product_id)]",
        tracking=True,
    )

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )


    # OWNERSHIP & ASSIGNMENT

    department_id = fields.Many2one(
        'res.partner',
        string="Owning Department",
        domain="[('is_medical_department','=',True)]",
        tracking=True,
        required=True,
    )

    assigned_physio_id = fields.Many2one(
        'res.partner',
        string="Assigned Physiotherapist",
        domain="[('is_physio','=',True)]",
        tracking=True,
    )


    # LIFECYCLE MANAGEMENT

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('maintenance', 'Under Maintenance'),
            ('retired', 'Retired'),
        ],
        default='draft',
        tracking=True,
        required=True,
    )

    acquisition_date = fields.Date(
        string="Acquisition Date",
        tracking=True
    )

    retirement_date = fields.Date(
        string="Retirement Date",
        tracking=True
    )

    notes = fields.Text(string="Notes")


    # CONSTRAINTS

    @api.constrains('product_id')
    def _check_product_configuration(self):
        """
        Ensure selected product is valid medical equipment.
        """
        for rec in self:
            tmpl = rec.product_id.product_tmpl_id
            if not tmpl.is_medical_product:
                raise ValidationError(
                    "Selected product is not marked as Medical Product."
                )
            if tmpl.medical_product_type != 'equipment':
                raise ValidationError(
                    "Selected product is not configured as Medical Equipment."
                )
            if rec.product_id.tracking != 'serial':
                raise ValidationError(
                    "Medical Equipment product must use Serial Number tracking."
                )

    @api.constrains('serial_lot_id', 'product_id')
    def _check_serial_uniqueness(self):
        """
        Prevent one serial being linked to multiple equipment records.
        """
        for rec in self:
            if not rec.serial_lot_id:
                continue
            count = self.search_count([
                ('id', '!=', rec.id),
                ('serial_lot_id', '=', rec.serial_lot_id.id),
                ('product_id', '=', rec.product_id.id),
            ])
            if count:
                raise ValidationError(
                    "This Serial Number is already linked to another equipment."
                )


    # CREATE OVERRIDE

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'medical.equipment'
                ) or 'New'
        return super().create(vals_list)


    # STATE ACTIONS

    def action_activate(self):
        for rec in self:
            if rec.state != 'draft':
                continue
            rec.state = 'active'
            rec.acquisition_date = fields.Date.today()

    def action_send_to_maintenance(self):
        for rec in self:
            if rec.state != 'active':
                raise ValidationError(
                    "Only active equipment can be sent to maintenance."
                )
            rec.state = 'maintenance'

    def action_retire(self):
        for rec in self:
            if rec.state == 'retired':
                continue
            rec.state = 'retired'
            rec.retirement_date = fields.Date.today()
            rec.assigned_physio_id = False

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.acquisition_date = False
            rec.retirement_date = False
