# -*- coding: utf-8 -*-
{

    "name": "Physiotherapy Management System",
    "version": "19.0.0.0.0",
    # "currency": 'EUR',
    "summary": "Apps basic Hospital Management system Healthcare Management Clinic Management apps manage clinic manage Patient hospital manage Healthcare system Patient Management Hospital Management Healthcare Management Clinic Management hospital Lab Test Request",
    "category": "Industry",
    "description": """
    Admionix Solutions developed a new odoo/OpenERP module apps
    This module is used to manage Hospital and Healthcare Management and Clinic Management apps. 
    manage clinic manage Patient hospital in odoo manage Healthcare system Patient Management, 
    Odoo Hospital Management odoo Healthcare Management Odoo Clinic Management
    Odoo hospital Patients
    Odoo Healthcare Patients Card Report
    Odoo Healthcare Patients Medication History Report
    Odoo Healthcare Appointments
    Odoo hospital Appointments Invoice
    Odoo Healthcare Families Prescriptions Healthcare Prescriptions
    Odoo Healthcare Create Invoice from Prescriptions odoo hospital Prescription Report
    Odoo Healthcare Patient Hospitalization
    odoo Hospital Management System
    Odoo Healthcare Management System
    Odoo Clinic Management System
    Odoo Appointment Management System
    health care management system
    Generate Report for patient details, appointment, prescriptions, lab-test

    Odoo Lab Test Request and Result
    Odoo Patient Hospitalization detail`s
    Generate Patient's Prescriptions

    
""",

    "depends": ["base", "sale_management", "stock", "accountant", "hr", "contacts", "mail",
                "portal", "website", "web", "purchase", "product", "planning", "payment", "appointment"],

    'data': [
        'security/medical_clinic_groups.xml',
        'security/ir.model.access.csv',
        'security/medical_partner_rules.xml',

        'data/medical_appointment_mail_template.xml',
        'data/patient_id_sequence.xml',
        'data/medical_specialist_data.xml',
        'data/treatment_category_data.xml',
        'data/medical_treatment_data.xml',
        'data/medical_time_shift_data.xml',
        'data/medicine_frequency_data.xml',
        'data/medical_working_day_data.xml',

        'views/res_partner_views.xml',
        'views/patient_view.xml',
        'views/medical_appointment_views.xml',
        'views/medical_doctor_views.xml',
        'views/medical_prescription_views.xml',
        'views/medical_payment_log_views.xml',
        'views/medical_treatment_views.xml',
        'views/treatment_category_views.xml',
        'views/medicine_frequency_views.xml',
        'views/medical_medicine_views.xml',
        'views/medical_questions_views.xml',
        'views/medical_specialist_views.xml',
        'views/medical_time_shift_views.xml',
        'views/medical_source_views.xml',
        'views/portal_templates.xml',
        'views/portal_appointment_templates.xml',
        'views/website_appointment_templates.xml',
        'views/website_menu.xml',

        'report/medical_prescription_report.xml',
        'report/medical_prescription_templates.xml',
        'report/medical_appointment_slip_report.xml',

    ],
    "author": "Admionix Solutions",
    'website': "https://admionixsolutions.com/",
    "installable": True,
    "application": True,
    'assets': {
        'web.assets_frontend': [
            'adm_physiotherapy/static/src/js/appointment_slots.js'],
        'web.assets_backend': [
            'adm_physiotherapy/static/src/js/disable_select_role.js'],

    },
    # "auto_install": False,
    "images": ["static/description/icon.png"],
    "license": 'OPL-1',

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
