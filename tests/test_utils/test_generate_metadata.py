import pytest
from utils.generate_metadata import (
    generate_object_xml,
    generate_tab_xml,
    generate_profile_xml,
    generate_custom_field_xml,
    generate_package_xml,
)
import xml.etree.ElementTree as ET


def test_generate_object_xml():
    label = "Test Object"
    plural = "Test Objects"
    api_name = "TestObject__c"
    fields = [
        {"apiName": "Test_Field__c", "label": "Test Field", "type": "Text"},
        {"apiName": "Amount__c", "label": "Amount", "type": "Number"},
    ]

    xml_output = generate_object_xml(label, plural, api_name, fields)

    # Assert key strings are in the XML
    assert "<label>Test Object</label>" in xml_output
    assert "<pluralLabel>Test Objects</pluralLabel>" in xml_output
    assert "<fullName>Test_Field__c</fullName>" in xml_output
    assert "<type>Text</type>" in xml_output
    assert "<fullName>Amount__c</fullName>" in xml_output
    assert "<type>Number</type>" in xml_output

    # Ensure it's valid XML
    try:
        root = ET.fromstring(xml_output)
        assert root.tag.endswith("CustomObject")
    except ET.ParseError:
        pytest.fail("Output is not valid XML")


def test_generate_tab_xml():
    label = "Test Tab"
    api_name = "TestObject__c"

    xml_output = generate_tab_xml(label, api_name)

    assert "<fullName>TestObject__c</fullName>" in xml_output
    assert "<label>Test Tab</label>" in xml_output
    assert "<customObject>true</customObject>" in xml_output
    assert "<motif>Custom41: Handsaw</motif>" in xml_output

    # Ensure it's valid XML
    try:
        root = ET.fromstring(xml_output)
        assert root.tag.endswith("CustomTab")
    except ET.ParseError:
        pytest.fail("Invalid XML returned by generate_tab_xml")


def test_generate_profile_xml():
    custom_object_apis = ["TestObject__c"]
    custom_objects = [
        {
            "objectLabel": "Test Object",
            "fields": [
                {"apiName": "Field_One__c", "label": "Field One", "type": "Text"},
                {"apiName": "Field_Two__c", "label": "Field Two", "type": "Checkbox"},
            ],
        }
    ]
    standard_fields = [
        {"object": "Account", "field": "Phone"},
        {"object": "Contact", "field": "Email"},
    ]

    xml_output = generate_profile_xml(
        custom_object_apis, custom_objects, standard_fields
    )

    assert "<tab>TestObject__c</tab>" in xml_output
    assert "<field>TestObject__c.Field_One__c</field>" in xml_output
    assert "<field>Account.Phone</field>" in xml_output
    assert "<object>TestObject__c</object>" in xml_output

    try:
        root = ET.fromstring(xml_output)
        assert root.tag.endswith("Profile")
    except ET.ParseError:
        pytest.fail("Invalid XML returned by generate_profile_xml")


def test_generate_custom_field_text_type():
    xml_output = generate_custom_field_xml("Region__c", "Region", "Text")

    assert "<fullName>Region__c</fullName>" in xml_output
    assert "<label>Region</label>" in xml_output
    assert "<type>Text</type>" in xml_output
    assert "<length>100</length>" in xml_output

    try:
        root = ET.fromstring(xml_output)
        assert root.tag.endswith("CustomField")
    except ET.ParseError:
        pytest.fail("Invalid XML returned by generate_custom_field_xml")


def test_generate_custom_field_non_text_type():
    xml_output = generate_custom_field_xml("IsActive__c", "Is Active", "Checkbox")

    assert "<type>Checkbox</type>" in xml_output
    assert "<length>100</length>" not in xml_output  # Should not include length

    try:
        root = ET.fromstring(xml_output)
        assert root.tag.endswith("CustomField")
    except ET.ParseError:
        pytest.fail("Invalid XML returned by generate_custom_field_xml")


def test_generate_package_xml_structure():
    custom_object_apis = ["Region__c"]
    custom_objects = [{"objectLabel": "Region", "fields": []}]
    standard_fields = [
        {"object": "Account", "field": "Industry"},
        {"object": "Contact", "field": "Phone"},
    ]

    xml_output = generate_package_xml(
        custom_object_apis, custom_objects, standard_fields
    )

    assert "<members>Region__c</members>" in xml_output
    assert "<name>CustomObject</name>" in xml_output
    assert "<name>CustomField</name>" in xml_output
    assert "<members>Account.Industry</members>" in xml_output
    assert "<members>Region__c-Region Layout</members>" in xml_output
    assert "<version>63.0</version>" in xml_output

    try:
        root = ET.fromstring(xml_output)
        assert root.tag.endswith("Package")
    except ET.ParseError:
        pytest.fail("Invalid XML returned by generate_package_xml")
