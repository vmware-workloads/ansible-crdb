# AAP vRO Workflow Installer


### Prerequisites
* AAP installed and running
* Python 3.10 or higher on the machine where the script will be executed
* Aria Automation 8.16 or higher


### Deployment
Open the file 'config.json', and enter the appropriate values for the following parameters:
* aria_base_url: Enter the base url of your Aria deployment
* aria_username: Enter the username of your Aria deployment
* aria_password: Enter the password of your Aria deployment

The other config.json parameters are optional and can be left as is or modified as per your requirements.


Post entering the appropriate values for the above-mentioned parameters, save changes made to the file 'config.json' and run the python script called 'vro_aria.py':
```bash
python3 vro_aria.py
```




