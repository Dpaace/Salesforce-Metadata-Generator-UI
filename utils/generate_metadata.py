import os

def create_metadata_folder(base_path, objects):
    # Create necessary folders
    os.makedirs(base_path, exist_ok=True)
    os.makedirs(os.path.join(base_path, 'objects'), exist_ok=True)
    os.makedirs(os.path.join(base_path, 'objects', 'fields'), exist_ok=True)
    os.makedirs(os.path.join(base_path, 'layouts'), exist_ok=True)
    os.makedirs(os.path.join(base_path, 'tabs'), exist_ok=True)
    os.makedirs(os.path.join(base_path, 'profiles'), exist_ok=True)

    custom_objects = []
    custom_labels = []
    standard_fields = []
    profile_fields = []

    for obj in objects:
        obj_label = obj['objectLabel']
        obj_api = obj['objectApiName']
        obj_plural = obj['objectPluralLabel']
        obj_type = obj.get('objectType', 'custom')
        fields = obj['fields']

        if obj_type == 'custom':
            if not obj_api.endswith('__c'):
                obj_api += '__c'
            custom_objects.append(obj_api)
            custom_labels.append(obj_label)

            # Create .object
            with open(os.path.join(base_path, 'objects', f"{obj_api}.object"), 'w') as f:
                f.write(generate_custom_object_xml(obj_label, obj_plural, obj_api, fields))

            # Create layout
            with open(os.path.join(base_path, 'layouts', f"{obj_api}-{obj_label} Layout.layout"), 'w') as f:
                f.write(generate_layout_xml(fields))

            # Create tab
            with open(os.path.join(base_path, 'tabs', f"{obj_api}.tab"), 'w') as f:
                f.write(generate_tab_xml(obj_api, obj_label))

            # Track for profile
            for field in fields:
                field_name = field['apiName'] or field['label'].replace(" ", "_") + '__c'
                profile_fields.append(f"{obj_api}.{field_name}")
        else:
            for field in fields:
                field_name = field['apiName'] or field['label'].replace(" ", "_") + '__c'
                standard_fields.append({'object': obj_api, 'field': field_name})
                profile_fields.append(f"{obj_api}.{field_name}")

                # Create field metadata file
                field_dir = os.path.join(base_path, 'objects', 'fields')
                with open(os.path.join(field_dir, f"{obj_api}.{field_name}.field-meta.xml"), 'w') as f:
                    f.write(generate_standard_field_xml(field_name, field['label'], field['type']))

    # Profile metadata
    with open(os.path.join(base_path, 'profiles', 'Admin.profile-meta.xml'), 'w') as f:
        f.write(generate_profile_xml(custom_objects, profile_fields))

    # Package.xml
    with open(os.path.join(base_path, 'package.xml'), 'w') as f:
        f.write(generate_package_xml(custom_objects, profile_fields, standard_fields))


def generate_custom_object_xml(label, plural, api_name, fields):
    fields_xml = ""
    for field in fields:
        field_name = field['apiName'] or field['label'].replace(" ", "_") + '__c'
        fields_xml += f"""
    <fields>
        <fullName>{field_name}</fullName>
        <label>{field['label']}</label>
        <type>{field['type']}</type>
        {"<length>100</length>" if field['type'] == "Text" else ""}
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

def generate_standard_field_xml(name, label, field_type):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>{name}</fullName>
    <label>{label}</label>
    <type>{field_type}</type>
    {"<length>100</length>" if field_type == "Text" else ""}
</CustomField>"""

def generate_layout_xml(fields):
    layout_items = ""
    for field in fields:
        field_name = field['apiName'] or field['label'].replace(" ", "_") + '__c'
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
        <layoutColumns>{layout_items}
        </layoutColumns>
        <style>TwoColumnsTopToBottom</style>
    </layoutSections>
</Layout>"""

def generate_tab_xml(api_name, label):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomTab xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>{api_name}</fullName>
    <label>{label}</label>
    <customObject>true</customObject>
    <motif>Custom41: Handsaw</motif>
</CustomTab>"""

def generate_profile_xml(object_names, field_permissions):
    object_xml = ""
    for obj in object_names:
        object_xml += f"""
    <objectPermissions>
        <object>{obj}</object>
        <allowCreate>true</allowCreate>
        <allowRead>true</allowRead>
        <allowEdit>true</allowEdit>
        <allowDelete>true</allowDelete>
        <modifyAllRecords>true</modifyAllRecords>
        <viewAllRecords>true</viewAllRecords>
    </objectPermissions>"""

    field_xml = ""
    for field in field_permissions:
        field_xml += f"""
    <fieldPermissions>
        <field>{field}</field>
        <readable>true</readable>
        <editable>true</editable>
    </fieldPermissions>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    {object_xml}
    {field_xml}
</Profile>"""

def generate_package_xml(custom_objects, field_permissions, standard_fields):
    types = []

    if custom_objects:
        types.append(f"""<types>
        {"".join(f"<members>{o}</members>" for o in custom_objects)}
        <name>CustomObject</name>
    </types>""")

        types.append(f"""<types>
        {"".join(f"<members>{o}</members>" for o in custom_objects)}
        <name>CustomTab</name>
    </types>""")

        types.append(f"""<types>
        {"".join(f"<members>{o}-{o.split('__')[0]} Layout</members>" for o in custom_objects)}
        <name>Layout</name>
    </types>""")

    if standard_fields:
        types.append(f"""<types>
        {"".join(f"<members>{f['object']}.{f['field']}</members>" for f in standard_fields)}
        <name>CustomField</name>
    </types>""")

    types.append("""<types>
        <members>Admin</members>
        <name>Profile</name>
    </types>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    {''.join(types)}
    <version>63.0</version>
</Package>"""
