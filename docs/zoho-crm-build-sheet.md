# Zoho CRM Build Sheet

This is the concrete CRM build sheet for Opticable.

It is designed for:

- English internal API names
- bilingual English/French UI labels
- simple first implementation
- enough structure to scale later

## 1. Global Rules

Use these rules everywhere:

- Keep **module API names and field API names in English**
- Use **English/French display labels** for users
- Keep `Deals` for sales only
- Keep `Service Locations` for operations
- Create `Units` only for multi-tenant jobs
- Use `Installations` for scheduling and field completion

Recommended naming rule:

- API names: English only, stable, no accents
- English label: normal English
- French label: translated label for users

Example:

- API name: `WorkDrive_Folder_Id`
- English label: `WorkDrive Folder ID`
- French label: `ID du dossier WorkDrive`

## 2. Module List

Build these modules.

### Standard modules

| API / Module | English label | French label | Purpose |
| --- | --- | --- | --- |
| `Leads` | Leads | Prospects | Incoming opportunities |
| `Accounts` | Accounts | Comptes | Companies, owners, customers |
| `Contacts` | Contacts | Contacts | People linked to accounts |
| `Deals` | Deals | Opportunites | Sales pipeline |
| `Quotes` or Finance Quotes | Quotes | Devis | Commercial proposal |
| `Tasks` | Tasks | Taches | Follow-up actions |

### Custom modules

| API / Module | English label | French label | Purpose |
| --- | --- | --- | --- |
| `Service_Locations` | Service Locations | Emplacements de service | Physical service sites |
| `Units` | Units | Unites | Per-unit provisioning rows |
| `Installations` | Installations | Installations | Scheduling and completion |
| `Service_Changes` | Service Changes | Changements de service | Optional later for change requests |

## 3. Best Use Of Products And Quotes

Recommended structure:

- Keep the **financial item catalog** in `Zoho Books` or `Zoho Billing`
- Sync products/items into CRM for sales visibility
- Build and manage the **sales process** in CRM
- Create **quotes / estimates** from the finance side inside CRM where possible

Simple rule:

- recurring services -> Billing
- one-time invoicing -> Books
- CRM still stores the sales context and related record links

Recommended product categories:

- Managed WiFi
- Internet Access
- Cabling
- Cameras
- VoIP
- Support / Maintenance
- Installation Labor
- Hardware

## 4. Module Build Sheet

## 4.1 Leads

Use for:

- web forms
- calls
- word of mouth
- referrals

### Fields

| API name | English label | French label | Type | Notes |
| --- | --- | --- | --- | --- |
| `Lead_Source_Detail` | Lead Source Detail | Detail de la source du prospect | Picklist | Web, call, referral, etc. |
| `Service_Type_Requested` | Service Type Requested | Type de service demande | Multi-select picklist | WiFi, cameras, cabling, etc. |
| `Client_Type` | Client Type | Type de client | Picklist | Residential building, business, etc. |
| `Building_Type` | Building Type | Type de batiment | Picklist | Multi-tenant, office, retail, house |
| `Estimated_Unit_Count` | Estimated Unit Count | Nombre d'unites estime | Number | Empty for non-multi-tenant |
| `Qualification_Status` | Qualification Status | Statut de qualification | Picklist | New, Qualified, etc. |

### Suggested picklists

`Client_Type`

- Residential Building / Immeuble residentiel
- Commercial Building / Immeuble commercial
- Business Customer / Client commercial
- Condo Board / Syndicat de copropriete
- Property Manager / Gestionnaire immobilier
- Direct Residential / Residentiel direct
- Partner / Partenaire

`Building_Type`

- Multi-Tenant Building / Immeuble multi-locatif
- Office / Bureau
- Retail / Commerce
- Industrial / Industriel
- House / Maison
- Mixed Use / Usage mixte

## 4.2 Deals

Use for:

- quoting
- negotiation
- contract handling
- sales pipeline

### Fields

| API name | English label | French label | Type | Notes |
| --- | --- | --- | --- | --- |
| `Deal_Type` | Deal Type | Type d'opportunite | Picklist | New install, renewal, change |
| `Service_Type` | Service Type | Type de service | Multi-select picklist | WiFi, internet, cameras |
| `Client_Type` | Client Type | Type de client | Picklist | Same as Leads |
| `Quoted_Units` | Quoted Units | Unites soumissionnees | Number | Optional |
| `Contract_Status` | Contract Status | Statut du contrat | Picklist | Draft, sent, signed |
| `Quote_Status` | Quote Status | Statut du devis | Picklist | Draft, sent, accepted |
| `Finance_Quote_Id` | Finance Quote ID | ID du devis finance | Single line | Books/Billing quote reference |
| `Sign_Request_Id` | Sign Request ID | ID de la demande Sign | Single line | Zoho Sign reference |
| `Primary_WorkDrive_Folder_Id` | Primary WorkDrive Folder ID | ID principal du dossier WorkDrive | Single line | Optional pre-site folder |
| `Primary_Site_Count` | Primary Site Count | Nombre principal de sites | Number | For multi-site deals |
| `Won_Date` | Won Date | Date gagnee | Date | Sales closure |

