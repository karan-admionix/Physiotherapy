# -*- coding: utf-8 -*-

from odoo import fields, models


class MedicalMedicine(models.Model):
    """Extends product.template to support medicine products in Physiotherapy Management"""
    _inherit = 'product.template'

    # Marks this product as a medicine for filtering purposes
    is_medicine = fields.Boolean('Is Medicine',
                                 help="If the product is a Medicine")
    generic_name = fields.Char(string="Generic Name",
                               help="Generic name of the medicament")
    dosage_strength = fields.Integer(string="Dosage Strength",
                                     help="Dosage strength of medicament")
