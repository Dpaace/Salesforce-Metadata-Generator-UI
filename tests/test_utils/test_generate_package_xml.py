import pytest
from app import generate_package_xml
from tests.logger_config import setup_test_logger

logger = setup_test_logger(__name__)

def test_generate_package_xml():
    logger.info("Starting test: generate_package_xml")

    object_name = "MyObject__c"
    layout_name = "MyObject__c-MyObject Layout"

    xml = generate_package_xml(object_name, layout_name)

    assert "<members>MyObject__c</members>" in xml
    assert "<name>CustomObject</name>" in xml
    assert "<members>MyObject__c-MyObject Layout</members>" in xml
    assert "<name>Layout</name>" in xml
    assert "<members>Admin</members>" in xml
    assert "<name>Profile</name>" in xml
    assert "<version>63.0</version>" in xml

    logger.info("Test passed: generate_package_xml output structure is valid")
