# AAP vRO Workflow Installer


### Prerequisites
* AAP installed and running
* Python 3.10 or higher on the machine where the script will be executed
* Aria Automation 8.16 or higher


### Deployment
Open the file 'config.json', and enter the appropriate values for the following parameters:
* dsm_hostname: Enter the IP address of DSM
* dsm_user_id: Enter the username of DSM
* dsm_password: Enter the password of DSM
* aria_base_url: Enter the base url of your Aria deployment
* org_id: Enter the organization id of your Aria deployment. This org id can be found by logging into your Aria setup and clicking on 'User/Organization Settings' (found in the top right corner of the page)
* aria_username: Enter the username of your Aria deployment
* aria_password: Enter the password of your Aria deployment
* skip_certificate_check: Enter 'False' to enable verified connection to DSM using certificates. The default value is 'True'
* dsm_root_ca: Enter the root CA of DSM. Setting the value of this parameter is essential when the parameter 'skip_certificate_check' is set to 'False'

The other config.json parameters are optional and can be left as is or modified as per your requirements.

#### Example config.json file
![Screenshot](readme_assets/config_json.png)

Post entering the appropriate values for the above-mentioned parameters, save changes made to the file 'config.json' and run the python script called 'aria.py':
```bash
python3 aria.py
```

Note: In order to enable enhanced blueprint/template (supported in Aria versions 8.16.2 or higher) in your Aria environment and to have an 'Overview' tab displayed with details for your deployments, run the python script called 'aria.py' as follows:

```bash
python3 aria.py enable-blueprint-version-2
```

At the bottom of this README, you will find a list of imported items and their location in Aria Automation (Refer the section 'Imported Items').

### Using Aria to perform CRUD operations in DSM