### Deal stages

| English | French |
| --- | --- |
| Qualification | Qualification |
| Survey / Discovery | Releve / decouverte |
| Quote Preparation | Preparation du devis |
| Quote Sent | Devis envoye |
| Negotiation | Negociation |
| Contract Sent | Contrat envoye |
| Contract Signed | Contrat signe |
| Won | Gagne |
| Lost | Perdu |

## 4.3 Service Locations

This is the main operational module.

Use for:

- any physical service location
- buildings
- offices
- stores
- camera jobs
- cabling jobs

### Fields

| API name | English label | French label | Type | Notes |
| --- | --- | --- | --- | --- |
| `Service_Location_Name` | Service Location Name | Nom de l'emplacement de service | Single line | Main record name |
| `Building_Name` | Building Name | Nom du batiment | Single line | Optional separate display name |
| `Street_Address` | Street Address | Adresse civique | Single line |  |
| `City` | City | Ville | Single line |  |
| `Province_State` | Province / State | Province / etat | Single line |  |
| `Postal_Code` | Postal Code | Code postal | Single line |  |
| `Country` | Country | Pays | Single line |  |
| `Linked_Deal` | Linked Deal | Opportunite liee | Lookup | Deal |
| `Linked_Account` | Linked Account | Compte lie | Lookup | Account |
| `Primary_Contact` | Primary Contact | Contact principal | Lookup | Contact |
| `Service_Type` | Service Type | Type de service | Multi-select picklist | Main service families |
| `Engagement_Model` | Engagement Model | Mode d'engagement | Picklist | One-time, recurring, mixed |
| `Client_Type` | Client Type | Type de client | Picklist | Same family as Deal |
| `Multi_Tenant` | Multi-Tenant | Multi-locatif | Checkbox | Yes when units exist |
| `Requires_Network_Provisioning` | Requires Network Provisioning | Necessite du provisionnement reseau | Checkbox | Omada-related work |
| `Requires_Installation` | Requires Installation | Necessite une installation | Checkbox | Field work |
| `Implementation_Stage` | Implementation Stage | Etape d'implantation | Picklist | Main lifecycle |
| `Operational_Status` | Operational Status | Statut operationnel | Picklist | Active, suspended, etc. |
| `WorkDrive_Folder_Id` | WorkDrive Folder ID | ID du dossier WorkDrive | Single line | Main building folder |
| `Current_Document_Folder_Link` | Current Document Folder Link | Lien du dossier de documents courant | URL | Optional |
| `Zoho_Sign_Status` | Zoho Sign Status | Statut Zoho Sign | Picklist | Draft, sent, signed |
| `Omada_Site_Id` | Omada Site ID | ID du site Omada | Single line | Filled after create |
| `Last_Omada_Operation` | Last Omada Operation | Derniere operation Omada | Picklist | create, update, upsert |
| `Last_Workflow_Job_Id` | Last Workflow Job ID | ID du dernier job workflow | Single line | API job |
| `Last_Omada_Job_Id` | Last Omada Job ID | ID du dernier job Omada | Single line | Omada job |
| `Live_Site_Yaml_Link` | Live Site YAML Link | Lien du YAML du site en direct | URL | Latest live-site.yaml |
| `Activation_Date` | Activation Date | Date d'activation | Date | Service live date |
| `Billing_Status` | Billing Status | Statut de facturation | Picklist | Not started, ready, active |
| `Billing_Customer_Id` | Billing Customer ID | ID du client de facturation | Single line | Finance ID |
| `Billing_Subscription_Id` | Billing Subscription ID | ID de l'abonnement de facturation | Single line | Billing ID |
| `Desk_Enabled` | Desk Enabled | Desk active | Checkbox | Support live |

### Suggested picklists

`Engagement_Model`

- One-Time Project / Projet ponctuel
- Recurring Service / Service recurrent
- Mixed / Mixte

`Implementation_Stage`

- Intake / Demarrage
- WorkDrive Ready / WorkDrive pret
- Contract Signed / Contrat signe
- Units Pending / Unites en attente
- Ready For Provisioning / Pret pour le provisionnement
- Provisioning In Progress / Provisionnement en cours
- Provisioned / Provisionne
- Scheduled / Planifie
- Installation In Progress / Installation en cours
- Installed / Installe
- Billing Ready / Pret a la facturation
- Active / Actif
- Support / Support
- Suspended / Suspendu
- Cancelled / Annule

