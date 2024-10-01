import requests
import yaml
import json
import urllib3
urllib3.disable_warnings()
from datetime import datetime
import time
import sys


sourceId = "" 
contentSourceId = ""




configFile = f'config.json' # Name of the configuration file

vroWorkflowFile=f'vro_workflow.json'
vroDeleteWorkflowFile=f'vro_delete_workflow.json'



def get_vra_auth_token(token_endpoint, requestData, bearer_endpoint):
    """
        Gets the authentication token from aria.
        First we need the refresh token, we then use this to obtain the full (bearer) token

        Args:
            token_endpoint (str): the url of the token site
            requestData (dict): username & password for auth
            bearer_endpoint (str): the url of the bearer token site

        Returns:
            str: login (bearer) token
    """

    #  Get the initial refresh token
    headers = {"Content-Type": "application/json"}
    body = json.dumps(requestData).encode('utf-8')
    response = requests.post(token_endpoint, 
                             headers=headers, 
                             data=body, 
                             verify=False)

    token_data = response.json()
    access_token = token_data.get("refresh_token")
    requestData = {"refreshToken": access_token}
    body = json.dumps(requestData).encode('utf-8')
  
    # From refresh token get Bearer token
    response = requests.post(bearer_endpoint, 
                             headers=headers, 
                             data=body,
                             verify=False)
    data = response.json()
    bearer_token = data.get("token")
    return bearer_token

def read_config(configFile):
    """
        Reads the configuration file

        Args:
            configFile (str): The name of the config file.

        Returns:
            list: configuration items
    """

    with open(configFile) as config_file:
        config_data = json.load(config_file)
    return config_data

def createOrUpdateContentSource(projectId):
    """
        Creates or updates the content source which includes the templates for the given project.

        Args:
            projectId (str): The ID of the project.

        Returns:
            str: The ID of the created or updated content source.
    """

    # Get the list of content sources entitled to the specified project ID
    url = f'{baseUrl}/catalog/api/admin/sources?search=&size=20&sort=name%2Casc'
    resp = requests.get(url, headers=headers, verify=False)
    print(resp.status_code, resp.text)
    existing = [x for x in resp.json()["content"] if x.get("projectId") == projectId]

    # Configure the content source with the templates and associate it with the specified project ID
    if len(existing) == 0:
        # XXX: Code path untested ...
        url = f'{baseUrl}/catalog/api/admin/sources'
        body = {
            "name": "DSM_CONTENT_SOURCE",
            "typeId": "com.vmw.blueprint",
            "config": {
                "sourceProjectId": projectId
            },
            "projectId": projectId,
            "global": True,
            "iconId": "1495b8d9-9428-30d6-9626-10ff9281645e"
        }
        resp = requests.post(url, json=body, headers=headers, verify=False)
        print(resp.status_code, resp.text)
        resp.raise_for_status()
        return resp.json()["id"]
    else:
        # Refresh the content source, so the new template is referenced
        contentSourceId = existing[0]["id"]
        body = {
            "id": contentSourceId,
            "name":"DSM_CONTENT_SOURCE",
            "typeId":"com.vmw.blueprint",
            "createdAt":"2023-10-19T10:22:51.000135Z",
            "createdBy":"configadmin",
            "lastUpdatedAt":"2023-10-23T02:26:43.062315Z",
            "lastUpdatedBy":"system-user",
            "config":{
                "sourceProjectId":projectId
            },
            "itemsImported":1,"itemsFound":1,
            "lastImportStartedAt":"2023-10-23T02:26:42.880296Z",
            "lastImportCompletedAt":"2023-10-23T02:26:43.061977Z",
            "lastImportErrors":[],
            "projectId":projectId,
            "global":True,
            "iconId":"1495b8d9-9428-30d6-9626-10ff9281645e"
        }
        url = f'{baseUrl}/catalog/api/admin/sources'
        resp = requests.post(url, json=body, headers=headers, verify=False)
        print(resp.status_code, resp.text)
        resp.raise_for_status()
        return existing[0]["id"]

def getCatalogItemId(contentSourceId):
    """
        Retrieves the ID of the item (content source/template) released to the catalog.

        Args:
            contentSourceId (str): The content source ID to search for.

        Returns:
            str: The ID of the catalog item matching the content source ID.
    """
    url = f'{baseUrl}/catalog/api/admin/items?search=&page=0&size=20&sort=name%2Casc'
    resp = requests.get(url, headers=headers, verify=False)
    print(resp.status_code, resp.text)
    existing = [x for x in resp.json()["content"] if x["name"] == blueprintName and x["sourceId"] == contentSourceId]

    if len(existing) == 0:
        raise Exception("Shouldn't happen?")
    else:
        return existing[0]["id"]