#### Create
To create a database in DSM, follow the steps below:
* Post successful execution of the python script 'aria.py', login to your aria deployment setup
* Click on 'Service Broker'
* Click on 'Catalog'
* Click on the catalog item called 'DSM DBaaS' (this name may be different if you've changed the value of the 'blue_print_name' variable in the 'config.json' file)
* Fill in the required database related fields in the request form presented to you and click on submit.

#### Update
Once the database is successfully created in DSM, in order to update the database related fields, follow the steps below:
* login to your aria deployment setup
* Click on 'Service Broker'
* Click on 'Deployments'
* Click on the three vertical dots prepended to the name of the deployment which should be updated/modified
* Click on 'Update'
* Modify the necessary fields and click on submit.
  * **NOTE:** You cannot upgrade the DB and update other fields at the same time, these actions must be done sequentially.

#### Connect
Once the database is successfully created in DSM and the database is in the 'Ready' state, in order to connect to the database, follow the steps below:
* login to your aria deployment setup
* Click on 'Service Broker'
* Click on 'Deployments'
* Click on the database deployment name to be connected to
* Click on the 'Topology' tab
* Click on 'Actions' located on the right side of the 'Topology' Tab.
* Select the option 'Get Connection String' in order to view/copy the database connection string.
* You can click on 'Cancel' after you have successfully copied the connection string.

#### Delete
Once the database is successfully created in DSM, in order to delete it, follow the steps below:
* login to your aria deployment setup
* Click on 'Service Broker'
* Click on 'Deployments'
* Click on the three vertical dots prepended to the name of the deployment which should be deleted
* Click on 'Delete'

### Known Issues

#### Active connection timeout

The internal proxy service of Aria Automation has a default active connection timeout of 15 minutes. This means that if an action doesn't complete its execution within 15 minutes, then it is marked as failed. As part of this Aria integration work with DSM, the timeout value specified is 14 minutes, so we try to complete the create database operation within the max timeout of Aria. If a deployment requests takes more than 14 minutes to be 'Ready' (i.e. for HA Clusters, deployment is longer due to the additional resources needed), then a success status is returned back to Aria at the 14th minute mark, while the deployment continues in DSM.
To increase the timeout, perform the following steps: 
* Increase the timeout value in the Aria Automation proxy service. Refer the link: https://kb.vmware.com/s/article/94062#:~:text=The%20internal%20proxy%20service%20of,failure%20of%20the%20deployment%20request
* Open the file 'vro_abx.py' and search for the global variable called 'timeout' and set its value to the desired timeout value (in seconds) and save and close the file.
* Run the python script called 'aria.py' for this newly entered timeout value to be considered.
```bash
python3 aria.py
```

#### Some fields updates are not propagated

The following fields will not be reflected in the actual DB when updated via the update flow. As such it is not recommended to update them to avoid a discrepancy in the actual vs desired state of the DB.
* `Database Name`
* `Admin Username`

#### Disappearing fields when creating new DB

During some usecases, several fields in the create form will dissapear. This is a consequence of some guardrails that were introduced to block updates for a subset of non-updateable fields.

This is observed in the following usecases:
* Deployment Name is populated and then erased
* Deployment Name matches the Deployment Name of another Deployment

The workaround to this is to reopen the form and not match the usecases mentioned above.

#### DB Upgrade is an independant action

A DB's version cannot be updated to follow the upgrade path if other fields are updated at the same time.

If you see a failure due to this, please try again by running this update operation in isolation (by reverting other changes and updating them once the upgrade is complete)

#### Update feedback is misleading

When updating a deployment, the status field shows if the backing CR has been updated and not if the actual backing DB has been updated and is ready. The progress of the update can be observed in the DSM UI.

### Imported Items

Let's have a look at each of the functions in the 'aria.py' script and the corresponding items that are imported into Aria Automation.

```bash
projectId = createOrUpdateProject()
```
This function will create or update a project in Aria Automation with the name specified in the 'config.json' file and returns the project id.
Projects control who has access to Automation Assembler cloud templates and where the templates are deployed. Everything created by this script will be made available to this project. It will include:
* A Design Template including the DSM database custom resource
* Two ABX actions for CRUD operations in DSM
* 5 secrets for dsm_hostname, dsm_user_id, dsm_password, skip_certificate_check and dsm_root_ca respectively

![Screenshot](readme_assets/project_pic.png)

```bash
envId = createOrUpdateEnvironmentForVroAction()  # Create or update the environment for VRO action
```

This function will create or update an environment in Aria Automation Orchestrator with the name set in the 'config.json' file and return the environment id. Environments in Aria Automation Orchestrator are used to store dependencies for your actions or workflow runs within the Orchestrator. It will include:
* 5 environmental variables for dsm_hostname, dsm_user_id, dsm_password, skip_certificate_check and dsm_root_ca

![Screenshot](readme_assets/env_pic.png)

```bash
createSecrets(projectId)  # Create secrets for the given project ID
```

This function creates secrets for dsm_hostname, dsm_user_id, dsm_password, skip_certificate_check and dsm_root_ca respectively. A secret Automation Assembler property is a reusable, encrypted value that project users may
add to their cloud template designs. 

![Screenshot](readme_assets/secrets_pic.png)

```bash
createOrUpdateVroActions(envId)  # Create or update the VRO actions for the specified environment ID
```

This function will create or update actions in Aria Automation Orchestrator. Actions in Aria Automation Orchestrator are used to run workflows or scripts in the Orchestrator. It will include the following 2 actions:
* form_connectionstring (output type: string) - This action will return the connection string of the database deployment in DSM
* form_dsminputs (output type: array) - This action will return the inputs available to create a database deployment in DSM, based on infrastructure policy (i.e. storage policy, vm class etc.).

![Screenshot](readme_assets/actions_pic.png)

```bash
secretIds = getSecrets(projectId)  # Retrieve secrets IDs for the project
```

This function will retrieve the secret IDs created previously to add them as default inputs in the Abx Actions created in the next step.

![Screenshot](readme_assets/secretids_pic.png)

```bash
abxActionId = createOrUpdateAbxAction(projectId, secretIds)  # Create or update ABX action with secrets

day2OperationsActionID = createOrUpdateDSMDay2OperationsAction(projectId)  # Create or update Day 2 operations action
```

These functions will create or update the ABX actions in Aria Automation Assembler. These ABX action scripts run on Python 3.10 and will be used by the Assembler to perform CRUD operations in DSM.

![Screenshot](readme_assets/abxactions_pic.png)

```bash
createOrUpdateAbxBasedCustomResource(projectId, abxActionId,
                                     day2OperationsActionID)  # Create or update ABX-based custom resource
createOrUpdateDay2OperationsActionForms(projectId,
                                        day2OperationsActionID)  # Create or update forms for Day 2 operations actions
```

These functions will create or update the Assembler custom resource for DSM, based on the name provided in the config.json file and the forms for Day 2 operations actions for this resource based on the ABX Actions created previously.

![Screenshot](readme_assets/customresource_pic.png)

```bash
blueprintVersion = createOrUpdateBlueprint(projectId)  # Create or update blueprint for the project
```

This function will create or update a deployment template in Aria Automation Assembler with the name set in the 'config.json' file and return the blueprint version. Blueprints in Aria Automation Assembler are used to define the infrastructure and application components that make up a cloud template.

![Screenshot](readme_assets/blueprint_pic.png)

```bash
contentSourceId = createOrUpdateContentSource(projectId)  # Create or update content source for the project
```

This function will create or update a Content Source in Aria Automation Service Broker and return the content source id. Content sources in Aria Automation Service Broker are repositories where you can define and manage items that users can request through the Service Broker catalog. These are bound to a project and inherit the project's templates, users, secrets, etc.

![Screenshot](readme_assets/contentsource_pic.png)

```bash
sourceId = getCatalogItemId(contentSourceId)  # Retrieve catalog item ID from the content source ID
createOrUpdateCustomForm(sourceId)  # Create or update custom form for the catalog item
```

These functions will create or update a custom form for the catalog item in Aria Automation Service Broker. Custom forms in Aria Automation Service Broker are used to define the fields that users must fill in when they request an item from the Service Broker catalog.

![Screenshot](readme_assets/customform_pic.png)

```bash
createOrUpdateContentSharingPolicy(projectId, contentSourceId)  # Create or update content sharing policy for the project
```

This function will create or update a content sharing policy in Aria Automation Service Broker. Content sharing policies in Aria Automation Service Broker are used to define the sharing rules for items in the Service Broker catalog. These are the link between the Content Sources, their templates and the Service Catalog self-service portal.

![Screenshot](readme_assets/contentsharingpolicy_pic.png)


### Removing Imported Items

In the current version of this integration, there is no script to remove the imported items. However, you can remove the items manually by following the steps below:

NOTE: Due to the dependencies between the items, it is recommended to login to your Aria Automation console and remove the items in the optimal order listed below.

1. Remove Deployments
* Click on 'Service Broker'
* In the 'Consume' tab, click on 'Deployments' on the LHS and verify that all DSM related deployments are deleted

2. Remove Content Source
* Click on 'Service Broker'
* In the 'Content & Policies' tab, click on 'Content Sources' on the LHS and delete the 'DSM_CONTENT_SOURCE'

3. Remove Policy
* Click on 'Service Broker'
* In the 'Content & Policies' tab, click on 'Definitions' under 'Policies' on the LHS and delete the 'share1'

4. Remove VRO Actions
* In your Orchestrator services, click on 'Actions' under 'Library' on the LHS and delete the 'form_connectionstring' and 'form_dsminputs' actions

5. Remove Environment
* In your Orchestrator services, click on 'Environments' under 'Assets' on the LHS and delete the 'DSM_ENV' (this name may be different if you've changed the value of the 'env_name' variable in the 'config.json' file)

6. Remove Custom Resource
* In your Aria Automation console, click on 'Assembler'
* In the 'Design' tab, click on 'Custom resources' on the LHS and delete the 'DSMDB' custom resource (this name may be different if you've changed the value of the 'cr_name' variable in the 'config.json' file)

7. Remove Template
* In your Aria Automation console, click on 'Assembler'
* In the 'Design' tab, click on 'Templates' on the LHS and delete the 'DSM DBaaS' template (this name may be different if you've changed the value of the 'blue_print_name' variable in the 'config.json' file)

8. Remove ABX Actions
* In your Aria Automation console, click on 'Assembler'
* In the 'Extensibility' tab, click on 'Actions' under 'Library' on the LHS and delete the 'DSM-Day2-Operations' action and the 'DSM-DB-crud' action (this name may be different if you've changed the value of the 'abx_action_name' variable in the 'config.json' file)

9. Remove Secrets
* In your Aria Automation console, click on 'Assembler'
* In the 'Infrastructure' tab, click on 'Secrets' under 'Administration' on the LHS and delete the 'dsmHost', 'dsmPassword', 'dsmUserID', 'dsmCertificateCheck' and 'dsmRootCA' secrets

10. Remove Project
* In your Aria Automation console, click on 'Assembler'
* In the 'Infrastructure' tab, click on 'Projects' under 'Administration' on the LHS and delete the 'DSM_PROJECT' project (this name may be different if you've changed the value of the 'project_name' variable in the 'config.json' file)



