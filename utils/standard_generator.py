import os
import time
import xml.etree.ElementTree as ET
from retrieve_standard_layout import (
    retrieve_layout_metadata,
    check_retrieve_status,
    extract_layout_from_response,
)


def merge_fields_into_layout(layout_xml: str, field_api_names: list[str]) -> str:
    ns = {"ns": "http://soap.sforce.com/2006/04/metadata"}
    ET.register_namespace("", ns["ns"])

    root = ET.fromstring(layout_xml)

    # Create new layout section
    section = ET.Element("layoutSections")
    ET.SubElement(section, "customLabel").text = "true"
    ET.SubElement(section, "detailHeading").text = "true"
    ET.SubElement(section, "editHeading").text = "true"
    ET.SubElement(section, "label").text = "Custom Fields"

    column1 = ET.SubElement(section, "layoutColumns")
    ET.SubElement(section, "layoutColumns")

    for api_name in field_api_names:
        layout_item = ET.Element("layoutItems")
        ET.SubElement(layout_item, "behavior").text = "Edit"
        ET.SubElement(layout_item, "field").text = api_name
        column1.append(layout_item)

    ET.SubElement(section, "style").text = "TwoColumnsTopToBottom"

    layout_sections = root.findall("ns:layoutSections", ns)
    if layout_sections:
        last_section = layout_sections[-1]
        index = list(root).index(last_section)
        root.insert(index + 1, section)
    else:
        root.append(section)

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        root, encoding="unicode"
    )


# def generate_object_file(object_name: str, fields: list[dict]) -> str:
#     field_blocks = "\n".join([
#         f"""    <fields>
#         <fullName>{f['apiName']}</fullName>
#         <externalId>false</externalId>
#         <label>{f['label']}</label>
#         <required>false</required>
#         <trackHistory>false</trackHistory>
#         <trackTrending>false</trackTrending>
#         <type>Text</type>
#         <length>255</length>
#     </fields>""" for f in fields
#     ])

#     return f"""<?xml version="1.0" encoding="UTF-8"?>
# <CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
# {field_blocks}
#     <deploymentStatus>Deployed</deploymentStatus>
#     <sharingModel>ReadWrite</sharingModel>
# </CustomObject>"""


# <required>{str(field.get('required', False)).lower()}</required>
def generate_object_file(object_name: str, fields: list[dict]) -> str:
    def build_field_block(field: dict) -> str:
        base = f"""    <fields>
        <fullName>{field['apiName']}</fullName>
        <externalId>false</externalId>
        <label>{field['label']}</label>
        <required>false</required>
        <trackHistory>false</trackHistory>
        <trackTrending>false</trackTrending>"""

        field_type = field.get("type", "Text")

        if field_type == "Text":
            base += f"""
        <type>Text</type>
        <length>255</length>
        </fields>"""
        elif field_type == "Number":
            base += f"""
        <type>Number</type>
        <precision>18</precision>
        <scale>2</scale>
        </fields>"""
        elif field_type == "Date":
            base += f"""
        <type>Date</type>
        </fields>"""
        elif field_type == "Checkbox":
            base += f"""
        <type>Checkbox</type>
        <defaultValue>false</defaultValue>
        </fields>"""
        elif field_type == "Picklist":
            picklist_vals = field.get("picklistValues", "")
            picklist_items = []

            # Support both string and list inputs
            if isinstance(picklist_vals, str):
                picklist_items = [
                    v.strip() for v in picklist_vals.split(",") if v.strip()
                ]
            elif isinstance(picklist_vals, list):
                picklist_items = [
                    v.strip() for v in picklist_vals if isinstance(v, str) and v.strip()
                ]

            picklist_entries = ""
            for val in picklist_items:
                picklist_entries += f"""
                <value>
                    <fullName>{val}</fullName>
                    <default>false</default>
                </value>"""

            base += f"""
                <type>Picklist</type>
                <valueSet>
                    <valueSetDefinition>
                        {picklist_entries}
                    </valueSetDefinition>
                    <restricted>true</restricted>
                </valueSet>
                </fields>"""
        return base

    field_blocks = "\n".join([build_field_block(f) for f in fields])

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
{field_blocks}
    <deploymentStatus>Deployed</deploymentStatus>
    <sharingModel>ReadWrite</sharingModel>
</CustomObject>"""


# def generate_profile_xml(object_name: str, fields: list[dict]) -> str:
#     permissions = "\n".join(
#         [
#             f"""    <fieldPermissions>
#         <field>{object_name}.{f['apiName']}</field>
#         <readable>true</readable>
#         <editable>true</editable>
#     </fieldPermissions>"""
#             for f in fields
#         ]
#     )
#     return f"""<?xml version="1.0" encoding="UTF-8"?>
# <Profile xmlns="http://soap.sforce.com/2006/04/metadata">
# {permissions}
# </Profile>"""


