import pytest
from utils.standard_generator import (
    merge_fields_into_layout,
    generate_object_file,
    generate_profile_xml,
    generate_package_xml,
    generate_combined_package_xml,
)
import xml.etree.ElementTree as ET


def test_merge_fields_into_layout():
    layout_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Layout xmlns="http://soap.sforce.com/2006/04/metadata">
</Layout>"""
    new_fields = ["Region__c", "Status__c"]
    updated_xml = merge_fields_into_layout(layout_xml, new_fields)

    assert "Region__c" in updated_xml
    assert "Status__c" in updated_xml

    try:
        root = ET.fromstring(updated_xml)
        assert root.tag.endswith("Layout")
    except ET.ParseError:
        pytest.fail("Invalid XML returned by merge_fields_into_layout")


def test_generate_object_file():
    fields = [
        {"apiName": "Region__c", "label": "Region", "type": "Text"},
        {"apiName": "IsActive__c", "label": "Is Active", "type": "Checkbox"},
    ]
    xml_output = generate_object_file("Account", fields)

    assert "<type>Text</type>" in xml_output
    assert "<type>Checkbox</type>" in xml_output

    try:
        root = ET.fromstring(xml_output)
        assert root.tag.endswith("CustomObject")
    except ET.ParseError:
        pytest.fail("Invalid XML returned by generate_object_file")


def test_generate_profile_xml():
    objects = [
        {
            "objectApiName": "Account",
            "fields": [
                {"apiName": "Region__c", "label": "Region", "type": "Text"},
                {"apiName": "Status__c", "label": "Status", "type": "Picklist"},
            ],
        }
    ]
    xml_output = generate_profile_xml(objects)

    assert "<field>Account.Region__c</field>" in xml_output
    assert "<field>Account.Status__c</field>" in xml_output

    try:
        root = ET.fromstring(xml_output)
        assert root.tag.endswith("Profile")
    except ET.ParseError:
        pytest.fail("Invalid XML returned by generate_profile_xml")


def test_generate_package_xml():
    xml_output = generate_package_xml("Account", "Account Layout")

    assert "<members>Account</members>" in xml_output
    assert "<members>Account Layout</members>" in xml_output
    assert "<name>CustomObject</name>" in xml_output

    try:
        root = ET.fromstring(xml_output)
        assert root.tag.endswith("Package")
    except ET.ParseError:
        pytest.fail("Invalid XML returned by generate_package_xml")


def test_generate_combined_package_xml():
    object_names = ["Account", "Contact"]
    layout_names = ["Account Layout", "Contact Layout"]

    xml_output = generate_combined_package_xml(object_names, layout_names)

    assert "<members>Account</members>" in xml_output
    assert "<members>Contact</members>" in xml_output
    assert "<members>Account Layout</members>" in xml_output

    try:
        root = ET.fromstring(xml_output)
        assert root.tag.endswith("Package")
    except ET.ParseError:
        pytest.fail("Invalid XML returned by generate_combined_package_xml")
