AAP vRO Workflow Installer
==========================

Installs the given aria blueprint and vro workflows into aria automation.  
The automation will then be available in Service Broker.

 

### Prerequisites

-   AAP installed and running

-   Python 3.10 or higher on the machine where the script will be executed

-   Aria Automation 8.16 or higher

 

### Deployment

Open the file 'config.json', and enter the appropriate values for the following
parameters:

 

\* aria_base_url: Enter the base url of your Aria deployment  
\* aria_username: Enter the username of your Aria deployment  
\* aria_password: Enter the password of your Aria deployment

 

The other config.json parameters are optional and can be left as is or modified
as per your requirements.

 

After updating the configuration file, run the installer script:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ bash
python3 vro_aria.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