`Operational_Status`

- Pending / En attente
- Active / Actif
- Suspended / Suspendu
- Cancelled / Annule
- Closed / Ferme

## 4.4 Units

Create only when `Multi_Tenant = true`.

### Fields

| API name | English label | French label | Type | Notes |
| --- | --- | --- | --- | --- |
| `Linked_Service_Location` | Linked Service Location | Emplacement de service lie | Lookup | Parent site |
| `Unit_Label` | Unit Label | Numero / etiquette d'unite | Single line | 101, 201A, etc. |
| `SSID` | SSID | SSID | Single line | Generated or predefined |
| `Password` | Password | Mot de passe | Single line | Generated or predefined |
| `VLAN` | VLAN | VLAN | Number | Optional |
| `Hidden` | Hidden | Cache | Checkbox | Hidden SSID |
| `Credential_Source` | Credential Source | Source des identifiants | Picklist | Generated, predefined |
| `Provisioning_Status` | Provisioning Status | Statut de provisionnement | Picklist | Pending, applied |
| `Last_Generated_At` | Last Generated At | Derniere generation le | Date/Time |  |
| `Last_Applied_At` | Last Applied At | Derniere application le | Date/Time |  |
| `Active` | Active | Actif | Checkbox | In service |

### Suggested picklists

`Credential_Source`

- Generated / Genere
- Predefined / Predefini
- Imported / Importe

`Provisioning_Status`

- Pending / En attente
- Generated / Genere
- Uploaded / Televerse
- Applied / Applique
- Failed / Echec

## 4.5 Installations

### Fields

| API name | English label | French label | Type | Notes |
| --- | --- | --- | --- | --- |
| `Linked_Service_Location` | Linked Service Location | Emplacement de service lie | Lookup | Parent record |
| `Installation_Type` | Installation Type | Type d'installation | Picklist | WiFi, cameras, cabling |
| `Scheduled_Date` | Scheduled Date | Date planifiee | Date/Time |  |
| `Assigned_Technician` | Assigned Technician | Technicien assigne | User lookup |  |
| `Installation_Status` | Installation Status | Statut d'installation | Picklist | Requested, scheduled, completed |
| `Technician_Notes` | Technician Notes | Notes du technicien | Multi-line |  |
| `Completion_Proof_Link` | Completion Proof Link | Lien de preuve de completion | URL | Photos/docs |
| `Completed_At` | Completed At | Complete le | Date/Time |  |

### Suggested picklists

`Installation_Type`

- Managed WiFi / WiFi gere
- Cabling / Cablage
- Cameras / Cameras
- Internet / Internet
- Mixed / Mixte

`Installation_Status`

- Requested / Demandee
- Scheduled / Planifiee
- Technician Assigned / Technicien assigne
- In Progress / En cours
- Completed / Completee
- Failed / Echouee
- Revisit Required / Retour requis

## 5. Blueprint Build Sheet

## 5.1 Deals Blueprint

Module:

- `Deals`

### States

| English | French |
| --- | --- |
| Qualification | Qualification |
| Survey / Discovery | Releve / decouverte |
| Quote Preparation | Preparation du devis |
| Quote Sent | Devis envoye |
| Negotiation | Negociation |
| Contract Sent | Contrat envoye |
| Contract Signed | Contrat signe |
| Won | Gagne |
| Lost | Perdu |

### Main transitions

| Transition | English | French | Required action |
| --- | --- | --- | --- |
| `Prepare_Quote` | Prepare Quote | Preparer le devis | Confirm service scope |
| `Send_Quote` | Send Quote | Envoyer le devis | Quote exists |
| `Send_Contract` | Send Contract | Envoyer le contrat | Sign request prepared |
| `Mark_Contract_Signed` | Mark Contract Signed | Marquer le contrat signe | Signed copy/status present |
| `Mark_Won` | Mark Won | Marquer gagne | Final commercial approval |
| `Mark_Lost` | Mark Lost | Marquer perdu | Lost reason required |

### Automation

After `Mark_Contract_Signed`:

- CRM Function: `initialize_site_from_deal`

Result:

- create `Service Location`
- create WorkDrive folder
- copy commercial data from Deal

## 5.2 Service Locations Blueprint

Module:

- `Service_Locations`

### States

| English | French |
| --- | --- |
| Intake | Demarrage |
| WorkDrive Ready | WorkDrive pret |
| Contract Signed | Contrat signe |
| Units Pending | Unites en attente |
| Ready For Provisioning | Pret pour le provisionnement |
| Provisioning In Progress | Provisionnement en cours |
| Provisioned | Provisionne |
| Scheduled | Planifie |
| Installation In Progress | Installation en cours |
| Installed | Installe |
| Billing Ready | Pret a la facturation |
| Active | Actif |
| Support | Support |
| Suspended | Suspendu |
| Cancelled | Annule |

