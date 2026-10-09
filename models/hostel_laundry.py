from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class HostelLaundryRequest(models.Model):
    _name = "hostel.laundry.request"
    _description = "Hostel Laundry Request"
    _order = "request_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        default="/",
        copy=False,
        readonly=True,
    )
    student_id = fields.Many2one(
        "res.partner",
        string="Student",
        required=True,
        domain=[("is_student", "=", True)],
        ondelete="cascade",
    )
    building_id = fields.Many2one(
        "hostel.building",
        string="Building",
        ondelete="set null",
    )
    request_date = fields.Date(
        string="Request Date",
        required=True,
        default=fields.Date.context_today,
    )
    service_type = fields.Selection(
        [
            ("wash", "Wash Only"),
            ("iron", "Iron Only"),
            ("wash_iron", "Wash & Iron"),
            ("dry_clean", "Dry Clean"),
        ],
        string="Service Type",
        required=True,
        default="wash_iron",
    )
    items_description = fields.Text(
        string="Items Description",
        help="e.g. 2 shirts, 1 jeans, 3 T-shirts",
    )
    quantity = fields.Integer(
        string="Number of Pieces",
        default=1,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
    )
    fee = fields.Monetary(
        string="Fee",
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    pickup_date = fields.Date(string="Pickup Date")
    delivery_date = fields.Date(string="Delivery Date")
    notes = fields.Text(string="Notes")

    @api.model_create_multi
    def create(self, vals_list):
        ICP = self.env["ir.config_parameter"].sudo()
        max_items_str = ICP.get_str("sirita_mahad.laundry_max_items", "0") or "0"
        try:
            max_items = int(max_items_str)
        except ValueError:
            max_items = 0

        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("hostel.laundry.request") or "/"
                )

            quantity = vals.get("quantity")
            if max_items and quantity and quantity > max_items:
                raise ValidationError(
                    "Maximum items per laundry request is %s. You entered %s."
                    % (max_items, quantity)
                )

            if not vals.get("fee"):
                service_type = vals.get("service_type") or "wash_iron"
                service_param_map = {
                    "wash": "sirita_mahad.laundry_fee_wash",
                    "iron": "sirita_mahad.laundry_fee_iron",
                    "wash_iron": "sirita_mahad.laundry_fee_wash_iron",
                    "dry_clean": "sirita_mahad.laundry_fee_dry_clean",
                }
                param_key = service_param_map.get(service_type)
                if param_key:
                    fee_str = ICP.get_str(param_key, "0") or "0"
                    try:
                        fee_per_item = float(fee_str)
                    except ValueError:
                        fee_per_item = 0.0
                    if fee_per_item:
                        qty = quantity or 1
                        vals["fee"] = fee_per_item * qty

        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError("Only draft requests can be submitted.")
            rec.state = "submitted"

    def action_start(self):
        for rec in self:
            if rec.state not in ("submitted", "in_progress"):
                raise UserError(
                    "Only submitted requests can be marked as in progress."
                )
            rec.state = "in_progress"

    def action_complete(self):
        for rec in self:
            if rec.state != "in_progress":
                raise UserError(
                    "Only in-progress requests can be marked as completed."
                )
            rec.state = "completed"
            if not rec.delivery_date:
                rec.delivery_date = fields.Date.context_today(self)

    def action_cancel(self):
        for rec in self:
            if rec.state in ("completed", "cancelled"):
                raise UserError(
                    "Completed or already cancelled requests cannot be cancelled."
                )
            rec.state = "cancelled"

    def action_reset_draft(self):
        for rec in self:
            if rec.state != "cancelled":
                raise UserError(
                    "Only cancelled requests can be reset to draft."
                )
            rec.state = "draft"

    # -------------------------------------------------------------------------
    # Settings-driven behaviours: default fees & max items
    # -------------------------------------------------------------------------

    def _get_service_fee_per_item(self, service_type):
        """Read per-item laundry fee from configuration for the given service."""
        ICP = self.env["ir.config_parameter"].sudo()
        service_param_map = {
            "wash": "sirita_mahad.laundry_fee_wash",
            "iron": "sirita_mahad.laundry_fee_iron",
            "wash_iron": "sirita_mahad.laundry_fee_wash_iron",
            "dry_clean": "sirita_mahad.laundry_fee_dry_clean",
        }
        param_key = service_param_map.get(service_type)
        if not param_key:
            return 0.0
        fee_str = ICP.get_str(param_key, "0") or "0"
        try:
            return float(fee_str)
        except ValueError:
            return 0.0

    def _get_laundry_max_items(self):
        """Return configured max items per request (0 = no limit)."""
        ICP = self.env["ir.config_parameter"].sudo()
        max_items_str = ICP.get_str("sirita_mahad.laundry_max_items", "0") or "0"
        try:
            return int(max_items_str)
        except ValueError:
            return 0

    @api.onchange("service_type", "quantity")
    def _onchange_service_type_or_quantity(self):
        """Auto-compute fee when service type or quantity changes, if settings exist."""
        for rec in self:
            if not rec.service_type:
                continue
            fee_per_item = rec._get_service_fee_per_item(rec.service_type)
            quantity = rec.quantity or 0
            if fee_per_item and quantity:
                rec.fee = fee_per_item * quantity

    @api.constrains("quantity")
    def _check_max_items_per_request(self):
        """Validate quantity against configurable max items per request."""
        max_items = self._get_laundry_max_items()
        if not max_items:
            return
        for rec in self:
            if rec.quantity and rec.quantity > max_items:
                raise ValidationError(
                    "Maximum items per laundry request is %s. You entered %s."
                    % (max_items, rec.quantity)
                )