def generate_profile_xml(objects: list[dict]) -> str:
    permissions = []

    for obj in objects:
        object_name = obj.get("objectApiName")
        fields = obj.get("fields", [])
        for f in fields:
            permissions.append(
                f"""    <fieldPermissions>
        <field>{object_name}.{f['apiName']}</field>
        <readable>true</readable>
        <editable>true</editable>
    </fieldPermissions>"""
            )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
{chr(10).join(permissions)}
</Profile>"""


def generate_package_xml(object_name: str, layout_name: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>{object_name}</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>{layout_name}</members>
        <name>Layout</name>
    </types>
    <types>
        <members>Admin</members>
        <name>Profile</name>
    </types>
    <version>63.0</version>
</Package>"""


# def create_standard_metadata_folder(base_path, objects, access_token, instance_url):
#     layout_folder = os.path.join(base_path, "layouts")
#     object_folder = os.path.join(base_path, "objects")
#     profile_folder = os.path.join(base_path, "profiles")

#     os.makedirs(layout_folder, exist_ok=True)
#     os.makedirs(object_folder, exist_ok=True)
#     os.makedirs(profile_folder, exist_ok=True)

#     for obj in objects:
#         object_name = obj["objectApiName"]
#         fields = obj["fields"]
#         layout_name = f"{object_name}-{object_name} Layout"

#         try:
#             retrieve_id = retrieve_layout_metadata(
#                 access_token, instance_url, layout_name
#             )
#             for _ in range(10):
#                 status_response = check_retrieve_status(
#                     access_token, instance_url, retrieve_id
#                 )
#                 layout_xml = extract_layout_from_response(status_response)
#                 if layout_xml:
#                     break
#                 time.sleep(2)
#         except Exception as e:
#             print(f"[!] Failed to retrieve layout for {layout_name}: {e}")
#             raise

#         merged_layout = merge_fields_into_layout(
#             layout_xml, [f["apiName"] for f in fields]
#         )
#         with open(
#             os.path.join(layout_folder, f"{layout_name}.layout"), "w", encoding="utf-8"
#         ) as f:
#             f.write(merged_layout)

#         object_xml = generate_object_file(object_name, fields)
#         with open(
#             os.path.join(object_folder, f"{object_name}.object"), "w", encoding="utf-8"
#         ) as f:
#             f.write(object_xml)

#         profile_xml = generate_profile_xml(object_name, fields)
#         with open(
#             os.path.join(profile_folder, "Admin.profile-meta.xml"),
#             "w",
#             encoding="utf-8",
#         ) as f:
#             f.write(profile_xml)

#         package_xml = generate_package_xml(object_name, layout_name)
#         with open(os.path.join(base_path, "package.xml"), "w", encoding="utf-8") as f:
#             f.write(package_xml)


def generate_combined_package_xml(
    object_names: list[str], layout_names: list[str]
) -> str:
    object_entries = "\n".join(
        [f"        <members>{name}</members>" for name in object_names]
    )
    layout_entries = "\n".join(
        [f"        <members>{name}</members>" for name in layout_names]
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
{object_entries}
        <name>CustomObject</name>
    </types>
    <types>
{layout_entries}
        <name>Layout</name>
    </types>
    <types>
        <members>Admin</members>
        <name>Profile</name>
    </types>
    <version>63.0</version>
</Package>"""


def create_standard_metadata_folder(base_path, objects, access_token, instance_url):
    layout_folder = os.path.join(base_path, "layouts")
    object_folder = os.path.join(base_path, "objects")
    profile_folder = os.path.join(base_path, "profiles")

    os.makedirs(layout_folder, exist_ok=True)
    os.makedirs(object_folder, exist_ok=True)
    os.makedirs(profile_folder, exist_ok=True)

    all_layout_names = []
    all_object_names = []

    for obj in objects:
        object_name = obj["objectApiName"]
        fields = obj["fields"]
        layout_name = f"{object_name}-{object_name} Layout"

        # --- Retrieve and merge layout ---
        try:
            retrieve_id = retrieve_layout_metadata(
                access_token, instance_url, layout_name
            )
            for _ in range(10):
                status_response = check_retrieve_status(
                    access_token, instance_url, retrieve_id
                )
                layout_xml = extract_layout_from_response(status_response)
                if layout_xml:
                    break
                time.sleep(2)
        except Exception as e:
            print(f"[!] Failed to retrieve layout for {layout_name}: {e}")
            raise

        merged_layout = merge_fields_into_layout(
            layout_xml, [f["apiName"] for f in fields]
        )
        with open(
            os.path.join(layout_folder, f"{layout_name}.layout"), "w", encoding="utf-8"
        ) as f:
            f.write(merged_layout)

        # --- Generate object XML ---
        object_xml = generate_object_file(object_name, fields)
        with open(
            os.path.join(object_folder, f"{object_name}.object"), "w", encoding="utf-8"
        ) as f:
            f.write(object_xml)

        all_layout_names.append(layout_name)
        all_object_names.append(object_name)

    # ✅ Generate combined Admin profile for all objects
    profile_xml = generate_profile_xml(objects)
    with open(
        os.path.join(profile_folder, "Admin.profile-meta.xml"), "w", encoding="utf-8"
    ) as f:
        f.write(profile_xml)

    # ✅ Generate combined package.xml
    package_xml = generate_combined_package_xml(all_object_names, all_layout_names)
    with open(os.path.join(base_path, "package.xml"), "w", encoding="utf-8") as f:
        f.write(package_xml)
