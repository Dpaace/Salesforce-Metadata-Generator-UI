import os

def create_metadata_folder(base_path, objects, access_token=None, instance_url=None):
    object_folder = os.path.join(base_path, 'objects')
    fields_folder = os.path.join(base_path, 'objects/fields')
    layout_folder = os.path.join(base_path, 'layouts')
    tab_folder = os.path.join(base_path, 'tabs')
    profile_folder = os.path.join(base_path, 'profiles')

    os.makedirs(object_folder, exist_ok=True)
    os.makedirs(fields_folder, exist_ok=True)
    os.makedirs(layout_folder, exist_ok=True)
    os.makedirs(tab_folder, exist_ok=True)
    os.makedirs(profile_folder, exist_ok=True)

    custom_objects = []
    standard_fields = []

    for obj in objects:
        label = obj['objectLabel']
        api = obj['objectApiName']
        plural = obj['objectPluralLabel']
        fields = obj['fields']
        is_custom = obj.get('objectType', 'custom') == 'custom'

        if is_custom:
            if not api.endswith('__c'):
                api += '__c'
            custom_objects.append(api)

            # Create .object file
            with open(os.path.join(object_folder, f"{api}.object"), 'w') as f:
                f.write(generate_object_xml(label, plural, api, fields))

            # Create layout
            # with open(os.path.join(layout_folder, f"{api}-{label} Layout.layout"), 'w') as f:
            #     f.write(generate_layout_xml(api, fields))
            
            from retrieve_layout import (
                retrieve_layout_metadata,
                check_retrieve_status,
                extract_layout_from_response,
                generate_layout_xml  # Make sure to import this updated version
            )
            import time

            layout_filename = f"{api}-{label} Layout"
            layout_file_path = os.path.join(layout_folder, f"{layout_filename}.layout")

            existing_layout_xml = None
            if access_token and instance_url:
                try:
                    retrieve_id = retrieve_layout_metadata(access_token, instance_url, layout_filename)
                    for _ in range(10):
                        status_response = check_retrieve_status(access_token, instance_url, retrieve_id)
                        existing_layout_xml = extract_layout_from_response(status_response)
                        if existing_layout_xml:
                            break
                        time.sleep(3)
                except Exception as e:
                    print(f"[!] Layout retrieval failed: {e}")

            merged_layout_xml = generate_layout_xml(api, fields, existing_layout_xml)
            with open(layout_file_path, "w", encoding="utf-8") as f:
                f.write(merged_layout_xml)


            # Create tab
            with open(os.path.join(tab_folder, f"{api}.tab"), 'w') as f:
                f.write(generate_tab_xml(label, api))
        else:
            # Treat as standard object (e.g., Account, Contact)
            for field in fields:
                field_name = field['apiName'] or field['label'].replace(' ', '_') + '__c'
                standard_fields.append({
                    'object': api,
                    'field': field_name,
                    'label': field['label'],
                    'type': field['type']
                })

                # Create field-meta.xml file
                with open(os.path.join(fields_folder, f"{api}.{field_name}.field-meta.xml"), 'w') as f:
                    f.write(generate_custom_field_xml(field_name, field['label'], field['type']))

    # Write profile
    with open(os.path.join(profile_folder, "Admin.profile-meta.xml"), 'w') as f:
        f.write(generate_profile_xml(custom_objects, objects, standard_fields))

    # Write package.xml
    with open(os.path.join(base_path, "package.xml"), 'w') as f:
        f.write(generate_package_xml(custom_objects, objects, standard_fields))


def generate_object_xml(label, plural, api_name, fields):
    fields_xml = ""
    for field in fields:
        name = field['apiName'] or field['label'].replace(' ', '_') + '__c'
        typ = field['type']
        length = "<length>100</length>" if typ == 'Text' else ""

        fields_xml += f"""
    <fields>
        <fullName>{name}</fullName>
        <label>{field['label']}</label>
        <type>{typ}</type>
        {length}
    </fields>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>{label}</label>
    <pluralLabel>{plural}</pluralLabel>
    <nameField>
        <label>{label} Name</label>
        <type>Text</type>
    </nameField>
    <deploymentStatus>Deployed</deploymentStatus>
    <sharingModel>ReadWrite</sharingModel>
    {fields_xml}
</CustomObject>"""


