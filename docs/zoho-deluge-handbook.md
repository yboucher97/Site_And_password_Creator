# Zoho Deluge Handbook

This handbook shows how to call the Opticable API Platform from Zoho Deluge.

For the CRM and business-process design that should wrap these API calls, see [zoho-operating-model.md](./zoho-operating-model.md).

Current public base URL:

- `https://api01.opticable.ca`

Main workflow endpoint:

- `POST /v1/workflows/site-and-password`

Direct Omada-from-WorkDrive endpoint:

- `POST /v1/omada/workdrive/jobs`

Useful read endpoints:

- `GET /v1/workflows/site-and-password/jobs/{job_id}`
- `GET /v1/omada/jobs/{job_id}`
- `GET /v1/omada/sites`
- `GET /v1/omada/sites/{site_id}`
- `GET /v1/omada/sites/{site_id}/lans`
- `GET /v1/omada/sites/{site_id}/wlan-groups`
- `GET /v1/omada/sites/{site_id}/wlan-groups/{wlan_id}/ssids`
- `GET /v1/omada/sites/{site_id}/snapshot`

## 1. Deluge Setup

Use these variables in your Deluge functions:

```deluge
api_base = "https://api01.opticable.ca";
api_key = "REPLACE_WITH_YOUR_WORKFLOW_API_KEY";
```

Common header builder:

```deluge
get_opticable_headers()
{
	headers = Map();
	headers.put("X-API-Key",api_key);
	headers.put("Content-Type","application/json");
	return headers;
}
```

POST helper:

```deluge
opticable_post(path,payload)
{
	response = invokeurl
	[
		url : api_base + path
		type : POST
		headers : get_opticable_headers()
		body : payload.toString()
	];
	return response;
}
```

GET helper:

```deluge
opticable_get(path)
{
	response = invokeurl
	[
		url : api_base + path
		type : GET
		headers : get_opticable_headers()
	];
	return response;
}
```

## 2. Choose The Right Endpoint

Use `POST /v1/workflows/site-and-password` when you want:

- generated or predefined SSIDs/passwords
- PDFs
- TXT/ZIP exports
- WorkDrive upload
- optional Omada site creation

Use `POST /v1/omada/workdrive/jobs` when you want:

- read `create.yaml`, `upsert.yaml`, `update.yaml`, or TXT from WorkDrive
- create or modify Omada without running PDF generation

## 3. Common Workflow Fields

Canonical fields for the main workflow endpoint:

- `building_name`
- `city`
- `credential_mode`
  - `generated`
  - `predefined`
- `workflow_mode`
  - `pdf_only`
  - `pdf_and_site`
  - `site_only`
- `template_name`
  - currently use `Opticable_Template_01`
- `workdrive_folder_id`
- `site_name`
- `omada_operation`
  - `ensure`
  - `create`
  - `upsert`
  - `update`
- `omada_region`
- `omada_timezone`
- `omada_scenario`
- `hidden`
- `ssid_prefix`
- `ssid_template`
- `ssid_suffix_length`
- `password_specials`

Credential input styles:

- `records`
- or simple lists:
  - `units`
  - `ssids`
  - `passwords`
  - `unit_labels`
  - `vlans`

## 4. Most Common Workflow Scenarios

### A. Generate SSIDs and passwords, create PDFs only

Use when you want:

- `APT_101_XX` style SSIDs
- generated passwords
- PDF/TXT/ZIP/YA
- WorkDrive upload
- no Omada changes

```deluge
payload = Map();
payload.put("building_name","123 Main Street");
payload.put("credential_mode","generated");
payload.put("workflow_mode","pdf_only");
payload.put("template_name","Opticable_Template_01");
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");

units = List();
units.add("101");
units.add("102");
units.add("103");
payload.put("units",units);

response = opticable_post("/v1/workflows/site-and-password",payload);
info response;
```

### B. Generate SSIDs and passwords, create PDFs and Omada site

Use when you want the full flow.

```deluge
payload = Map();
payload.put("building_name","123 Main Street");
payload.put("site_name","123 Main Street");
payload.put("credential_mode","generated");
payload.put("workflow_mode","pdf_and_site");
payload.put("omada_operation","create");
payload.put("template_name","Opticable_Template_01");
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");
payload.put("omada_region","Canada");
payload.put("omada_timezone","America/Toronto");
payload.put("omada_scenario","Office");

units = List();
units.add("101");
units.add("102");
units.add("103");
payload.put("units",units);

response = opticable_post("/v1/workflows/site-and-password",payload);
info response;
```

### C. Generate passwords only for an existing site, then update Omada

Use when you want password rotation on an existing site.

```deluge
payload = Map();
payload.put("building_name","123 Main Street");
payload.put("site_name","123 Main Street");
payload.put("credential_mode","generated");
payload.put("workflow_mode","pdf_and_site");
payload.put("omada_operation","update");
payload.put("template_name","Opticable_Template_01");
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");

units = List();
units.add("101");
units.add("102");
units.add("103");
payload.put("units",units);

response = opticable_post("/v1/workflows/site-and-password",payload);
info response;
```

