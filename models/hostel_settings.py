from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # -------------------------------------------------------------------------
    # Dashboard settings
    # -------------------------------------------------------------------------
    hostel_default_dashboard_range_days = fields.Integer(
        string="Hostel dashboard default days",
        config_parameter="sirita_mahad.default_dashboard_range_days",
        default=30,
        help="Number of days shown by default in the hostel dashboard date range (From = To - N days).",
    )

    hostel_dashboard_show_expiry_highlights = fields.Boolean(
        string="Show expiry highlights on dashboard",
        config_parameter="sirita_mahad.dashboard_show_expiry_highlights",
        default=True,
        help="If enabled, the dashboard shows cards for contracts expiring in the next 10/30 days.",
    )

    hostel_dashboard_auto_refresh_interval = fields.Integer(
        string="Dashboard auto-refresh interval (minutes)",
        config_parameter="sirita_mahad.dashboard_auto_refresh_interval",
        default=0,
        help="If greater than 0, the hostel dashboard can auto-refresh every N minutes.",
    )

    # -------------------------------------------------------------------------
    # Visitor control settings
    # -------------------------------------------------------------------------
    hostel_visitor_require_approval = fields.Boolean(
        string="Require visitor approval",
        config_parameter="sirita_mahad.visitor_require_approval",
        default=True,
        help="If disabled, visitor requests can be auto-approved on creation.",
    )

    hostel_visitor_max_per_day = fields.Integer(
        string="Max visitors per student per day",
        config_parameter="sirita_mahad.visitor_max_per_day",
        default=0,
        help="Soft limit for the number of visitors per student per day (0 = no limit).",
    )

    hostel_visitor_overstay_minutes = fields.Integer(
        string="Visitor overstay threshold (minutes)",
        config_parameter="sirita_mahad.visitor_overstay_minutes",
        default=0,
        help="Number of minutes beyond expected duration after which a visitor is considered overdue (0 = disabled).",
    )

    hostel_visitor_notify_email = fields.Boolean(
        string="Email student on visitor approval/rejection",
        config_parameter="sirita_mahad.visitor_notify_email",
    )

    hostel_visitor_notify_sms = fields.Boolean(
        string="SMS student on visitor approval/rejection",
        config_parameter="sirita_mahad.visitor_notify_sms",
    )

    # -------------------------------------------------------------------------
    # Attendance settings
    # -------------------------------------------------------------------------
    hostel_attendance_source = fields.Selection(
        [
            ("manual", "Manual"),
            ("checkin", "From Check-In/Out"),
            ("mixed", "Mixed"),
        ],
        string="Attendance source",
        config_parameter="sirita_mahad.attendance_source",
        default="manual",
    )

    hostel_attendance_late_grace = fields.Integer(
        string="Late entry grace minutes",
        config_parameter="sirita_mahad.attendance_late_grace",
        default=0,
        help="Number of minutes after the official time before a student is marked as late (0 = no grace).",
    )

    hostel_attendance_absent_notify_guardian = fields.Boolean(
        string="Notify guardian on absence",
        config_parameter="sirita_mahad.attendance_absent_notify_guardian",
        help="If enabled, guardians can be notified when a student is absent.",
    )

    # -------------------------------------------------------------------------
    # Fee management & penalties
    # -------------------------------------------------------------------------
    hostel_rent_invoice_day = fields.Integer(
        string="Rent invoice generation day",
        config_parameter="sirita_mahad.rent_invoice_day",
        default=1,
        help="Day of the month when monthly rent invoices are generated.",
    )

    hostel_late_payment_penalty_type = fields.Selection(
        [
            ("none", "No penalty"),
            ("fixed", "Fixed amount"),
            ("percent", "Percentage of due amount"),
        ],
        string="Late payment penalty type",
        config_parameter="sirita_mahad.late_penalty_type",
        default="none",
    )

    hostel_late_payment_penalty_value = fields.Float(
        string="Late payment penalty value",
        config_parameter="sirita_mahad.late_penalty_value",
        help="Fixed amount or percentage value depending on the penalty type.",
    )

    hostel_payment_reminder_days_before_due = fields.Integer(
        string="Payment reminder days before due",
        config_parameter="sirita_mahad.payment_reminder_days_before_due",
        default=0,
        help="Number of days before due date to trigger payment reminders (0 = disabled).",
    )

    hostel_enable_payment_gateway = fields.Boolean(
        string="Enable payment gateway integration",
        config_parameter="sirita_mahad.enable_payment_gateway",
    )

    # -------------------------------------------------------------------------
    # Room allocation
    # -------------------------------------------------------------------------
    hostel_enable_allocation_requests = fields.Boolean(
        string="Enable allocation requests",
        config_parameter="sirita_mahad.enable_allocation_requests",
        help="If enabled, room allocation request workflow is available.",
    )

    hostel_allocation_strategy = fields.Selection(
        [
            ("first_free", "First free bed"),
            ("balanced", "Balanced across buildings"),
            ("preference_based", "Preference based"),
        ],
        string="Default allocation strategy",
        config_parameter="sirita_mahad.allocation_strategy",
        default="first_free",
    )

    hostel_allow_mixed_gender_buildings = fields.Boolean(
        string="Allow mixed-gender buildings",
        config_parameter="sirita_mahad.allow_mixed_gender_buildings",
        help="If enabled, allocation can ignore strict gender separation by building.",
    )

    # -------------------------------------------------------------------------
    # Maintenance
    # -------------------------------------------------------------------------
    hostel_maintenance_default_priority = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Default maintenance priority",
        config_parameter="sirita_mahad.maintenance_default_priority",
        default="medium",
    )

    hostel_maintenance_auto_assign = fields.Boolean(
        string="Auto-assign maintenance requests",
        config_parameter="sirita_mahad.maintenance_auto_assign",
    )

    hostel_maintenance_notify_requester = fields.Boolean(
        string="Notify requester on maintenance updates",
        config_parameter="sirita_mahad.maintenance_notify_requester",
    )

    # -------------------------------------------------------------------------
    # Complaints & grievances
    # -------------------------------------------------------------------------
    hostel_complaint_allow_anonymous = fields.Boolean(
        string="Allow anonymous complaints",
        config_parameter="sirita_mahad.complaint_allow_anonymous",
    )

    hostel_complaint_escalation_days = fields.Integer(
        string="Complaint escalation days",
        config_parameter="sirita_mahad.complaint_escalation_days",
        default=0,
        help="Number of days after which unresolved complaints are escalated (0 = disabled).",
    )

    hostel_complaint_notify_student = fields.Boolean(
        string="Notify student on complaint updates",
        config_parameter="sirita_mahad.complaint_notify_student",
    )

    hostel_complaint_notify_manager = fields.Boolean(
        string="Notify hostel manager on complaint updates",
        config_parameter="sirita_mahad.complaint_notify_manager",
    )

    # -------------------------------------------------------------------------
    # Mess / food
    # -------------------------------------------------------------------------
    hostel_meal_booking_cutoff_hours = fields.Integer(
        string="Meal booking cutoff (hours)",
        config_parameter="sirita_mahad.meal_booking_cutoff_hours",
        default=0,
        help="Number of hours before meal time after which bookings are not allowed (0 = disabled).",
    )

    hostel_meal_charge_enabled = fields.Boolean(
        string="Enable mess meal charges",
        config_parameter="sirita_mahad.meal_charge_enabled",
    )

    # -------------------------------------------------------------------------
    # Laundry
    # -------------------------------------------------------------------------
    hostel_laundry_default_fee_wash = fields.Float(
        string="Default laundry fee (wash)",
        config_parameter="sirita_mahad.laundry_fee_wash",
    )

    hostel_laundry_default_fee_iron = fields.Float(
        string="Default laundry fee (iron)",
        config_parameter="sirita_mahad.laundry_fee_iron",
    )

    hostel_laundry_default_fee_wash_iron = fields.Float(
        string="Default laundry fee (wash & iron)",
        config_parameter="sirita_mahad.laundry_fee_wash_iron",
    )

    hostel_laundry_default_fee_dry_clean = fields.Float(
        string="Default laundry fee (dry clean)",
        config_parameter="sirita_mahad.laundry_fee_dry_clean",
    )

    hostel_laundry_max_items = fields.Integer(
        string="Max items per laundry request",
        config_parameter="sirita_mahad.laundry_max_items",
        default=0,
        help="Soft limit for number of items per laundry request (0 = no limit).",
    )

    # -------------------------------------------------------------------------
    # Room inspections
    # -------------------------------------------------------------------------
    hostel_inspection_default_frequency = fields.Integer(
        string="Default inspection frequency (days)",
        config_parameter="sirita_mahad.inspection_default_frequency",
        default=0,
        help="Used for auto-scheduling room inspections (0 = disabled).",
    )

    hostel_inspection_auto_schedule = fields.Boolean(
        string="Enable auto-scheduling of inspections",
        config_parameter="sirita_mahad.inspection_auto_schedule",
    )

    # -------------------------------------------------------------------------
    # Notice board / announcements
    # -------------------------------------------------------------------------
    hostel_announcement_default_target = fields.Selection(
        [
            ("all", "All students"),
            ("building", "By building"),
        ],
        string="Default announcement target",
        config_parameter="sirita_mahad.announcement_default_target",
        default="all",
    )

    hostel_announcement_email_broadcast = fields.Boolean(
        string="Email announcements to students",
        config_parameter="sirita_mahad.announcement_email_broadcast",
    )

    # -------------------------------------------------------------------------
    # Document management
    # -------------------------------------------------------------------------
    hostel_document_expiry_warning_days = fields.Integer(
        string="Document expiry warning days",
        config_parameter="sirita_mahad.document_expiry_warning_days",
        default=30,
        help="Number of days before expiry when documents are considered 'expiring soon'.",
    )

    hostel_require_documents_on_checkin = fields.Boolean(
        string="Require key documents on check-in",
        config_parameter="sirita_mahad.require_documents_on_checkin",
        help="If enabled, check-in can be blocked when mandatory documents are missing or expired.",
    )

    # -------------------------------------------------------------------------
    # Security / portals
    # -------------------------------------------------------------------------
    hostel_security_enable_student_portal = fields.Boolean(
        string="Enable student portal features",
        config_parameter="sirita_mahad.security_enable_student_portal",
    )

    hostel_security_enable_staff_portal = fields.Boolean(
        string="Enable staff portal features",
        config_parameter="sirita_mahad.security_enable_staff_portal",
    )

    # -------------------------------------------------------------------------
    # Communication / email & SMS
    # -------------------------------------------------------------------------
    hostel_enable_sms = fields.Boolean(
        string="Enable hostel SMS notifications",
        config_parameter="sirita_mahad.enable_sms",
    )

    hostel_default_email_template_contract = fields.Many2one(
        "mail.template",
        string="Default contract email template",
        config_parameter="sirita_mahad.email_template_contract",
        domain="[('model', '=', 'hostel.contract')]",
    )

    hostel_default_email_template_visitor = fields.Many2one(
        "mail.template",
        string="Default visitor email template",
        config_parameter="sirita_mahad.email_template_visitor",
        domain="[('model', '=', 'hostel.visitor')]",
    )

    # -------------------------------------------------------------------------
    # Reporting / exports
    # -------------------------------------------------------------------------
    hostel_enable_advanced_reports = fields.Boolean(
        string="Enable advanced hostel reports",
        config_parameter="sirita_mahad.enable_advanced_reports",
    )

    hostel_default_export_format = fields.Selection(
        [
            ("pdf", "PDF"),
            ("xlsx", "Excel (XLSX)"),
        ],
        string="Default export format",
        config_parameter="sirita_mahad.default_export_format",
        default="pdf",
    )

    # -------------------------------------------------------------------------
    # Mobile / API
    # -------------------------------------------------------------------------
    hostel_enable_rest_api = fields.Boolean(
        string="Enable hostel REST API",
        config_parameter="sirita_mahad.enable_rest_api",
    )

    hostel_mobile_app_base_url = fields.Char(
        string="Mobile app base URL",
        config_parameter="sirita_mahad.mobile_app_base_url",
        help="Base URL for linking to or from the mobile app.",
    )

