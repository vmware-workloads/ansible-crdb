import requests
import yaml
import json
import urllib3
urllib3.disable_warnings()
from datetime import datetime
import time
import sys
import hashlib



sourceId = "" 
contentSourceId = ""


# Files

configFile = f'config.json' # Name of the configuration file
vroWorkflowFile=f'vro_workflow.json'
vroDeleteWorkflowFile=f'vro_delete_workflow.json'
blueprintFile=f'aria_blueprint.yaml'



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



def createOrUpdateBlueprint(projectId, blueprint_filename, blueprintDetails):
    """
        Creates or updates the blueprint/template for the given project.

        Args:
            projectId (str): The ID of the project.
            blueprint_filename (str): Name of the blueprint file

        Returns:
            str: The new version of the blueprint.
    """


    print("Update blueprint ...")
    print(blueprintDetails['name'])
    print(blueprintDetails['version'])
    body = {
        "name":blueprintDetails['name'],
        "description":"",
        "valid":True,
        "content": open(blueprint_filename).read(),  # The file to read the blueprint specifications from
        "projectId": projectId,
        "requestScopeOrg":True}

    # Get the list of existing blueprints/templates
    url = f'{baseUrl}/blueprint/api/blueprints?apiVersion=2019-09-12'
    resp = requests.get(url, headers=headers, verify=False)
    existing = [x for x in resp.json()["content"] if x["name"] == blueprintDetails['name']]
    existing_ver = ""


    # Update the blueprint if it already exists
    if len(existing) > 0:
        # get the versions
        blueprintId = existing[0]['id']
        url = f'{baseUrl}/blueprint/api/blueprints/{blueprintId}/versions?apiVersion=2019-09-12'
        resp = requests.get(url, headers=headers, verify=False)
        existing_ver = [x for x in resp.json()["content"] if x["id"] == blueprintDetails['version']]

        # if the version already exists, just update it
        if len(existing_ver) > 0:
            print("existing blueprint version found, updating...")
            url = f'{baseUrl}/blueprint/api/blueprints/{blueprintId}?apiVersion=2019-09-12'
            resp = requests.put(url, json=body, headers=headers, verify=False)
            print(resp.status_code, resp.text)
            
    else:
        # Create a blueprint with the desired specifications if it doesn't already exist
        url = f'{baseUrl}/blueprint/api/blueprints?apiVersion=2019-09-12'
        resp = requests.post(url, json=body, headers=headers, verify=False)
        print(resp.status_code, resp.text)
        blueprintId = resp.json()['id']

    if len(existing_ver) == 0:
        # Create a new version 
        newVersion = blueprintDetails['version']
        body = {"version": newVersion,"description":"","changeLog":"","release":True}
        url = f'{baseUrl}/blueprint/api/blueprints/{blueprintId}/versions?apiVersion=2019-09-12'
        resp = requests.post(url, json=body, headers=headers, verify=False)
        print(resp.status_code, resp.text)
        return newVersion




