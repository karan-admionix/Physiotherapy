# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PhysiotherapyPortal(CustomerPortal):

    @http.route(['/my/appointments'], type='http', auth="user", website=True)
    def portal_my_appointments(self, **kw):

        user = request.env.user
        partner = user.partner_id

        Appointment = request.env["medical.appointment"].sudo()

        is_admin = user.has_group("base.group_system")
        is_doctor = user.has_group("adm_physiotherapy.group_physio_doctor")

        if is_admin:
            domain = []

        elif is_doctor:
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            domain = [('doctor_id', '=', employee.id)] if employee else [('id', '=', 0)]

        else:
            domain = [('patient_id', '=', partner.id)]

        appointments = Appointment.search(domain)
        appointment_count = Appointment.search_count(domain)

        values = {
            "appointments": appointments,
            "appointment_count": appointment_count,
            "page_name": "appointments",
        }

        return request.render("adm_physiotherapy.portal_appointment_templates", values)