def generate_layout_xml_old(api_name, fields):
    layout_items = """
            <layoutItems>
                <behavior>Required</behavior>
                <field>Name</field>
            </layoutItems>"""

    for field in fields:
        name = field['apiName'] or field['label'].replace(' ', '_') + '__c'
        layout_items += f"""
            <layoutItems>
                <field>{name}</field>
            </layoutItems>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Layout xmlns="http://soap.sforce.com/2006/04/metadata">
    <layoutSections>
        <customLabel>false</customLabel>
        <detailHeading>true</detailHeading>
        <editHeading>true</editHeading>
        <label>Information</label>
        <layoutColumns>
            {layout_items}
        </layoutColumns>
        <style>TwoColumnsTopToBottom</style>
    </layoutSections>
</Layout>"""


def generate_tab_xml(label, api_name):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>{api_name}</fullName>
    <label>{label}</label>
    <customObject>true</customObject>
    <motif>Custom41: Handsaw</motif>
</CustomTab>"""


def generate_profile_xml(custom_object_apis, custom_objects, standard_fields):
    permissions = ""
    tab_visibilities = ""
    object_access = ""

    for obj, api in zip(custom_objects, custom_object_apis):
        # Add tab visibility
        tab_visibilities += f"""
    <tabVisibilities>
        <tab>{api}</tab>
        <visibility>DefaultOn</visibility>
    </tabVisibilities>"""

        # Add field permissions
        for field in obj['fields']:
            field_name = field['apiName'] or field['label'].replace(' ', '_') + '__c'
            permissions += f"""
    <fieldPermissions>
        <field>{api}.{field_name}</field>
        <readable>true</readable>
        <editable>true</editable>
    </fieldPermissions>"""

        # Add object permissions
        object_access += f"""
    <objectPermissions>
        <object>{api}</object>
        <allowCreate>true</allowCreate>
        <allowRead>true</allowRead>
        <allowEdit>true</allowEdit>
        <allowDelete>true</allowDelete>
        <modifyAllRecords>true</modifyAllRecords>
        <viewAllRecords>true</viewAllRecords>
    </objectPermissions>"""

    # Add standard field permissions
    for sf in standard_fields:
        permissions += f"""
    <fieldPermissions>
        <field>{sf['object']}.{sf['field']}</field>
        <readable>true</readable>
        <editable>true</editable>
    </fieldPermissions>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    {tab_visibilities}
    {permissions}
    {object_access}
</Profile>"""



def generate_custom_field_xml(field_name, label, field_type):
    length = "<length>100</length>" if field_type == "Text" else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>{field_name}</fullName>
    <label>{label}</label>
    <type>{field_type}</type>
    {length}
</CustomField>"""


def generate_package_xml(custom_object_apis, custom_objects, standard_fields):
    object_entries = "".join(f"<members>{api}</members>\n" for api in custom_object_apis)
    tab_entries = "".join(f"<members>{api}</members>\n" for api in custom_object_apis)
    layout_entries = "".join(
        f"<members>{api}-{obj['objectLabel']} Layout</members>\n"
        for api, obj in zip(custom_object_apis, custom_objects)
    )
    field_entries = "".join(
        f"<members>{sf['object']}.{sf['field']}</members>\n" for sf in standard_fields
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        {object_entries}<name>CustomObject</name>
    </types>
    <types>
        {tab_entries}<name>CustomTab</name>
    </types>
    <types>
        {layout_entries}<name>Layout</name>
    </types>
    <types>
        {field_entries}<name>CustomField</name>
    </types>
    <types>
        <members>Admin</members>
        <name>Profile</name>
    </types>
    <version>63.0</version>
</Package>"""