### D. Safe create-or-update run

Use when the site may already exist and you want missing pieces created, existing SSIDs updated in place.

```deluge
payload = Map();
payload.put("building_name","123 Main Street");
payload.put("site_name","123 Main Street");
payload.put("credential_mode","generated");
payload.put("workflow_mode","pdf_and_site");
payload.put("omada_operation","upsert");
payload.put("template_name","Opticable_Template_01");
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");

units = List();
units.add("101");
units.add("102");
payload.put("units",units);

response = opticable_post("/v1/workflows/site-and-password",payload);
info response;
```

### E. Predefined SSIDs and passwords, PDFs only

Use when Zoho already has the exact SSIDs and passwords.

```deluge
payload = Map();
payload.put("building_name","123 Main Street");
payload.put("credential_mode","predefined");
payload.put("workflow_mode","pdf_only");
payload.put("template_name","Opticable_Template_01");
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");

ssids = List();
ssids.add("APT_101_AA");
ssids.add("APT_102_BB");
payload.put("ssids",ssids);

passwords = List();
passwords.add("2249da8679!#");
passwords.add("4907ug5605$*");
payload.put("passwords",passwords);

response = opticable_post("/v1/workflows/site-and-password",payload);
info response;
```

### F. Predefined SSIDs and passwords, site only

Use when you do not want PDFs, only Omada creation/modification.

```deluge
payload = Map();
payload.put("building_name","123 Main Street");
payload.put("site_name","123 Main Street");
payload.put("credential_mode","predefined");
payload.put("workflow_mode","site_only");
payload.put("omada_operation","create");
payload.put("template_name","Opticable_Template_01");
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");

ssids = List();
ssids.add("APT_101_AA");
ssids.add("APT_102_BB");
payload.put("ssids",ssids);

passwords = List();
passwords.add("2249da8679!#");
passwords.add("4907ug5605$*");
payload.put("passwords",passwords);

response = opticable_post("/v1/workflows/site-and-password",payload);
info response;
```

### G. Use explicit record objects

Use when each record needs its own `hidden`, `unit_label`, or `vlan_id`.

```deluge
payload = Map();
payload.put("building_name","123 Main Street");
payload.put("site_name","123 Main Street");
payload.put("credential_mode","predefined");
payload.put("workflow_mode","pdf_and_site");
payload.put("omada_operation","create");
payload.put("template_name","Opticable_Template_01");
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");

records = List();

record1 = Map();
record1.put("SSID","APT_101_AA");
record1.put("PASSWORD","2249da8679!#");
record1.put("hidden",false);
record1.put("unit_label","101");
record1.put("vlan_id",10);
records.add(record1);

record2 = Map();
record2.put("SSID","APT_102_BB");
record2.put("PASSWORD","4907ug5605$*");
record2.put("hidden",false);
record2.put("unit_label","102");
record2.put("vlan_id",20);
records.add(record2);

payload.put("records",records);

response = opticable_post("/v1/workflows/site-and-password",payload);
info response;
```

### H. Custom generated SSID format

Useful if you ever change naming rules.

Allowed placeholders in `ssid_template`:

- `{prefix}`
- `{identifier}`
- `{suffix}`
- `{index}`
- `{building}`
- `{building_slug}`

Example:

```deluge
payload = Map();
payload.put("building_name","123 Main Street");
payload.put("credential_mode","generated");
payload.put("workflow_mode","pdf_only");
payload.put("template_name","Opticable_Template_01");
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");
payload.put("ssid_prefix","APT_");
payload.put("ssid_template","{prefix}{identifier}_{suffix}");
payload.put("ssid_suffix_length",2);
payload.put("password_specials","*!$@#");
payload.put("hidden",false);

units = List();
units.add("101");
units.add("102");
payload.put("units",units);

response = opticable_post("/v1/workflows/site-and-password",payload);
info response;
```

### I. Generated site only

Use when you want generated SSIDs/passwords for Omada, but no PDFs.

```deluge
payload = Map();
payload.put("building_name","123 Main Street");
payload.put("site_name","123 Main Street");
payload.put("credential_mode","generated");
payload.put("workflow_mode","site_only");
payload.put("omada_operation","create");
payload.put("template_name","Opticable_Template_01");
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");

units = List();
units.add("101");
units.add("102");
payload.put("units",units);

response = opticable_post("/v1/workflows/site-and-password",payload);
info response;
```

## 5. WorkDrive-Driven Omada Jobs

Use this endpoint when the source of truth is already in WorkDrive.

Endpoint:

- `POST /v1/omada/workdrive/jobs`

Fields:

- `workdrive_folder_id`
- `operation`
  - `create`
  - `upsert`
  - `update`
- `source_preference`
  - `yaml_then_txt`
  - `yaml_only`
  - `txt_only`
- `building_name`
- `site_name`
- `city`
- `template_name`
- `omada_region`
- `omada_timezone`
- `omada_scenario`

### A. Create from `create.yaml`, or TXT fallback

