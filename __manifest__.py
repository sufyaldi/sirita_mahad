{
    "name": "Sirita Ma'had Al-Jami'ah — Sistem Informasi Manajemen Asrama & Pembinaan Mahasantri PTKIN",
    "version": "20.0.1.0",
    "category": "Education / Hostel",
    "summary": "Core hostel management system for buildings, rooms, beds, students, and contracts",
    "description": """
        Hostel & Student Accommodation Management System
        
        This module provides the core data backbone for managing:
        - Hostel buildings, units, rooms, and beds
        - Student master data and hostel contracts
        - Bed-level occupancy tracking
        - Check-in and check-out processes
        - Apartment-wise and bed-wise occupancy history
        - Room status management (Dirty, Ready, Buffer, Out of Order)
        - Gender- and room-type-based allocation
        
        This module is intentionally designed as a foundational layer.
        Advanced features such as dashboards, penalties, invoicing,
        asset management, HR, and automation are implemented in
        separate dependent modules.
    """,
    'author': 'sufyALDI / TIPD IAIN Parepare',
    'website': 'https://tipd.iainpare.ac.id',
    "depends": [
        "base",
        "base_setup",
        "web",
        "contacts",
        "account",
        "hr",
        "mail",
        "hr_attendance",
        "hr_holidays"
    ],
    "data": [
        "security/hostel_security.xml",
        "report/hostel_reports.xml",
        "report/hostel_report_templates.xml",
        "data/email_templates.xml",
        "data/hostel_announcement_data.xml",
        "data/demo_data.xml",
        "data/mahad_initial_data.xml",
        "data/ir_cron_data.xml",
        "views/hostel_building_views.xml",
        "views/hostel_unit_views.xml",
        "views/hostel_room_views.xml",
        "views/hostel_bed_views.xml",
        "views/hostel_contract_views.xml",
        "views/hostel_checkin_views.xml",
        "views/res_partner_views.xml",
        "views/hostel_dashboard_views.xml",
        "views/hostel_automation_views.xml",
        "views/hostel_asset_views.xml",
        "views/hostel_communication_views.xml",
        "views/hostel_announcement_views.xml",
        "views/account_move_views.xml",
        "views/hr_employee_views.xml",
        "views/hostel_visitor_views.xml",
        "views/hostel_student_attendance_views.xml",
        "views/hostel_rent_invoice_views.xml",
        "views/hostel_maintenance_request_views.xml",
        "views/hostel_complaint_views.xml",
        "views/hostel_mess_views.xml",
        "views/hostel_laundry_views.xml",
        "views/hostel_room_inspection_views.xml",
        "views/hostel_student_document_views.xml",
        "views/hostel_settings_views.xml",
        "views/hostel_report_views.xml",
        "views/hostel_help_views.xml",
        "views/menu.xml",
        "views/hostel_penalty_type_views.xml",
        'security/ir.access.csv',
    ],
    "assets": {
        "web.assets_backend": [
            "sirita_mahad/static/src/css/dashboard.css",
            "sirita_mahad/static/src/xml/hostel_dashboard.xml",
            "sirita_mahad/static/src/js/hostel_dashboard.js",
        ],
    },
    "application": True,
    "installable": True,
    "license": "LGPL-3",
    "images": ["static/description/main_screenshot.png"],
    "icon": "sirita_mahad/static/description/icon.png",
}
