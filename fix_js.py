import re

with open("static/src/js/hostel_dashboard.js", "r") as f:
    content = f.read()

# Replace imports
content = content.replace("useState, useRef", "proxy, signal")

# Replace setup methods
content = content.replace('useRef("revenueChart")', 'signal.ref()')
content = content.replace('useRef("attendanceChart")', 'signal.ref()')
content = content.replace('useRef("visitorsChart")', 'signal.ref()')
content = content.replace('useState({', 'proxy({')

# Replace .el calls
content = content.replace('this.revenueChartRef.el', 'this.revenueChartRef()')
content = content.replace('canvasRef.el', 'canvasRef()')

with open("static/src/js/hostel_dashboard.js", "w") as f:
    f.write(content)

