import pytest
from app import generate_profile_xml
from tests.logger_config import setup_test_logger

logger = setup_test_logger(__name__)

def test_generate_profile_xml():
    logger.info("Starting test: generate_profile_xml")

    object_name = "Test_Object__c"
    fields = [
        {"apiName": "Field1__c"},
        {"apiName": "Field2__c"}
    ]

    xml = generate_profile_xml(object_name, fields, profile_name="Admin")

    assert "<Profile" in xml
    assert "<field>Test_Object__c.Field1__c</field>" in xml
    assert "<field>Test_Object__c.Field2__c</field>" in xml
    assert "<readable>true</readable>" in xml
    assert "<editable>true</editable>" in xml

    logger.info("Test passed: generate_profile_xml includes correct field permissions")
