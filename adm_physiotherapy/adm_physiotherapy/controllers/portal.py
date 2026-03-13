# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from datetime import datetime
import pytz


class PhysiotherapyPortal(CustomerPortal):
    # Extends Odoo portal to support role-based appointment access (Admin, Doctor, Patient)

    def _prepare_home_portal_values(self, counters):
        # Inject appointment count into portal home dashboard based on user role
        values = super()._prepare_home_portal_values(counters)

        user = request.env.user
        Appointment = request.env["medical.appointment"].sudo()

        is_admin = user.has_group("base.group_system")
        is_doctor = user.has_group("adm_physiotherapy.group_medical_doctor")

        # Build domain based on role
        if is_admin:
            domain = []
        elif is_doctor:
            employee = request.env['hr.employee'].sudo().search(
                [('user_id', '=', user.id)], limit=1
            )
            domain = [('doctor_id', '=', employee.id)] if employee else [('id', '=', 0)]
        else:
            domain = [('patient_id', '=', user.partner_id.id)]

        if 'appointment_count' in counters:
            values['appointment_count'] = Appointment.search_count(domain)

        return values

    @http.route(['/my/appointments'], type='http', auth="user", website=True)
    def portal_my_appointments(self, **kw):
        # Portal page listing appointments grouped by status for the logged-in user

        user = request.env.user
        Appointment = request.env["medical.appointment"].sudo()

        is_admin = user.has_group("base.group_system")
        is_doctor = (
                user.has_group("adm_physiotherapy.group_medical_doctor") or
                user.has_group("adm_physiotherapy.group_physio_doctor")
        )

        # Set domain and portal_role based on user role
        if is_admin:
            domain = []
            portal_role = 'admin'
        elif is_doctor:
            employee = request.env['hr.employee'].sudo().search(
                [('user_id', '=', user.id)], limit=1
            )
            domain = [('doctor_id', '=', employee.id)] if employee else [('id', '=', 0)]
            portal_role = 'doctor'
        else:
            domain = [('patient_id', '=', user.partner_id.id)]
            portal_role = 'patient'

        from datetime import datetime
        import pytz

        # Convert current UTC time to IST to get correct today boundaries
        user_tz = pytz.timezone('Asia/Kolkata')
        now_utc = datetime.utcnow()
        now_local = pytz.utc.localize(now_utc).astimezone(user_tz)

        today_start = now_local.replace(
            hour=0, minute=0, second=0, microsecond=0
        ).astimezone(pytz.utc).replace(tzinfo=None)

        today_end = now_local.replace(
            hour=23, minute=59, second=59, microsecond=0
        ).astimezone(pytz.utc).replace(tzinfo=None)

        # WAITING LIST — today's confirmed/in_progress
        waiting_domain = domain + [
            ('appointment_date', '>=', today_start),
            ('appointment_date', '<=', today_end),
            ('state', 'in', ['confirmed', 'in_progress']),
        ]
        waiting_list = Appointment.search(waiting_domain, order='appointment_date asc')

        # UPCOMING — future confirmed
        upcoming_domain = domain + [
            ('appointment_date', '>', today_end),
            ('state', 'in', ['draft', 'confirmed']),
        ]
        upcoming = Appointment.search(upcoming_domain, order='appointment_date asc')

        # PAST — done appointments
        past_domain = domain + [
            ('state', '=', 'done'),
        ]
        past = Appointment.search(past_domain, order='appointment_date desc')

        # CANCELLED
        cancelled_domain = domain + [
            ('state', '=', 'cancelled'),
        ]
        cancelled = Appointment.search(cancelled_domain, order='appointment_date desc')

        appointment_count = Appointment.search_count(domain)

        values = {
            "waiting_list": waiting_list,
            "upcoming": upcoming,
            "past": past,
            "cancelled": cancelled,
            "appointment_count": appointment_count,
            "page_name": "appointments",
            "portal_role": portal_role,  # Used in template to control visible sections
        }

        return request.render(
            "adm_physiotherapy.portal_appointment_templates", values
        )

    @http.route(['/my/appointments/<int:appointment_id>'],
                type='http', auth="user", website=True)
    def portal_appointment_detail(self, appointment_id, **kw):
        # Shows detail view of a single appointment with role-based access control

        user = request.env.user
        appointment = request.env['medical.appointment'].sudo().browse(appointment_id)

        if not appointment.exists():
            return request.redirect('/my/appointments')

        # Security check — restrict access based on role
        is_admin = user.has_group("base.group_system")
        is_doctor = user.has_group("adm_physiotherapy.group_medical_doctor")

        if not is_admin:
            if is_doctor:
                employee = request.env['hr.employee'].sudo().search(
                    [('user_id', '=', user.id)], limit=1
                )
                # Doctor can only view their own assigned appointments
                if appointment.doctor_id.id != employee.id:
                    return request.redirect('/my/appointments')
            else:
                # Patient can only view their own appointments
                if appointment.patient_id.id != user.partner_id.id:
                    return request.redirect('/my/appointments')

        return request.render(
            'adm_physiotherapy.portal_appointment_detail',
            {'appointment': appointment}
        )

    @http.route(['/my/appointments/<int:appointment_id>/cancel'],
                type='http', auth="user", website=True, methods=['POST'])
    def portal_appointment_cancel(self, appointment_id, **kw):
        # Cancels an appointment from the portal — only allowed for draft/confirmed states

        appointment = request.env['medical.appointment'].sudo().browse(appointment_id)

        if appointment.exists() and appointment.state in ('draft', 'confirmed'):
            appointment.write({'state': 'cancelled'})

        return request.redirect('/my/appointments')

    # WAITING AREA SCREEN
    @http.route(['/waiting-screen'], type='http', auth="public", website=True)
    def waiting_screen(self, **kw):
        # Public screen for clinic waiting area — shows today's active appointments

        user_tz = pytz.timezone('Asia/Kolkata')
        now_utc = datetime.utcnow()
        now_local = pytz.utc.localize(now_utc).astimezone(user_tz)

        # Today's date range in UTC
        today_start = user_tz.localize(
            now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        ).astimezone(pytz.utc).replace(tzinfo=None)

        today_end = user_tz.localize(
            now_local.replace(hour=23, minute=59, second=59, microsecond=0)
        ).astimezone(pytz.utc).replace(tzinfo=None)

        # Get today's confirmed/in_progress appointments
        appointments = request.env['medical.appointment'].sudo().search([
            ('appointment_date', '>=', today_start),
            ('appointment_date', '<=', today_end),
            ('state', 'in', ['confirmed', 'in_progress']),
        ], order='appointment_date asc')

        return request.render(
            'adm_physiotherapy.waiting_screen_template',
            {
                'appointments': appointments,
                'now': now_local.strftime('%d %b %Y  %I:%M %p'),
            }
        )
