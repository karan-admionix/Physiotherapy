# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import pytz


class WebsiteAppointment(http.Controller):

    # AJAX ROUTE - LOAD AVAILABLE SLOTS

    @http.route('/get-available-slots', type='jsonrpc', auth='public')
    def get_available_slots(self, doctor_id, date):

        if not doctor_id or not date:
            return []

        doctor = request.env['hr.employee'].sudo().browse(int(doctor_id))
        if not doctor.exists():
            return []

        user_tz = pytz.timezone('Asia/Kolkata')
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        selected_day = str(date_obj.weekday())

        # Convert local date range to UTC for DB query
        local_start = user_tz.localize(
            date_obj.replace(hour=0, minute=0, second=0)
        )
        local_end = user_tz.localize(
            date_obj.replace(hour=23, minute=59, second=59)
        )
        utc_start = local_start.astimezone(pytz.utc).replace(tzinfo=None)
        utc_end = local_end.astimezone(pytz.utc).replace(tzinfo=None)

        # Get ALL appointments for that day (including booked)
        appointments = request.env['medical.appointment'].sudo().search([
            ('doctor_id', '=', doctor.id),
            ('state', '!=', 'cancelled'),
            ('appointment_date', '>=', utc_start),
            ('appointment_date', '<=', utc_end),
        ])

        # Map booked times in IST
        booked_slots = {}
        for appt in appointments:
            local_dt = pytz.utc.localize(
                appt.appointment_date
            ).astimezone(user_tz)
            t = local_dt.strftime("%H:%M")
            booked_slots[t] = True

        all_slots = []

        for shift in doctor.time_shift_ids:

            if shift.working_days:
                shift_days = [wd.code for wd in shift.working_days]
                if selected_day not in shift_days:
                    continue

            start = shift.start_time
            end = shift.end_time
            duration = int(shift.slot_duration or 30) / 60

            current = start
            while current < end:
                hour = int(current)
                minute = int(round((current - hour) * 60))

                if minute == 60:
                    hour += 1
                    minute = 0

                slot_time = f"{hour:02d}:{minute:02d}"
                is_booked = slot_time in booked_slots

                all_slots.append({
                    'time': slot_time,
                    'shift_id': shift.id,
                    'duration': shift.slot_duration or '30',
                    'is_booked': is_booked,
                })

                current += duration

        return all_slots

    # AJAX ROUTE - GET DOCTOR AVAILABLE DAYS
    @http.route('/get-doctor-available-days', type='jsonrpc', auth='public')
    def get_doctor_available_days(self, doctor_id):

        if not doctor_id:
            return []

        doctor = request.env['hr.employee'].sudo().browse(int(doctor_id))
        if not doctor.exists():
            return []

        available_days = []

        for shift in doctor.time_shift_ids:
            if shift.working_days:
                for wd in shift.working_days:
                    if wd.code not in available_days:
                        available_days.append(wd.code)
            else:
                # If no working days configured → all days allowed
                return ['0', '1', '2', '3', '4', '5', '6']

        return available_days

    # WEBSITE FORM
    @http.route('/book-appointment', type='http', auth='public', website=True)
    def appointment_form(self, **kwargs):
        import qrcode
        import base64
        from io import BytesIO

        doctors = request.env['hr.employee'].sudo().search([
            ('is_doctor', '=', True)
        ])

        # Generate QR code for booking page
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        booking_url = '%s/book-appointment' % base_url

        qr = qrcode.make(booking_url)
        buf = BytesIO()
        qr.save(buf, format='PNG')
        qr_image = base64.b64encode(buf.getvalue()).decode('utf-8')

        return request.render(
            'adm_physiotherapy.website_appointment_form',
            {
                'doctors': doctors,
                'qr_image': qr_image,
                'booking_url': booking_url,
            }
        )

    # SUBMIT APPOINTMENT
    @http.route('/submit-appointment', type='http', auth='public',
                website=True, methods=['POST'])
    def submit_appointment(self, **post):

        # -------- Get Form Values --------
        name = post.get('name')
        email = post.get('email')
        phone = post.get('phone')
        doctor_id = int(post.get('doctor_id'))
        appointment_date = post.get('appointment_date')
        slot_data = post.get('slot_time')

        if not slot_data:
            return request.redirect('/book-appointment')

        time_str, shift_id = slot_data.split("|")

        # ALWAYS use Asia/Kolkata for public booking
        user_tz = pytz.timezone('Asia/Kolkata')
        local_dt = datetime.strptime(
            f"{appointment_date} {time_str}",
            "%Y-%m-%d %H:%M"
        )
        local_dt = user_tz.localize(local_dt)
        date_time = local_dt.astimezone(pytz.utc).replace(tzinfo=None)

        # -------- Get Doctor --------
        doctor = request.env['hr.employee'].sudo().browse(doctor_id)

        # -------- Find or Create Partner --------
        user = request.env.user
        is_public = user._is_public()

        if not is_public:
            # Logged in user → use their own partner directly
            partner = user.partner_id
            partner.sudo().write({
                'name': name,
                'phone': phone or partner.phone,
                'is_patient': True,
            })
        else:
            # Guest user → find or create by email
            partner = request.env['res.partner'].sudo().search([
                ('email', '=', email)
            ], limit=1)

            if not partner:
                partner = request.env['res.partner'].sudo().create({
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'is_patient': True,
                })

        # -------- Check Double Booking --------
        slot_start = date_time
        slot_end = slot_start + timedelta(minutes=30)
        # slot_end = slot_start + __import__('datetime').timedelta(minutes=30)

        existing = request.env['medical.appointment'].sudo().search([
            ('doctor_id', '=', doctor.id),
            ('state', '!=', 'cancelled'),
            ('appointment_date', '<', slot_end),
            ('appointment_end', '>', slot_start),
        ], limit=1)

        if existing:
            return request.render(
                'adm_physiotherapy.website_appointment_error',
                {
                    'error_message': 'This time slot is already booked. Please select another time.',
                    'doctor_name': doctor.name,
                }
            )

        # -------- Create Appointment --------
        appointment = request.env['medical.appointment'].sudo().create({
            'patient_id': partner.id,
            'doctor_id': doctor.id,
            'shift_id': int(shift_id),
            'appointment_date': date_time,
            'state': 'draft',
        })

        # -------- Redirect to Payment Page --------
        return request.redirect(
            '/appointment/payment/%s' % appointment.id
        )

    # THANK YOU PAGE
    @http.route('/thank-you', type='http', auth='public', website=True)
    def thank_you(self, **kwargs):
        return request.render(
            'adm_physiotherapy.website_thank_you',
            {}
        )

    # PAYMENT PAGE
    @http.route('/appointment/payment/<int:appointment_id>',
                type='http', auth='public', website=True)
    def appointment_payment(self, appointment_id, **kwargs):

        appointment = request.env['medical.appointment'].sudo().browse(
            appointment_id
        )

        if not appointment.exists():
            return request.redirect('/book-appointment')

        # Get available payment providers
        providers = request.env['payment.provider'].sudo().search([
            ('state', 'in', ['enabled', 'test']),
        ])

        return request.render(
            'adm_physiotherapy.website_appointment_payment',
            {
                'appointment': appointment,
                'providers': providers,
            }
        )

    # PAYMENT SUCCESS CALLBACK
    @http.route('/appointment/payment/success',
                type='http', auth='public', website=True)
    # @http.route('/appointment/payment/success',
    #             type='http', auth='user', website=True)
    def appointment_payment_success(self, appointment_id=None, **kwargs):

        if not appointment_id:
            return request.redirect('/book-appointment')

        appointment = request.env['medical.appointment'].sudo().browse(
            int(appointment_id)
        )

        if appointment.exists() and appointment.state == 'draft':

            # Confirm appointment
            appointment.write({'state': 'confirmed'})

            # Send confirmation email
            template = request.env.ref(
                'adm_physiotherapy.email_template_medical_appointment',
                raise_if_not_found=False
            )
            if template and appointment.patient_id.email:
                template.sudo().send_mail(
                    appointment.id,
                    force_send=True
                )

        return request.redirect('/thank-you')

    # PAYMENT CANCEL CALLBACK
    @http.route('/appointment/payment/cancel',
                type='http', auth='public', website=True)
    # @http.route('/appointment/payment/cancel',
    #             type='http', auth='user', website=True)
    def appointment_payment_cancel(self, appointment_id=None, **kwargs):

        if appointment_id:
            appointment = request.env['medical.appointment'].sudo().browse(
                int(appointment_id)
            )
            if appointment.exists():
                appointment.write({'state': 'cancelled'})

        return request.render(
            'adm_physiotherapy.website_appointment_error',
            {
                'error_message': 'Payment was cancelled. Your appointment has not been confirmed.',
                'doctor_name': '',
            }
        )