```deluge
payload = Map();
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");
payload.put("operation","create");
payload.put("source_preference","yaml_then_txt");
payload.put("building_name","123 Main Street");
payload.put("site_name","123 Main Street");

response = opticable_post("/v1/omada/workdrive/jobs",payload);
info response;
```

### B. Upsert from `upsert.yaml`, or fallback to `create.yaml`, or TXT

```deluge
payload = Map();
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");
payload.put("operation","upsert");
payload.put("source_preference","yaml_then_txt");
payload.put("building_name","123 Main Street");
payload.put("site_name","123 Main Street");

response = opticable_post("/v1/omada/workdrive/jobs",payload);
info response;
```

### C. Update from `update.yaml`, or TXT fallback

```deluge
payload = Map();
payload.put("workdrive_folder_id","REPLACE_WITH_WORKDRIVE_FOLDER_ID");
payload.put("operation","update");
payload.put("source_preference","yaml_then_txt");
payload.put("building_name","123 Main Street");
payload.put("site_name","123 Main Street");

response = opticable_post("/v1/omada/workdrive/jobs",payload);
info response;
```

## 6. Read And Tracking Calls

### A. Get workflow job status

```deluge
job_id = "REPLACE_WITH_JOB_ID";
response = opticable_get("/v1/workflows/site-and-password/jobs/" + job_id);
info response;
```

### B. Get Omada job status

```deluge
job_id = "REPLACE_WITH_OMADA_JOB_ID";
response = opticable_get("/v1/omada/jobs/" + job_id);
info response;
```

### C. List Omada sites

```deluge
response = opticable_get("/v1/omada/sites");
info response;
```

### D. Get one site

```deluge
site_id = "REPLACE_WITH_SITE_ID";
response = opticable_get("/v1/omada/sites/" + site_id);
info response;
```

### E. Get LANs for a site

```deluge
site_id = "REPLACE_WITH_SITE_ID";
response = opticable_get("/v1/omada/sites/" + site_id + "/lans");
info response;
```

### F. Get WLAN groups for a site

```deluge
site_id = "REPLACE_WITH_SITE_ID";
response = opticable_get("/v1/omada/sites/" + site_id + "/wlan-groups");
info response;
```

### G. Get SSIDs for one WLAN group

```deluge
site_id = "REPLACE_WITH_SITE_ID";
wlan_id = "REPLACE_WITH_WLAN_GROUP_ID";
response = opticable_get("/v1/omada/sites/" + site_id + "/wlan-groups/" + wlan_id + "/ssids");
info response;
```

### H. Get a full site snapshot

JSON:

```deluge
site_id = "REPLACE_WITH_SITE_ID";
response = opticable_get("/v1/omada/sites/" + site_id + "/snapshot");
info response;
```

YAML:

```deluge
site_id = "REPLACE_WITH_SITE_ID";
response = opticable_get("/v1/omada/sites/" + site_id + "/snapshot?format=yaml");
info response;
```

Important:

- the public snapshot endpoint does not expose live PSKs
- the current password source of truth is the generated files in WorkDrive
- after successful create, upsert, or update runs, `live-site.yaml` is refreshed with IDs and the applied passwords

## 7. Response Pattern

Workflow and Omada job creation calls return `accepted` first.

Typical response:

```json
{
  "status": "accepted",
  "job_id": "20260404T181627Z-...",
  "job_status_url": "/v1/workflows/site-and-password/jobs/20260404T181627Z-..."
}
```

So the normal Zoho pattern is:

1. send the POST
2. store `job_id`
3. optionally poll the status endpoint later

## 8. Recommended Zoho Patterns

Use these simple rules:

- new building with generated credentials:
  - `credential_mode=generated`
  - `workflow_mode=pdf_and_site`
  - `omada_operation=create`

- regenerate docs only:
  - `credential_mode=generated` or `predefined`
  - `workflow_mode=pdf_only`

- password rotation on an existing site:
  - `credential_mode=generated` or `predefined`
  - `workflow_mode=pdf_and_site`
  - `omada_operation=update`

- safe rerun on a site that may already exist:
  - `omada_operation=upsert`

- direct execution from WorkDrive folder content:
  - `POST /v1/omada/workdrive/jobs`

## 9. File Behavior In WorkDrive

For generated workflow runs:

- files are uploaded inside `Document locataire`
- if `Document locataire` already contains files, it is moved into:
  - `Archive/<timestamp>`
- a fresh `Document locataire` is created
- current runs keep:
  - PDFs
  - TXT
  - ZIP
  - `.ya`
  - `omada-plan.yaml`
  - operation file like `create.yaml`, `upsert.yaml`, or `update.yaml`
  - `live-site.yaml` after successful Omada execution

## 10. Best Practice

Use canonical field names in Deluge:

- `building_name`
- `credential_mode`
- `workflow_mode`
- `omada_operation`
- `template_name`
- `workdrive_folder_id`
- `site_name`
- `units`
- `ssids`
- `passwords`
- `records`

Do not rely on old alias keys unless you need backward compatibility.
