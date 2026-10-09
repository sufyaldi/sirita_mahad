# -*- coding: utf-8 -*-

import json
from odoo import http
from odoo.http import request, Response


class HostelAPIController(http.Controller):
    """REST API for hostel data - gated by hostel_enable_rest_api setting."""

    def _check_api_enabled(self):
        """Check if REST API is enabled. Returns (enabled, response) - if not enabled, response is 403."""
        ICP = request.env["ir.config_parameter"].sudo()
        enabled = ICP.get_str("sirita_mahad.enable_rest_api", "False") != "False"
        if not enabled:
            return False, Response(
                json.dumps({
                    "success": False,
                    "error": "REST API is disabled. Enable it in Settings > Hostel Management > Mobile & API.",
                }),
                status=403,
                mimetype="application/json",
            )
        return True, None

    def _get_mobile_app_base_url(self):
        """Get mobile app base URL from settings for deep links."""
        ICP = request.env["ir.config_parameter"].sudo()
        return ICP.get_str("sirita_mahad.mobile_app_base_url", "") or ""

    @http.route("/hostel/api/info", type="http", auth="public", methods=["GET"])
    def api_info(self, **kwargs):
        """
        Public endpoint returning API status and mobile app base URL.
        Always accessible (even when API disabled) so mobile can check config.
        """
        ICP = request.env["ir.config_parameter"].sudo()
        enabled = ICP.get_str("sirita_mahad.enable_rest_api", "False") != "False"
        mobile_url = ICP.get_str("sirita_mahad.mobile_app_base_url", "") or ""
        return Response(
            json.dumps({
                "success": True,
                "api_enabled": enabled,
                "mobile_app_base_url": mobile_url,
            }),
            mimetype="application/json",
        )

    @http.route("/hostel/api/buildings", type="http", auth="user", methods=["GET"])
    def api_buildings(self, **kwargs):
        """List buildings - requires REST API enabled and user auth."""
        ok, err_response = self._check_api_enabled()
        if not ok:
            return err_response

        Building = request.env["hostel.building"].with_user(request.env.user)
        buildings = Building.search([("active", "=", True)], order="name")
        data = [
            {
                "id": b.id,
                "name": b.name,
                "code": b.code or "",
                "gender_allowed": b.gender_allowed,
            }
            for b in buildings
        ]
        mobile_url = self._get_mobile_app_base_url()
        return Response(
            json.dumps({
                "success": True,
                "data": data,
                "mobile_app_base_url": mobile_url,
            }),
            mimetype="application/json",
        )

    @http.route("/hostel/api/stats", type="http", auth="user", methods=["GET"])
    def api_stats(self, **kwargs):
        """Dashboard-style stats - requires REST API enabled and user auth."""
        ok, err_response = self._check_api_enabled()
        if not ok:
            return err_response

        Dashboard = request.env["hostel.dashboard"]
        stats = Dashboard.get_statistics()
        chart_data = Dashboard.get_chart_data()
        mobile_url = self._get_mobile_app_base_url()
        return Response(
            json.dumps({
                "success": True,
                "data": {
                    "statistics": stats,
                    "chart_data": chart_data,
                },
                "mobile_app_base_url": mobile_url,
            }),
            mimetype="application/json",
        )