### Main transitions

| Transition | English | French | Use |
| --- | --- | --- | --- |
| `Prepare_WorkDrive` | Prepare WorkDrive | Preparer WorkDrive | Create folder structure |
| `Collect_Units` | Collect Units | Collecter les unites | Only for multi-tenant |
| `Generate_Docs` | Generate Docs | Generer les documents | Calls main workflow |
| `Provision_Site` | Provision Site | Provisionner le site | Calls create/upsert/update |
| `Schedule_Install` | Schedule Install | Planifier l'installation | Create installation record |
| `Mark_Installed` | Mark Installed | Marquer installe | Installation done |
| `Mark_Billing_Ready` | Mark Billing Ready | Marquer pret a la facturation | Finance handoff |
| `Activate_Service` | Activate Service | Activer le service | Service live |

### Automation

`Generate_Docs`

- CRM Function: `site_generate_docs_and_create`

`Provision_Site`

- CRM Function: `site_apply_workdrive_plan`

`Password_Rotation`

- add as button or transition
- CRM Function: `site_rotate_passwords`

## 5.3 Installations Blueprint

Module:

- `Installations`

### States

| English | French |
| --- | --- |
| Requested | Demandee |
| Scheduled | Planifiee |
| Technician Assigned | Technicien assigne |
| In Progress | En cours |
| Completed | Completee |
| Failed / Revisit Required | Echec / retour requis |

### Main transitions

| Transition | English | French | Use |
| --- | --- | --- | --- |
| `Schedule` | Schedule | Planifier | Set date and technician |
| `Assign_Technician` | Assign Technician | Assigner le technicien | Field work ownership |
| `Start_Work` | Start Work | Commencer les travaux | Technician on site |
| `Complete` | Complete | Completer | Require notes |
| `Fail_And_Revisit` | Fail and Revisit | Echec et retour | Require failure reason |

## 6. Workflow Rules And Functions

Use this exact split.

| Trigger place | Tool | Function / action |
| --- | --- | --- |
| Lead becomes qualified | CRM Workflow Rule | `convert_qualified_lead` |
| Deal contract signed | Deal Blueprint or Workflow Rule | `initialize_site_from_deal` |
| Service Location ready for provisioning | Site Blueprint transition | `site_generate_docs_and_create` |
| Password rotation requested | Button or Site Blueprint transition | `site_rotate_passwords` |
| Operator wants YAML/TXT apply | Button | `site_apply_workdrive_plan` |
| Need current controller state | Button | `site_fetch_live_snapshot` |
| Installation completed | Installation Blueprint / Workflow Rule | update site to `Billing Ready` |
| Billing activated | Flow or finance-side automation | update billing fields on `Service_Location` |
| Desk ticket escalation | Flow | update `Service_Location` support state or task |

## 7. Recommended Buttons

Add these buttons on `Service Locations`.

| API / Internal name | English label | French label | Action |
| --- | --- | --- | --- |
| `Generate_Docs_Create_Site` | Generate Docs + Create Site | Generer les documents + creer le site | Workflow API |
| `Rotate_Passwords` | Rotate Passwords | Rotation des mots de passe | Workflow API update |
| `Apply_Create_Yaml` | Apply Create YAML | Appliquer le YAML de creation | WorkDrive job create |
| `Apply_Upsert_Yaml` | Apply Upsert YAML | Appliquer le YAML d'upsert | WorkDrive job upsert |
| `Apply_Update_Yaml` | Apply Update YAML | Appliquer le YAML de mise a jour | WorkDrive job update |
| `Fetch_Live_Snapshot` | Fetch Live Snapshot | Recuperer l'etat en direct | Omada GET snapshot |

## 8. Best Build Order

Build in this order:

1. Create custom modules:
   - `Service Locations`
   - `Units`
   - `Installations`
2. Add the critical fields
3. Add picklists
4. Build `Deals Blueprint`
5. Build `Service Locations Blueprint`
6. Build `Installations Blueprint`
7. Add CRM Functions
8. Add Workflow Rules
9. Add buttons on `Service Locations`
10. Add Books/Billing sync
11. Add Sign automation
12. Add Flow for cross-app sync
13. Add Desk integration

## 9. Minimal First Version

If you want the smallest useful v1, do only this:

- Leads
- Accounts
- Contacts
- Deals
- Service Locations
- Units
- Installations
- one Deals Blueprint
- one Service Locations Blueprint
- these CRM Functions:
  - `convert_qualified_lead`
  - `initialize_site_from_deal`
  - `site_generate_docs_and_create`
  - `site_rotate_passwords`
  - `site_apply_workdrive_plan`
  - `site_fetch_live_snapshot`

That is enough to run the business without overbuilding it.
