from odoo import models, fields, api


class AccountPayment(models.Model):
    # Extend account.payment to add treatment-related payment fields
    _inherit = 'account.payment'

    move_id = fields.Many2one('account.move', string="Related Invoice")
    treatment_name = fields.Char(string="Treatment Done")
    treatment_cost = fields.Float(string="Actual Cost")
    amount_due = fields.Float(string="Balance", compute="_compute_amount_due", store=True)
    patient_sign = fields.Char(string="Patient Sign")

    @api.depends('partner_id')
    def _compute_amount_due(self):
        for record in self:
            if record.partner_id:
                # Fetch all unpaid posted treatment invoices for this partner
                invoices = self.env['account.move'].search([
                    ('partner_id', '=', record.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('is_treatment_invoice', '=', True),
                    ('state', '=', 'posted'),
                    ('payment_state', '!=', 'paid'),
                ])
                total = sum(inv.amount_total for inv in invoices)
                paid = sum(inv.amount_total - inv.amount_residual for inv in invoices)
                record.amount_due = total - paid

                # Pull treatment details from the first unpaid invoice
                if invoices:
                    record.treatment_cost = invoices[0].amount_total
                    lines = invoices[0].invoice_line_ids
                    record.treatment_name = lines[0].name if lines else ''
            else:
                record.amount_due = 0.0
                record.treatment_cost = 0.0
                record.treatment_name = ''
