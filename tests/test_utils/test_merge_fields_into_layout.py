import xml.etree.ElementTree as ET
import pytest
from app import merge_fields_into_layout
from tests.logger_config import setup_test_logger

logger = setup_test_logger(__name__)

def test_merge_fields_into_layout():
    logger.info("Starting test: merge_fields_into_layout")

    original_layout = """<?xml version="1.0" encoding="UTF-8"?>
<Layout xmlns="http://soap.sforce.com/2006/04/metadata">
    <layoutSections>
        <customLabel>true</customLabel>
        <detailHeading>true</detailHeading>
        <editHeading>true</editHeading>
        <label>Information</label>
        <layoutColumns>
            <layoutItems>
                <behavior>Edit</behavior>
                <field>AccountNumber</field>
            </layoutItems>
        </layoutColumns>
        <layoutColumns/>
        <style>TwoColumnsTopToBottom</style>
    </layoutSections>
</Layout>"""

    fields_to_add = ["Test_Field_1__c", "Test_Field_2__c"]
    updated_layout = merge_fields_into_layout(original_layout, fields_to_add)

    # Parse output
    ns = {"ns": "http://soap.sforce.com/2006/04/metadata"}
    root = ET.fromstring(updated_layout)

    sections = root.findall("ns:layoutSections", ns)
    assert len(sections) >= 2

    last_section = sections[-1]
    label = last_section.find("ns:label", ns).text
    assert label == "Custom Fields"

    style = last_section.find("ns:style", ns).text
    assert style == "TwoColumnsTopToBottom"

    added_fields = last_section.find("ns:layoutColumns", ns).findall("ns:layoutItems", ns)
    found_fields = [item.find("ns:field", ns).text for item in added_fields]
    assert set(found_fields) == set(fields_to_add)

    logger.info("merge_fields_into_layout passed with expected fields and section")
