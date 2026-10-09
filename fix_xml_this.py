import re

with open("static/src/xml/hostel_dashboard.xml", "r") as f:
    xml = f.read()

# Replace state. with this.state.
xml = re.sub(r'(?<!this\.)state\.', 'this.state.', xml)

# Handlers
handlers = [
    "onApplyDateRange", "onDateFromChange", "onDateToChange", "onResetDateRange",
    "onDailyCheckin", "onDailyContractEnding", "onActiveStudents", "onVacantSpaces",
    "onUpcoming30Days", "onUpcoming10Days", "onVisitorsToday", "onPendingVisitors",
    "onMaintenanceOpen", "onRentInvoices", "onStudentAttendance", "onComplaintsOpen",
    "onLaundryOpen", "onRoomInspections", "onAnnouncements", "onViewContracts",
    "onCheckInOut", "onManageRooms", "onSendCommunication", "onVisitors",
    "onComplaints", "onExportContracts", "onAnnouncementsMenu"
]

for h in handlers:
    xml = re.sub(rf'(?<!this\.){h}', f'this.{h}', xml)

with open("static/src/xml/hostel_dashboard.xml", "w") as f:
    f.write(xml)

print("Updated XML successfully.")
