/** @odoo-module **/

import { Component, onWillStart, onMounted, onPatched, onWillUnmount, proxy, signal } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

const CHART_COLORS = [
    "#2A8FD6", "#198754", "#e65100", "#5e35b1", "#00796b", "#c62828",
    "#3949ab", "#0097a7", "#ef6c00", "#7b1fa2",
];

function getDefaultDateRange() {
    const today = new Date();
    const from = new Date(today);
    from.setDate(from.getDate() - 30);
    return {
        date_from: from.toISOString().slice(0, 10),
        date_to: today.toISOString().slice(0, 10),
    };
}

class HostelDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.revenueChartRef = signal.ref();
        this.attendanceChartRef = signal.ref();
        this.visitorsChartRef = signal.ref();
        this.revenueChartInstance = null;
        this.attendanceChartInstance = null;
        this.visitorsChartInstance = null;

        const defaultRange = getDefaultDateRange();
        this.state = proxy({
            statistics: {
                daily_checkin_count: 0,
                daily_contract_ending_count: 0,
                active_students_count: 0,
                vacant_spaces_count: 0,
                upcoming_30_days_count: 0,
                upcoming_10_days_count: 0,
                total_buildings: 0,
                total_rooms: 0,
                total_beds: 0,
                occupancy_rate: 0,
                visitor_today_count: 0,
                visitor_pending_count: 0,
                visitor_in_range_count: 0,
                maintenance_open_count: 0,
                maintenance_in_progress_count: 0,
                maintenance_total_count: 0,
                attendance_today_count: 0,
                attendance_in_range_count: 0,
                revenue_paid: 0,
                revenue_outstanding: 0,
                collection_rate: 0,
                complaints_open_count: 0,
                laundry_open_count: 0,
                inspections_open_count: 0,
                announcements_active_count: 0,
            },
            chartData: {
                occupancy_by_building: [],
                revenue_monthly: [],
                attendance_daily: [],
                visitors_daily: [],
                maintenance_by_state: [],
            },
            date_from: defaultRange.date_from,
            date_to: defaultRange.date_to,
            loading: true,
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadStatistics();
        });

        onMounted(() => {
            document.body.classList.add("hostel_dashboard");
            this.renderCharts();
        });
        onPatched(() => this.renderCharts());
        onWillUnmount(() => {
            document.body.classList.remove("hostel_dashboard");
            this.destroyCharts();
        });
    }

    // -------------------------------------------------------------------------
    // Chart.js rendering
    // -------------------------------------------------------------------------

    renderCharts() {
        this.renderRevenueChart();
        this.renderAttendanceChart();
        this.renderVisitorsChart();
    }

    destroyCharts() {
        if (this.revenueChartInstance) {
            this.revenueChartInstance.destroy();
            this.revenueChartInstance = null;
        }
        if (this.attendanceChartInstance) {
            this.attendanceChartInstance.destroy();
            this.attendanceChartInstance = null;
        }
        if (this.visitorsChartInstance) {
            this.visitorsChartInstance.destroy();
            this.visitorsChartInstance = null;
        }
    }

    renderRevenueChart() {
        const canvas = this.revenueChartRef();
        if (!canvas) return;
        const Chart = window.Chart;
        if (!Chart) return;

        const data = this.state.chartData.revenue_monthly || [];
        const labels = data.map((d) => d.label);
        const values = data.map((d) => d.value);
        const hasData = values.some((v) => v > 0);

        if (this.revenueChartInstance) {
            this.revenueChartInstance.data.labels = labels;
            this.revenueChartInstance.data.datasets[0].data = values;
            this.revenueChartInstance.update();
            return;
        }

        if (!hasData) return;

        this.revenueChartInstance = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: CHART_COLORS.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: "#fff",
                    hoverBorderWidth: 3,
                    hoverOffset: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "55%",
                plugins: {
                    legend: {
                        position: "right",
                        labels: {
                            padding: 14,
                            usePointStyle: true,
                            pointStyle: "circle",
                            font: { size: 11, weight: "500" },
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label(ctx) {
                                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                                return ` ${ctx.label}: ${ctx.raw.toLocaleString()} (${pct}%)`;
                            },
                        },
                    },
                },
            },
        });
    }

    renderBarChart(canvasRef, instanceKey, data, color, gradientEnd) {
        const canvas = canvasRef();
        if (!canvas) return;
        const Chart = window.Chart;
        if (!Chart) return;

        const labels = (data || []).map((d) => d.label);
        const values = (data || []).map((d) => d.value);

        if (this[instanceKey]) {
            this[instanceKey].data.labels = labels;
            this[instanceKey].data.datasets[0].data = values;
            this[instanceKey].update();
            return;
        }

        if (!values.some((v) => v > 0)) return;

        const ctx = canvas.getContext("2d");
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.parentElement.clientHeight || 180);
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, gradientEnd);

        this[instanceKey] = new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: gradient,
                    borderRadius: 4,
                    borderSkipped: false,
                    maxBarThickness: 32,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) => items[0].label,
                            label: (ctx) => ` Count: ${ctx.raw}`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 10 }, maxRotation: 0 },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: "#eef1f4" },
                        ticks: {
                            font: { size: 10 },
                            precision: 0,
                        },
                    },
                },
            },
        });
    }

    renderAttendanceChart() {
        this.renderBarChart(
            this.attendanceChartRef,
            "attendanceChartInstance",
            this.state.chartData.attendance_daily,
            "#3949ab",
            "#7986cb"
        );
    }

    renderVisitorsChart() {
        this.renderBarChart(
            this.visitorsChartRef,
            "visitorsChartInstance",
            this.state.chartData.visitors_daily,
            "#00796b",
            "#4db6ac"
        );
    }

    // -------------------------------------------------------------------------
    // Data loading
    // -------------------------------------------------------------------------

    getDateParams() {
        const fromVal = typeof this.state.date_from === "string" ? this.state.date_from.trim() : this.state.date_from;
        const toVal = typeof this.state.date_to === "string" ? this.state.date_to.trim() : this.state.date_to;
        return [fromVal || null, toVal || null];
    }

    getEmptyChartData() {
        return {
            occupancy_by_building: [],
            revenue_monthly: [],
            attendance_daily: [],
            visitors_daily: [],
            maintenance_by_state: [],
        };
    }

    async loadStatistics() {
        this.state.loading = true;
        const [dateFrom, dateTo] = this.getDateParams();
        try {
            const [stats, chartData] = await Promise.all([
                this.orm.call("hostel.dashboard", "get_statistics", [dateFrom, dateTo]),
                this.orm.call("hostel.dashboard", "get_chart_data", [dateFrom, dateTo]).catch((err) => {
                    console.error("Error loading chart data:", err);
                    return this.getEmptyChartData();
                }),
            ]);
            this.state.statistics = stats || this.state.statistics;
            this.state.chartData = chartData && typeof chartData === "object"
                ? { ...this.getEmptyChartData(), ...chartData }
                : this.getEmptyChartData();
        } catch (error) {
            console.error("Error loading dashboard statistics:", error);
        } finally {
            this.state.loading = false;
        }
    }

    // -------------------------------------------------------------------------
    // Date filter handlers
    // -------------------------------------------------------------------------

    async onApplyDateRange() {
        await this.loadStatistics();
    }

    onDateFromChange(ev) {
        this.state.date_from = ev.target.value || "";
    }

    onDateToChange(ev) {
        this.state.date_to = ev.target.value || "";
    }

    onResetDateRange() {
        const defaultRange = getDefaultDateRange();
        this.state.date_from = defaultRange.date_from;
        this.state.date_to = defaultRange.date_to;
        this.loadStatistics();
    }

    // -------------------------------------------------------------------------
    // Action handlers (model methods)
    // -------------------------------------------------------------------------

    async openAction(actionName) {
        try {
            const action = await this.orm.call("hostel.dashboard", actionName, []);
            if (action) {
                this.actionService.doAction(action);
            }
        } catch (error) {
            console.error(`Error opening action ${actionName}:`, error);
        }
    }

    onDailyCheckin() { this.openAction("action_daily_checkin"); }
    onDailyContractEnding() { this.openAction("action_daily_contract_ending"); }
    onActiveStudents() { this.openAction("action_active_students"); }
    onVacantSpaces() { this.openAction("action_vacant_spaces"); }
    onUpcoming30Days() { this.openAction("action_upcoming_30_days"); }
    onUpcoming10Days() { this.openAction("action_upcoming_10_days"); }
    onVisitorsToday() { this.openAction("action_visitors_today"); }
    onPendingVisitors() { this.openAction("action_pending_visitors"); }
    onMaintenanceOpen() { this.openAction("action_maintenance_open"); }
    onRentInvoices() { this.openAction("action_rent_invoices"); }
    onStudentAttendance() { this.openAction("action_student_attendance"); }
    onComplaintsOpen() { this.openAction("action_complaints_open"); }
    onLaundryOpen() { this.openAction("action_laundry_open"); }
    onRoomInspections() { this.openAction("action_room_inspections"); }
    onAnnouncements() { this.openAction("action_announcements"); }

    // -------------------------------------------------------------------------
    // Quick action handlers (XML ID based)
    // -------------------------------------------------------------------------

    async onQuickAction(actionXmlId) {
        try {
            const fullXmlId = actionXmlId.includes(".") ? actionXmlId : `sirita_mahad.${actionXmlId}`;
            await this.actionService.doAction(fullXmlId);
        } catch (error) {
            console.error(`Error opening quick action ${actionXmlId}:`, error);
        }
    }

    onViewContracts() { this.onQuickAction("action_contract"); }
    onCheckInOut() { this.onQuickAction("action_checkin"); }
    onManageRooms() { this.onQuickAction("action_room"); }
    onSendCommunication() { this.onQuickAction("action_group_communication"); }
    onVisitors() { this.onQuickAction("action_visitor"); }
    onComplaints() { this.onQuickAction("action_complaint"); }
    onExportContracts() { this.onQuickAction("action_contract"); }
    onAnnouncementsMenu() { this.onQuickAction("action_notice_board"); }
}

HostelDashboard.template = "sirita_mahad.HostelDashboard";

registry.category("actions").add(
    "sirita_mahad.dashboard",
    HostelDashboard
);
