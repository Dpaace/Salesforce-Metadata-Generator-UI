import subprocess
import datetime
import os

os.makedirs("reports", exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
report_file = f"reports/test_report_{timestamp}.html"

subprocess.run([
    "pytest", "tests/",
    f"--html={report_file}",
    "--self-contained-html"
])