def createOrUpdateDbCrudCustomForm(sourceId, blueprintName):
    """
        Creates or updates the catalog request form for users to enter the database specifications

        Args:
            sourceId (str): The ID of the source.
            blueprintName (str): The name of the blueprint.

        Returns:
            None
    """
    url = f'{baseUrl}/form-service/api/forms'
    body = {
        "name":blueprintName,
        "form": json.dumps(yaml.safe_load(open('db_crud_form.yaml', 'r'))),  # File to read in order to generate the custom form
        "styles": None,
        "status":"ON",
        "type":"requestForm",
        "sourceId":sourceId,
        "sourceType":"com.vmw.blueprint"
    }
    resp = requests.post(url, json=body, headers=headers, verify=False)
    print(resp.status_code, resp.text)
    resp.raise_for_status()


def createOrUpdateBlueprint(projectId):
    """
        Creates or updates the blueprint/template for the given project.

        Args:
            projectId (str): The ID of the project.

        Returns:
            str: The new version of the blueprint.
    """

    # Enable the enhanced cloud template/blueprint if the user specifies the command line option 'enable-blueprint-version-2'
    if len(sys.argv) > 1 and sys.argv[1] == "enable-blueprint-version-2":
        blueprint_filename = "blueprint_version_2.yaml"
    else:
        blueprint_filename = "blueprint_version_1.yaml"

    print("Update blueprint ...")
    body = {
        "name":blueprintName,
        "description":"",
        "valid":True,
        "content": open(blueprint_filename).read(),  # The file to read the blueprint specifications from
        "projectId": projectId,
        "requestScopeOrg":True}
    blueprintId = "76b311db-0d78-4d18-93c8-9ea6d2d86f7d"

    # Get the list of existing blueprints/templates
    url = f'{baseUrl}/blueprint/api/blueprints?apiVersion=2019-09-12'
    resp = requests.get(url, headers=headers, verify=False)
    existing = [x for x in resp.json()["content"] if x["name"] == blueprintName]

    # Update the blueprint if it already exists
    if len(existing) > 0:
        blueprintId = existing[0]['id']
        url = f'{baseUrl}/blueprint/api/blueprints/{blueprintId}?apiVersion=2019-09-12'
        resp = requests.put(url, json=body, headers=headers, verify=False)
        print(resp.status_code, resp.text)
    else:
        # Create a blueprint with the desired specifications if it doesn't already exist
        url = f'{baseUrl}/blueprint/api/blueprints?apiVersion=2019-09-12'
        resp = requests.post(url, json=body, headers=headers, verify=False)
        print(resp.status_code, resp.text)
        blueprintId = resp.json()['id']

    # Create a new version everytime the blueprint/template gets updated
    newVersion = datetime.now().strftime("%d-%m-%H-%M-%S")
    newVersion = f"v{newVersion}"
    body = {"version": newVersion,"description":"","changeLog":"","release":True}
    url = f'{baseUrl}/blueprint/api/blueprints/{blueprintId}/versions?apiVersion=2019-09-12'
    resp = requests.post(url, json=body, headers=headers, verify=False)
    print(resp.status_code, resp.text)
    return newVersion




def vroCreateWorkflow(workflowFile):
    """
        Creates a VRO (VMware vRealize Orchestrator) workflow.

        This function sends a POST request to update the VRO create workflow with the specified body.

        Returns:
            Id of workflow
    """

    with open(workflowFile) as workflow_file:
        workflow = json.load(workflow_file)

    print(workflow["name"])

    # Get the list of existing workflows from the vro proxy
    url = f'{baseUrl}/vro/workflows'
    resp = requests.get(url, headers=headers, verify=False)
    #print(resp.status_code, resp.text)
    resp.raise_for_status()
    existing = [x for x in resp.json()["content"] if x["name"] == workflow["name"]]

    #print(existing)

    if len(existing) > 0:
        print("WORKFLOW ALREADY EXISTS!")
        # If the name exists, just return the ID
        #return existing[0]["id"]
     

    url = f'{baseUrl}/vco/api/workflows'
    resp = requests.post(url, json=workflow, headers=headers, verify=False)
    #print(resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()["id"]






