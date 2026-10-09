with open("static/src/xml/hostel_dashboard.xml", "r") as f:
    content = f.read()

content = content.replace('t-ref="revenueChart"', 't-ref="this.revenueChartRef"')
content = content.replace('t-ref="attendanceChart"', 't-ref="this.attendanceChartRef"')
content = content.replace('t-ref="visitorsChart"', 't-ref="this.visitorsChartRef"')

with open("static/src/xml/hostel_dashboard.xml", "w") as f:
    f.write(content)

