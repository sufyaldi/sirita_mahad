from datetime import datetime
from odoo import api, models, fields, _
from odoo.exceptions import UserError


ADVANCED_REPORT_TYPES = (
    "occupancy",
    "financial",
    "attendance",
    "visitors",
)


class HostelReportWizard(models.TransientModel):
    _name = "hostel.report.wizard"
    _description = "Hostel Report Export Wizard"

    report_type = fields.Selection(
        [
            ("students_inhouse", "Students Currently In-House"),
            ("occupancy", "Occupancy Report"),
            ("financial", "Financial Report"),
            ("attendance", "Attendance Report"),
            ("visitors", "Visitor Report"),
        ],
        string="Report Type",
        required=True,
        default="students_inhouse",
    )

    export_format = fields.Selection(
        [
            ("pdf", "PDF"),
            ("xlsx", "Excel (XLSX)"),
        ],
        string="Export Format",
        required=True,
        default="pdf",
        help="Default format is taken from Settings > Hostel Management > Reporting & Export.",
    )

    date_from = fields.Date(
        string="Date From",
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_to = fields.Date(
        string="Date To",
        default=fields.Date.context_today,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "export_format" in fields_list:
            ICP = self.env["ir.config_parameter"].sudo()
            default_format = ICP.get_str(
                "sirita_mahad.default_export_format", "pdf"
            ) or "pdf"
            if default_format in ("pdf", "xlsx"):
                res["export_format"] = default_format
        return res

    def _check_advanced_reports_enabled(self):
        if self.report_type not in ADVANCED_REPORT_TYPES:
            return
        ICP = self.env["ir.config_parameter"].sudo()
        enabled = ICP.get_str(
            "sirita_mahad.enable_advanced_reports", "False"
        ) != "False"
        if not enabled:
            raise UserError(
                _(
                    "Advanced reports are disabled. "
                    "Enable them in Settings > Hostel Management > Reporting & Export."
                )
            )

    def action_generate(self):
        self.ensure_one()
        self._check_advanced_reports_enabled()

        if self.export_format == "pdf":
            return self._generate_pdf()
        return self._generate_list_view()

    def _generate_pdf(self):
        return self.env.ref(
            "sirita_mahad.action_report_hostel_wizard"
        ).report_action(self)

    def _generate_list_view(self):
        today = fields.Date.today()
        actions = {
            "students_inhouse": {
                "name": _("Students Currently In-House"),
                "res_model": "hostel.contract",
                "domain": [("state", "=", "active")],
                "context": {"group_by": "building_id"},
            },
            "occupancy": {
                "name": _("Occupancy Report"),
                "res_model": "hostel.contract",
                "domain": [("state", "=", "active")],
                "context": {"group_by": "room_id"},
            },
            "financial": {
                "name": _("Financial Report"),
                "res_model": "hostel.rent.invoice",
                "domain": [],
                "context": {},
            },
            "attendance": {
                "name": _("Attendance Report"),
                "res_model": "hostel.student.attendance",
                "domain": [("date", "=", today)],
                "context": {},
            },
            "visitors": {
                "name": _("Visitor Report"),
                "res_model": "hostel.visitor",
                "domain": [
                    ("visit_datetime", ">=", datetime.combine(today, datetime.min.time())),
                    ("visit_datetime", "<=", datetime.combine(today, datetime.max.time())),
                ],
                "context": {},
            },
        }
        action_config = actions.get(self.report_type, actions["students_inhouse"])
        action_config["type"] = "ir.actions.act_window"
        action_config["view_mode"] = "list,form"
        return action_config

    # ------------------------------------------------------------------
    #  Data provider called from QWeb templates
    # ------------------------------------------------------------------
    def get_report_data(self):
        self.ensure_one()
        handler = "_get_%s_data" % self.report_type
        data_fn = getattr(self, handler, None)
        records, summary = data_fn() if data_fn else (self.env["hostel.contract"], {})
        report_titles = dict(self._fields["report_type"].selection)
        return {
            "title": report_titles.get(self.report_type, "Hostel Report"),
            "subtitle": "Period: %s to %s" % (
                self.date_from or "-",
                self.date_to or "-",
            ),
            "generated_on": fields.Datetime.now().strftime("%d %b %Y, %H:%M"),
            "generated_by": self.env.user.name,
            "records": records,
            "summary": summary,
        }

    # --- Students In-House ------------------------------------------------
    def _get_students_inhouse_data(self):
        domain = [("state", "=", "active")]
        if self.date_from:
            domain.append(("contract_start", ">=", self.date_from))
        if self.date_to:
            domain.append(("contract_start", "<=", self.date_to))
        contracts = self.env["hostel.contract"].search(domain, order="building_id, room_id")
        summary = {
            "total": len(contracts),
            "buildings": len(contracts.mapped("building_id")),
        }
        return contracts, summary

    # --- Occupancy --------------------------------------------------------
    def _get_occupancy_data(self):
        rooms = self.env["hostel.room"].search([], order="unit_id, name")
        Contract = self.env["hostel.contract"]
        records = []
        total_beds = 0
        occupied_beds = 0
        contract_domain = [("state", "=", "active")]
        if self.date_from:
            contract_domain.append(("contract_end", ">=", self.date_from))
        if self.date_to:
            contract_domain.append(("contract_start", "<=", self.date_to))
        for room in rooms:
            beds = self.env["hostel.bed"].search([("room_id", "=", room.id)])
            t = len(beds)
            occ = 0
            for bed in beds:
                if Contract.search_count(contract_domain + [("bed_id", "=", bed.id)]):
                    occ += 1
            total_beds += t
            occupied_beds += occ
            room_type_label = "-"
            if hasattr(room, "room_type") and room.room_type:
                sel = room._fields["room_type"].selection
                if callable(sel):
                    sel = sel(room)
                room_type_label = dict(sel).get(room.room_type, room.room_type)
            records.append({
                "building": room.unit_id.building_id.name if room.unit_id and room.unit_id.building_id else "-",
                "room": room.name or "-",
                "room_type": room_type_label,
                "total_beds": t,
                "occupied": occ,
                "vacant": t - occ,
                "rate": round(occ * 100.0 / t, 1) if t else 0,
            })
        vacant_beds = total_beds - occupied_beds
        summary = {
            "total_rooms": len(rooms),
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "vacant_beds": vacant_beds,
            "occupancy_rate": round(
                occupied_beds * 100.0 / total_beds, 1
            ) if total_beds else 0,
        }
        return records, summary

    # --- Financial --------------------------------------------------------
    def _get_financial_data(self):
        domain = []
        if self.date_from:
            domain.append(("period_end", ">=", self.date_from))
        if self.date_to:
            domain.append(("period_start", "<=", self.date_to))
        invoices = self.env["hostel.rent.invoice"].search(domain, order="period_start desc")
        total = sum(invoices.mapped("amount"))
        paid = sum(invoices.filtered(lambda i: i.state == "paid").mapped("amount"))
        overdue = sum(invoices.filtered(lambda i: i.state == "overdue").mapped("amount"))
        currency = self.env.company.currency_id
        summary = {
            "total_invoices": len(invoices),
            "total_amount": "%s %s" % (currency.symbol, "{:,.2f}".format(total)),
            "paid_amount": "%s %s" % (currency.symbol, "{:,.2f}".format(paid)),
            "outstanding": "%s %s" % (currency.symbol, "{:,.2f}".format(total - paid)),
            "overdue": "%s %s" % (currency.symbol, "{:,.2f}".format(overdue)),
        }
        return invoices, summary

    # --- Attendance -------------------------------------------------------
    def _get_attendance_data(self):
        domain = []
        if self.date_from:
            domain.append(("date", ">=", self.date_from))
        if self.date_to:
            domain.append(("date", "<=", self.date_to))
        records = self.env["hostel.student.attendance"].search(domain, order="date desc, student_id")
        summary = {
            "total": len(records),
            "present": len(records.filtered(lambda r: r.status == "present")),
            "absent": len(records.filtered(lambda r: r.status == "absent")),
            "late": len(records.filtered(lambda r: r.status == "late")),
        }
        return records, summary

    # --- Visitors ---------------------------------------------------------
    def _get_visitors_data(self):
        domain = []
        if self.date_from:
            domain.append(
                ("visit_datetime", ">=", datetime.combine(self.date_from, datetime.min.time()))
            )
        if self.date_to:
            domain.append(
                ("visit_datetime", "<=", datetime.combine(self.date_to, datetime.max.time()))
            )
        records = self.env["hostel.visitor"].search(domain, order="visit_datetime desc")
        summary = {
            "total": len(records),
            "checked_in": len(records.filtered(lambda r: r.status == "checked_in")),
            "completed": len(records.filtered(lambda r: r.status == "completed")),
            "pending": len(records.filtered(lambda r: r.status == "pending")),
        }
        return records, summary