def createOrUpdateVroBasedCustomResource(projectId, WorkflowId, DeleteWorkflowId, propertySchema, vroID):
    """
         Creates or updates the custom resource
         Uses the same ABX for create/read/update/delete - the ABX needs the logic 
         to deal with each.


        Args:
            projectId (str): The ID of the project.
            abxActionId (str): The ID of the ABX action.
            propertySchema (dict): Schema of the Custom Resource. 

        Returns:
            None
    """

    custom_resource_exists = False
    # The extensibility action that this custom resource should be associated with
    vroWorkflow = {
        "id":WorkflowId,
        "name":WorkflowName,
        "projectId":projectId,
        "type":"vro.workflow",
        "inputParameters": [{"type": "string","name": "vm"}],
        "outputParameters": [{"type": "VC:VirtualMachine","name": "output"}],
        "endpointLink": vroID
    }

    vroDeleteWorkflow = {
        "id":DeleteWorkflowId,
        "name":DeleteWorkflowName,
        "projectId":projectId,
        "type":"vro.workflow",
        "inputParameters": [{"type": "VC:VirtualMachine","name": "vm"}],
        "endpointLink": vroID
    }    


    # create the body of the request 
    body = {
        "displayName":vroCrName,
        "description":"",
        "resourceType":vroCrTypeName,
        "externalType": "VC:VirtualMachine",
        "status":"RELEASED",
        "mainActions": {
          "create": vroWorkflow,
          "delete":  vroDeleteWorkflow,
        },
        "properties": propertySchema,
        "schemaType": "VRO_INVENTORY"
    }

    print(body)


    # Get the list of existing custom resources
    url = f'{baseUrl}/form-service/api/custom/resource-types'
    resp = requests.get(url, headers=headers, verify=False)
    #print(resp.status_code, resp.text)
    #resp.raise_for_status()
    existing = [x for x in resp.json()["content"] if x["displayName"] == vroCrName]
    #print(existing)

    # Create the custom resource if it doesn't already exist
    if len(existing) > 0:
        # Update the custom resource if it already exists
        body["id"] = existing[0]["id"]
        custom_resource_exists = True
    resp = requests.post(url, json=body, headers=headers, verify=False)
    #print(body)
    print(resp.status_code, resp.text)
    resp.raise_for_status()

    # Update the custom resource if it already exists
    if (custom_resource_exists):
        # When tried to re-add the 'additionalActions' to a custom resource, a duplicate key error is raised.
        # Hence, first add the 'mainActions' to a custom resource and only then add any 'additionalActions'
        body["id"] = existing[0]["id"]
        resp = requests.post(url, json=body, headers=headers, verify=False)
        #print(resp.status_code, resp.text)        
        resp.raise_for_status()




def createOrUpdateProject():
    """
        Creates or updates a project in the Aria system.

        Args:
            None

        Returns:
            str: The ID of the created or updated project.
    """

    # Get the list of existing projects
    url = f'{baseUrl}/project-service/api/projects?page=0&size=20&%24orderby=name%20asc&excludeSupervisor=false'
    resp = requests.get(url, headers=headers, verify=False)
    resp.raise_for_status()
    existing = [x for x in resp.json()["content"] if x["name"] == projectName]

    if len(existing) > 0:
        # If the project 'DSM_PROJECT' (This name will change based on the value specified in config.json) already exists then return its id
        return existing[0]["id"]

    # Create a new project 
    body = {
        "name": projectName,
        "description": "",
        "orgId": orgId,
        "administrators": [],
        "members": [],
        "viewers": [],
        "supervisors": [],
        "constraints": {},
        "properties": {
            "__projectPlacementPolicy": "DEFAULT"
        },
        "operationTimeout": 0,
        "sharedResources": True
    }
    url = f'{baseUrl}/project-service/api/projects'
    resp = requests.post(url, json=body, headers=headers, verify=False)
    resp.raise_for_status()
    return resp.json()["id"]


