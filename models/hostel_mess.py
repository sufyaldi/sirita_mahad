from datetime import timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HostelMess(models.Model):
    _name = "hostel.mess"
    _description = "Hostel Mess / Dining"
    _order = "name"

    name = fields.Char(string="Mess Name", required=True)
    code = fields.Char(string="Code", size=16)
    building_id = fields.Many2one(
        "hostel.building",
        string="Building",
        ondelete="set null",
        help="Optional: mess serving this building",
    )
    active = fields.Boolean(default=True)
    menu_ids = fields.One2many(
        "hostel.mess.menu",
        "mess_id",
        string="Menus",
    )
    booking_ids = fields.One2many(
        "hostel.meal.booking",
        "mess_id",
        string="Meal Bookings",
    )


class HostelMessMenu(models.Model):
    _name = "hostel.mess.menu"
    _description = "Hostel Mess Menu"
    _order = "menu_date desc, meal_type"

    mess_id = fields.Many2one(
        "hostel.mess",
        string="Mess",
        required=True,
        ondelete="cascade",
    )
    menu_date = fields.Date(string="Date", required=True)
    meal_type = fields.Selection(
        [
            ("breakfast", "Breakfast"),
            ("lunch", "Lunch"),
            ("dinner", "Dinner"),
            ("snack", "Snack"),
        ],
        string="Meal Type",
        required=True,
    )
    name = fields.Char(string="Menu Title", required=True)
    description = fields.Text(string="Items / Description")

    _mess_date_meal_unique = models.Constraint(
        'UNIQUE(mess_id, menu_date, meal_type)',
        'A menu already exists for this mess, date and meal type.',
    )


class HostelMealBooking(models.Model):
    _name = "hostel.meal.booking"
    _description = "Hostel Meal Booking"
    _order = "booking_date desc, meal_type"

    student_id = fields.Many2one(
        "res.partner",
        string="Student",
        required=True,
        domain=[("is_student", "=", True)],
        ondelete="cascade",
    )
    mess_id = fields.Many2one(
        "hostel.mess",
        string="Mess",
        required=True,
        ondelete="cascade",
    )
    booking_date = fields.Date(string="Date", required=True)
    meal_type = fields.Selection(
        [
            ("breakfast", "Breakfast"),
            ("lunch", "Lunch"),
            ("dinner", "Dinner"),
            ("snack", "Snack"),
        ],
        string="Meal Type",
        required=True,
    )
    state = fields.Selection(
        [
            ("booked", "Booked"),
            ("attended", "Attended"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="booked",
        required=True,
    )
    attended_at = fields.Datetime(string="Attended At", readonly=True)

    _student_mess_date_meal_unique = models.Constraint(
        'UNIQUE(student_id, mess_id, booking_date, meal_type)',
        'A booking already exists for this student, mess, date and meal type.',
    )

    def action_mark_attended(self):
        for rec in self:
            if rec.state != "booked":
                raise UserError("Only booked meals can be marked as attended.")
            rec.state = "attended"
            rec.attended_at = fields.Datetime.now()

    def action_cancel(self):
        for rec in self:
            if rec.state != "booked":
                raise UserError("Only booked meals can be cancelled.")
            rec.state = "cancelled"

    @api.model_create_multi
    def create(self, vals_list):
        """Apply booking cutoff setting when creating a meal booking."""
        ICP = self.env["ir.config_parameter"].sudo()
        cutoff_str = ICP.get_str("sirita_mahad.meal_booking_cutoff_hours", "0") or "0"
        try:
            cutoff_hours = int(cutoff_str)
        except ValueError:
            cutoff_hours = 0

        for vals in vals_list:
            booking_date = vals.get("booking_date")
            if cutoff_hours and booking_date:
                try:
                    if isinstance(booking_date, str):
                        booking_date_obj = fields.Date.from_string(booking_date)
                    else:
                        booking_date_obj = booking_date
                    meal_dt = fields.Datetime.to_datetime("%s 00:00:00" % booking_date_obj)
                    cutoff_dt = meal_dt - timedelta(hours=cutoff_hours)
                except Exception:
                    cutoff_dt = None

                now = fields.Datetime.now()
                if cutoff_dt and now > cutoff_dt:
                    raise ValidationError(
                        "Meal bookings for %s are closed due to cutoff setting."
                        % booking_date
                    )

        return super().create(vals_list)

    @api.depends("state")
    def _compute_chargeable(self):
        """Helper for UI: whether this booking is considered chargeable."""
        ICP = self.env["ir.config_parameter"].sudo()
        enabled = (
            ICP.get_str("sirita_mahad.meal_charge_enabled", "False") != "False"
        )
        for rec in self:
            rec.chargeable = enabled and rec.state == "attended"

    chargeable = fields.Boolean(
        string="Chargeable",
        compute="_compute_chargeable",
        store=False,
        help="True when 'Enable mess meal charges' is on and the booking is attended.",
    )