def vroCreateWorkflow(workflowFile, WorkflowName):
    """
        Creates a VRO (VMware vRealize Orchestrator) workflow.

        This function sends a POST request to update the VRO create workflow with the specified body.

        Returns:
            Id of workflow
    """

    with open(workflowFile) as workflow_file:
        workflow = json.load(workflow_file)


    workflow["name"] = WorkflowName
    #print(workflow["name"])

    # Get the list of existing workflows from the vro proxy
    url = f'{baseUrl}/vro/workflows?page=0&size=9999'
    resp = requests.get(url, headers=headers, verify=False)
    #print(resp.status_code, resp.text)
    resp.raise_for_status()
    existing = [x for x in resp.json()["content"] if x["name"] == workflow["name"]]

    # make sure it also exists in the vro inventory
    if len(existing) > 0:
        url = f'{baseUrl}/vco/api/workflows'
        resp = requests.get(url, headers=headers, verify=False)
        response_data = resp.json()
        for link in response_data.get('link', []):
            for attribute in link.get('attributes', []):
                if attribute.get('value') == workflow["name"]:
                    print(f'Found existing workflow: {workflow["name"]}')
                    return existing[0]['id']

    # Create a new Workflow if it doesn't exist yet 
    url = f'{baseUrl}/vco/api/workflows'
    resp = requests.post(url, json=workflow, headers=headers, verify=False)
    print(resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()["id"]






def createOrUpdateVroBasedCustomResource(projectId, WorkflowId, DeleteWorkflowId, propertySchema, externalType, vroID):
    """
         Creates or updates the custom resource
         Uses the same ABX for create/read/update/delete - the ABX needs the logic 
         to deal with each.


        Args:
            projectId (str): The ID of the project.
            abxActionId (str): The ID of the ABX action.
            propertySchema (dict): Schema of the Custom Resource. 
            externalType (str): Type of SDK object the workdlow returns, e.g. "VC:VirtualMachine"
            vroID: The ID of the vro instance

        Returns:
            None
    """

    custom_resource_exists = False
    # The extensibility action that this custom resource should be associated with
    vroWorkflow = {
        "id": WorkflowId,
        "name": WorkflowName,
        "projectId": projectId,
        "type":"vro.workflow",
        "inputParameters": [{"type": "string","name": "vm"}],
        "outputParameters": [{"type": "VC:VirtualMachine","name": "output"}],
        "endpointLink": vroID
    }

    vroDeleteWorkflow = {
        "id": DeleteWorkflowId,
        "name": DeleteWorkflowName,
        "projectId": projectId,
        "type":"vro.workflow",
        "inputParameters": [{"type": "VC:VirtualMachine","name": "vm"}],
        "endpointLink": vroID
    }    


    # create the body of the request 
    body = {
        "displayName": vroCrName,
        "description":"",
        "resourceType": vroCrTypeName,
        "externalType": externalType,
        "status":"RELEASED",
        "mainActions": {
          "create": vroWorkflow,
          "delete":  vroDeleteWorkflow,
        },
        "properties": propertySchema,
        "schemaType": "VRO_INVENTORY"
    }

    #print(body)


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
        print(f'Found existing custom resource: {vroCrName}\n\n')
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

    url = f'{baseUrl}/vro/workflows?page=0&size=9999&expand=true'
    resp = requests.get(url, headers=headers, verify=False)
    #print(resp.status_code, resp.text)
    resp.raise_for_status()
    
    content = resp.json().get('content', [])
    for item in content:
        if item.get('id') == WorkflowId:
            #print(WorkflowId)
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


def getBlueprintName(blueprintFile):
    """
        Reads the metadata from the blueprint yaml to get the name & version
        -- assuming this info is present 

        Args:
            blueprintFile (str): name of the aria blueprint file

        Returns:
            str: The name and version as per the blueprint OR a generic response

    """    

    # Generic response defined if we have issues - 
    # Set the blueprint name to the blueprint filename plus a hash
    blueprintDetails = dict();
    filehash=hashlib.md5(open(blueprintFile,'rb').read()).hexdigest()
    blueprintDetails['name'] = f"{blueprintFile.split('.')[0]}_{filehash}"
    blueprintDetails['version'] = datetime.now().strftime("%d-%m-%H-%M-%S")



    # Ensure we have the values of 'name' and 'version' present
    # Otherwise add a uuid or give a generic response as needed

    if len(blueprintFile) > 0: 
        with open(blueprintFile) as stream:
            try:
                blueprint = yaml.safe_load(stream)
                try:
                    blueprintDetails['name'] = blueprint['name']
                except:   
                    pass

                try:
                    blueprintDetails['version'] = blueprint['version']
                except:
                    pass  

            # If we can't read the file, we just return the generic response
            # incase it's a python or fileread error
            except yaml.YAMLError as exc:
                print(exc) 
 
        return blueprintDetails


    # Return nothing if we've been given nothing - i.e. if the filename is blank           
    else:
        return None               



def poll_function(func, target_value, sleepTime, timeout=None, *args, **kwargs):
    """
        Simple poll function to try a command and wait a given time/timeout 
        until the function returns what's expected

        Args:
            func (str): name of the function to call
            target_value (str): eventual output expected from function
            sleepTime (int): how many seconds to wait between tries
            timeout (int): time in seconds to give up

        Returns:
            none
    """
    
    start_time = time.time()
    
    while True:
        print('.', end='')  
        result = func(*args, **kwargs)
        #print(f'matching {result} with {target_value}')
        
        if result == target_value:
            return result
        
        if timeout and (time.time() - start_time) >= timeout:
            raise TimeoutError("Polling timed out.")
        
        time.sleep(sleepTime)  # Sleep for 5 seconds between checks

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


# Get the blueprint name+version from the blueprint file
blueprintDetails=getBlueprintName(blueprintFile)

print(blueprintDetails['name'])
print(blueprintDetails['version'])




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
WorkflowId=vroCreateWorkflow(workflowFile=vroWorkflowFile, WorkflowName=WorkflowName)


# 'Delete' orchestrator workflow
DeleteWorkflowId=vroCreateWorkflow(workflowFile=vroDeleteWorkflowFile, WorkflowName=DeleteWorkflowName)

vroID = getVroEndpointID()
#print(vroID)
vroInstanceId=vroID.split('/')[-1]

#print(WorkflowId)
#print(DeleteWorkflowId)

print("Waiting for sync .", end='')
# Start a data collection to sync the embedded vRO workflows, etc.
startVroDataCollection(vroInstanceId = vroInstanceId)

  

poll_function(matchVraGatewayWorkflowId, 
               target_value=WorkflowId, 
               sleepTime=5, 
               timeout=120,
               WorkflowId=WorkflowId)

poll_function(matchVraGatewayWorkflowId, 
               target_value=DeleteWorkflowId, 
               sleepTime=5, 
               timeout=120,
               WorkflowId=DeleteWorkflowId)

print("\n\nFound Workflows\n\n")

# Create/update the custom resource
# first we define the input/output schema, as per the spec in the vro workflow
# - needs at least one 'computed' value
properties = {
  "type": "object",
  "properties": {
    "vm": {"type": "string","title": "vm"},
    "output": {
      "type": "object",
      "properties": {
        "vimType": { "type": "string", "title": "vimType" },
        "hostName": { "type": "string", "title": "hostName" },
        "memory": { "type": "string", "title": "memory" },
        "vmToolsStatus": { "type": "string", "title": "vmToolsStatus" },
        "productFullVersion": { "type": "string", "title": "productFullVersion" },
        "displayName": { "type": "string", "title": "displayName" },
        "unsharedStorage": { "type": "string", "title": "unsharedStorage" },
        "configStatus": { "type": "object", "title": "configStatus" },
        "type": { "type": "string", "title": "type" },
        "hostMemoryUsage": { "type": "string", "title": "hostMemoryUsage" },
        "productName": { "type": "string", "title": "productName" },
        "biosId": { "type": "string", "title": "biosId" },
        "totalStorage": { "type": "string", "title": "totalStorage" },
        "instanceId": { "type": "string", "title": "instanceId" },
        "mem": { "type": "string", "title": "mem" },
        "id": { "type": "string", "title": "id" },
        "state": { "type": "string", "title": "state" },
        "annotation": { "type": "string", "title": "annotation" },
        "vimId": { "type": "string", "title": "vimId" },
        "overallCpuUsage": { "type": "string", "title": "overallCpuUsage" },
        "connectionState": { "type": "string", "title": "connectionState" },
        "guestMemoryUsage": { "type": "string", "title": "guestMemoryUsage" },
        "guestHeartbeatStatus": { "type": "object", "title": "guestHeartbeatStatus" },
        "ipAddress": { "type": "string", "title": "ipAddress" },
        "cpu": { "type": "string", "title": "cpu" },
        "productVendor": { "type": "string", "title": "productVendor" },
        "guestOS": { "type": "string", "title": "guestOS" },
        "memoryOverhead": { "type": "string", "title": "memoryOverhead" },
        "isTemplate": { "type": "boolean", "title": "isTemplate" },
        "sdkId": { "type": "string", "title": "sdkId" },
        "name": { "type": "string", "title": "name" },
        "committedStorage": { "type": "string", "title": "committedStorage" },
        "vmToolsVersionStatus": { "type": "string", "title": "vmToolsVersionStatus" },
        "vmVersion": { "type": "string", "title": "vmVersion" },
        "alarmActionsEnabled": { "type": "boolean", "title": "alarmActionsEnabled" },
        "overallStatus": { "type": "object", "title": "overallStatus" }
      },
      "computed": True
    }
  },
  "required": []
}    

externalType="VC:VirtualMachine"

createOrUpdateVroBasedCustomResource(projectId=projectId, 
                                    WorkflowId=WorkflowId, 
                                    DeleteWorkflowId=DeleteWorkflowId, 
                                    propertySchema=properties,
                                    externalType=externalType, 
                                    vroID=vroID)


# Create/update the blueprint/template for the project
createOrUpdateBlueprint(projectId, blueprintFile, blueprintDetails)

# Create/update the content sharing policy for the project members to access the required content
#createOrUpdateContentSharingPolicy(projectId, contentSourceId)



