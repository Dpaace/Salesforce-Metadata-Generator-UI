import pytest
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client

def pytest_html_report_title(report):
    report.title = "Salesforce Metadata Tool Test Report"

def pytest_html_results_summary(prefix, summary, postfix):
    prefix.extend([f"Environment: Local", f"Tested by: Dipesh Nepali"])