def createOrUpdateContentSharingPolicy(projectId, contentSourceId):
    """
        Creates or updates the content sharing policy for the project members to access the templates imported with the content source

        Args:
            projectId (str): The ID of the project.
            contentSourceId (str): The ID of the content source.

        Returns:
            str: The ID of the created or updated policy.
    """

    # Define the body of the policy
    body = {
        "typeId": "com.vmware.policy.catalog.entitlement",
        "definition": {
            "entitledUsers": [
            {
                "userType": "USER",
                "principals": [
                {
                    "type": "PROJECT",
                    "referenceId": ""
                }
                ],
                "items": [
                {
                    "id": contentSourceId,
                    "type": "CATALOG_SOURCE_IDENTIFIER"
                }
                ]
            }
            ]
        },
        "enforcementType": "HARD",
        "name": "share1",
        "projectId": projectId
    }

    url = f'{baseUrl}/policy/api/policies?page=0&size=20'
    resp = requests.get(url, headers=headers, verify=False)
    print(resp.status_code, resp.text)
    resp.raise_for_status()

    existing = [x for x in resp.json()["content"] if x["projectId"] == projectId and x["name"] == body["name"]]


    if len(existing) == 0:
        url = f'{baseUrl}/policy/api/policies'
        resp = requests.post(url, json=body, headers=headers, verify=False)
        print(resp.status_code, resp.text)
        resp.raise_for_status()
        return resp.json()["id"]
    else:
        return existing[0]["id"]



def getenvID(envList):
    """
        Get the ID of the environment from the given list.

        Args:
            envList (list): List of environments.

        Returns:
            str or None: The ID of the environment if found, None otherwise.
    """
    if envList is None:
        return None

    for item in envList:
         attrMap = dict([(attr.get('name'), attr.get('value'))  for attr in item["attributes"]])
         if attrMap.get('@name') == config["env_name"]:
              return attrMap.get('@id')
    return None


def getVroEndpointID():
    """
        Get the ID of the integrated VRO instance

        Args:
            none

        Returns:
            str or None: The ID of the vro instance if found, None otherwise.
    """

    url = f'{baseUrl}/abx/api/provisioning/endpoints'
    resp = requests.get(url, headers=headers, verify=False)
    #print(resp.status_code, resp.text)
    resp.raise_for_status()
    
    content = resp.json().get('content', [])
    for item in content:
        if item.get('endpointType') == 'vro':
            return item.get('documentSelfLink')

    return None


def matchVraGatewayWorkflowId(WorkflowId):
    """
        Match the given vRO workflow ID with the proxied workflow in vRA 

        Args:
            none

        Returns:
            str or None: The ID of the vro instance if found, None otherwise.
    """

    url = f'{baseUrl}/vro/workflows'
    resp = requests.get(url, headers=headers, verify=False)
    #print(resp.status_code, resp.text)
    resp.raise_for_status()
    
    content = resp.json().get('content', [])
    for item in content:
        if item.get('id') == WorkflowId:
            return WorkflowId

    return None    


def startVroDataCollection(vroInstanceId):
    """
        Match the given vRO workflow ID with the proxied workflow in vRA 

        Args:
            vroInstanceId (str): the ID of the vRO instance

        Returns:
            none
    """
    
    # Send an empty patch to update
    url = f'{baseUrl}/iaas/api/integrations/{vroInstanceId}?apiVersion=2021-07-15'
    #print(url)
    body = {}
    resp = requests.patch(url, json=body, headers=headers, verify=False)
    #print(resp.status_code, resp.text)
    resp.raise_for_status()



######

# Read the config file
config = read_config(configFile)


#blueprintName = config["blue_print_name"]  # Name of the blueprint
WorkflowName = config["workflow_name"]  # Name of the vRO Workflow
DeleteWorkflowName = config["delete_workflow_name"]  # Name of the delete vRO Workflow
vroCrName = config["vro_cr_name"]  # Name of the Custom Resource
vroCrTypeName = config["vro_cr_type_name"]  # Name of the Custom Resource Type
baseUrl = config["aria_base_url"]  # Base URL of Aria deployment
projectName = config["project_name"]  # Retrieve the project name from the config

# Get the authentication token from the VCF Automation (vRA) API
token_url = config["aria_base_url"]+"/csp/gateway/am/api/login?access_token=null"
request_data = {"username": config["aria_username"], "password":config["aria_password"]}
bearer_url = config["aria_base_url"]+"/iaas/api/login"

token = get_vra_auth_token(token_url, request_data, bearer_url)  
headers = {
    'authorization': f'Bearer {token}',
    'content-type': 'application/json',
}
          

# Create or update the project and retrieve its ID
projectId = createOrUpdateProject()


# 'Create' orchestrator workflow
WorkflowId=vroCreateWorkflow(workflowFile=vroWorkflowFile)


# 'Delete' orchestrator workflow
DeleteWorkflowId=vroCreateWorkflow(workflowFile=vroDeleteWorkflowFile)

