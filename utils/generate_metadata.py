import os

def create_metadata_folder(base_path, object_label, object_api_name, plural_label, fields):
    object_folder = os.path.join(base_path, 'objects')
    layout_folder = os.path.join(base_path, 'layouts')
    tab_folder = os.path.join(base_path, 'tabs')
    profile_folder = os.path.join(base_path, 'profiles')

    os.makedirs(object_folder, exist_ok=True)
    os.makedirs(layout_folder, exist_ok=True)
    os.makedirs(tab_folder, exist_ok=True)
    os.makedirs(profile_folder, exist_ok=True)

    # Ensure __c is added only once
    if not object_api_name.endswith('__c'):
        object_api_full = f"{object_api_name}__c"
    else:
        object_api_full = object_api_name

    # Write files
    with open(os.path.join(object_folder, f"{object_api_full}.object"), 'w') as f:
        f.write(generate_object_xml(object_label, plural_label, object_api_full, fields))

    with open(os.path.join(layout_folder, f"{object_api_full}-{object_label} Layout.layout"), 'w') as f:
        f.write(generate_layout_xml(object_api_full, fields))

    with open(os.path.join(tab_folder, f"{object_api_full}.tab"), 'w') as f:
        f.write(generate_tab_xml(object_label, object_api_full))

    with open(os.path.join(profile_folder, "Admin.profile-meta.xml"), 'w') as f:
        f.write(generate_profile_xml(object_api_full, fields))

    with open(os.path.join(base_path, "package.xml"), 'w') as f:
        f.write(generate_package_xml(object_api_full, object_label))

def generate_object_xml(object_label, plural_label, api_name, fields):
    fields_xml = ""
    for field in fields:
        field_name = field['apiName'] or field['label'].replace(' ', '_') + '__c'
        field_type = field['type']
        length_tag = ""

        if field_type == 'Text':
            length_tag = "<length>100</length>"

        field_xml = f"""
    <fields>
        <fullName>{field_name}</fullName>
        <label>{field['label']}</label>
        <type>{field_type}</type>
        {length_tag}
    </fields>"""
        fields_xml += field_xml

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>{object_label}</label>
    <pluralLabel>{plural_label}</pluralLabel>
    <nameField>
        <label>{object_label} Name</label>
        <type>Text</type>
    </nameField>
    <deploymentStatus>Deployed</deploymentStatus>
    <sharingModel>ReadWrite</sharingModel>
    {fields_xml}
</CustomObject>"""

def generate_layout_xml(api_name, fields):
    layout_items = """
            <layoutItems>
                <behavior>Required</behavior>
                <field>Name</field>
            </layoutItems>"""

    for field in fields:
        field_name = field['apiName'] or field['label'].replace(' ', '_') + '__c'
        layout_items += f"""
            <layoutItems>
                <field>{field_name}</field>
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

def generate_tab_xml(object_label, api_name):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>{api_name}</fullName>
    <label>{object_label}</label>
    <customObject>true</customObject>
    <motif>Custom41: Handsaw</motif>
</CustomTab>"""

def generate_profile_xml(api_name, fields):
    field_permissions = ""
    for field in fields:
        field_name = field['apiName'] or field['label'].replace(' ', '_') + '__c'
        field_permissions += f"""
    <fieldPermissions>
        <field>{api_name}.{field_name}</field>
        <readable>true</readable>
        <editable>true</editable>
    </fieldPermissions>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <tabVisibilities>
        <tab>{api_name}</tab>
        <visibility>DefaultOn</visibility>
    </tabVisibilities>

    <objectPermissions>
        <object>{api_name}</object>
        <allowCreate>true</allowCreate>
        <allowRead>true</allowRead>
        <allowEdit>true</allowEdit>
        <allowDelete>true</allowDelete>
        <modifyAllRecords>true</modifyAllRecords>
        <viewAllRecords>true</viewAllRecords>
    </objectPermissions>
    {field_permissions}
</Profile>"""

def generate_package_xml(api_name, object_label):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>{api_name}</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>{api_name}</members>
        <name>CustomTab</name>
    </types>
    <types>
        <members>{api_name}-{object_label} Layout</members>
        <name>Layout</name>
    </types>
    <types>
        <members>Admin</members>
        <name>Profile</name>
    </types>
    <version>63.0</version>
</Package>"""
