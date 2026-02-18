from odoo import http, fields
from odoo.http import request


class WebsiteAppointmentController(http.Controller):

    # APPOINTMENT FORM(GET)
    @http.route('/appointments', type='http', auth='public', website=True)
    def appointment_form(self, **kw):
        therapists = request.env['res.partner'].sudo().search([
            ('is_physio', '=', True)
        ])

        return request.render(
            'adm_physiotherapy.website_appointment_form',
            {
                'therapists': therapists
            }
        )

    # APPOINTMENT SUBMIT(POST)
    @http.route('/appointments/submit', type='http', auth='public',
                methods=['POST'], website=True)
    def appointment_submit(self, **post):
        user = request.env.user
        patient = user.partner_id if not user._is_public() else None

        vals = {
            'patient_id': patient.id if patient else None,
            'therapist_id': int(post.get('therapist_id')),
            'appointment_date': post.get('appointment_date'),
        }

        appointment = request.env['physio.appointment'].sudo().create(vals)

        return request.render(
            'adm_physiotherapy.website_appointment_success',
            {'appointment': appointment}
        )