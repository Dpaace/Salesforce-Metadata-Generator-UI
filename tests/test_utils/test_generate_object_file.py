import xml.etree.ElementTree as ET
import pytest
from app import generate_object_file
from tests.logger_config import setup_test_logger

logger = setup_test_logger(__name__)

def test_generate_object_file_with_text_and_number_fields():
    logger.info("Starting test: generate_object_file_with_text_and_number_fields")

    object_name = "Test_Object__c"
    fields = [
        {
            "apiName": "Text_Field__c",
            "label": "Text Field",
            "type": "Text",
            "required": True
        },
        {
            "apiName": "Number_Field__c",
            "label": "Number Field",
            "type": "Number"
        }
    ]

    xml_output = generate_object_file(object_name, fields)

    assert "<fullName>Text_Field__c</fullName>" in xml_output
    assert "<type>Text</type>" in xml_output
    assert "<required>true</required>" in xml_output

    assert "<fullName>Number_Field__c</fullName>" in xml_output
    assert "<type>Number</type>" in xml_output
    assert "<precision>18</precision>" in xml_output
    assert "<scale>2</scale>" in xml_output

    assert "<deploymentStatus>Deployed</deploymentStatus>" in xml_output
    assert "<sharingModel>ReadWrite</sharingModel>" in xml_output

    logger.info("Test passed: Text and Number fields were correctly generated")


def test_generate_object_file_with_picklist():
    logger.info("Starting test: generate_object_file_with_picklist")

    object_name = "Picklist_Object__c"
    fields = [
        {
            "apiName": "Status__c",
            "label": "Status",
            "type": "Picklist",
            "picklistValues": ["New", "In Progress", "Completed"]
        }
    ]

    xml_output = generate_object_file(object_name, fields)

    assert "<type>Picklist</type>" in xml_output
    assert "<valueSetDefinition>" in xml_output
    assert "<fullName>New</fullName>" in xml_output
    assert "<fullName>Completed</fullName>" in xml_output

    logger.info("Test passed: Picklist field generated with all values")