vroID = getVroEndpointID()
print(vroID)
vroInstanceId=vroID.split('/')[-1]

print(vroInstanceId)

print("Waiting for sync .", end='')
# Start a data collection to sync the embedded vRO workflows, etc.
startVroDataCollection(vroInstanceId = vroInstanceId)

# Wait until we the ID appear in vRA
while matchVraGatewayWorkflowId(WorkflowId=WorkflowId) != WorkflowId:
    time.sleep(5)
    print('.', end='')


print(WorkflowId)

# Create/update the custom resource
"""
properties = {
    "properties": {
        "vm": {"type": "string","title": "vm"},
        "output": {"type": "object","properties": {"name": {"type": "string","title": "name"}},"computed": True}
    }
}
"""
properties = {
  "type": "object",
  "properties": {
    "vm": {
      "type": "string",
      "title": "vm"
    },
    "output": {
      "type": "object",
      "properties": {
        "vimType": {
          "type": "string",
          "title": "vimType"
        },
        "hostName": {
          "type": "string",
          "title": "hostName"
        },
        "memory": {
          "type": "string",
          "title": "memory"
        },
        "vmToolsStatus": {
          "type": "string",
          "title": "vmToolsStatus"
        },
        "productFullVersion": {
          "type": "string",
          "title": "productFullVersion"
        },
        "displayName": {
          "type": "string",
          "title": "displayName"
        },
        "unsharedStorage": {
          "type": "string",
          "title": "unsharedStorage"
        },
        "configStatus": {
          "type": "object",
          "title": "configStatus"
        },
        "type": {
          "type": "string",
          "title": "type"
        },
        "hostMemoryUsage": {
          "type": "string",
          "title": "hostMemoryUsage"
        },
        "productName": {
          "type": "string",
          "title": "productName"
        },
        "biosId": {
          "type": "string",
          "title": "biosId"
        },
        "totalStorage": {
          "type": "string",
          "title": "totalStorage"
        },
        "instanceId": {
          "type": "string",
          "title": "instanceId"
        },
        "mem": {
          "type": "string",
          "title": "mem"
        },
        "id": {
          "type": "string",
          "title": "id"
        },
        "state": {
          "type": "string",
          "title": "state"
        },
        "annotation": {
          "type": "string",
          "title": "annotation"
        },
        "vimId": {
          "type": "string",
          "title": "vimId"
        },
        "overallCpuUsage": {
          "type": "string",
          "title": "overallCpuUsage"
        },
        "connectionState": {
          "type": "string",
          "title": "connectionState"
        },
        "guestMemoryUsage": {
          "type": "string",
          "title": "guestMemoryUsage"
        },
        "guestHeartbeatStatus": {
          "type": "object",
          "title": "guestHeartbeatStatus"
        },
        "ipAddress": {
          "type": "string",
          "title": "ipAddress"
        },
        "cpu": {
          "type": "string",
          "title": "cpu"
        },
        "productVendor": {
          "type": "string",
          "title": "productVendor"
        },
        "guestOS": {
          "type": "string",
          "title": "guestOS"
        },
        "memoryOverhead": {
          "type": "string",
          "title": "memoryOverhead"
        },
        "isTemplate": {
          "type": "boolean",
          "title": "isTemplate"
        },
        "sdkId": {
          "type": "string",
          "title": "sdkId"
        },
        "name": {
          "type": "string",
          "title": "name"
        },
        "committedStorage": {
          "type": "string",
          "title": "committedStorage"
        },
        "vmToolsVersionStatus": {
          "type": "string",
          "title": "vmToolsVersionStatus"
        },
        "vmVersion": {
          "type": "string",
          "title": "vmVersion"
        },
        "alarmActionsEnabled": {
          "type": "boolean",
          "title": "alarmActionsEnabled"
        },
        "overallStatus": {
          "type": "object",
          "title": "overallStatus"
        }
      },
      "computed": True
    }
  },
  "required": []
}    

createOrUpdateVroBasedCustomResource(projectId=projectId, WorkflowId=WorkflowId, DeleteWorkflowId=DeleteWorkflowId, propertySchema=properties, vroID=vroID)


# Create/update the blueprint/template for the project
#blueprintVersion = createOrUpdateBlueprint(projectId)



# Create/update the custom form for users to enter the database specifications
#createOrUpdateDbCrudCustomForm(sourceId, blueprintName)

# Create/update the content sharing policy for the project members to access the required content
#createOrUpdateContentSharingPolicy(projectId, contentSourceId)



