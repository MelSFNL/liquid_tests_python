# liquid_tests_python
Automatically create a YAML liquid test using python and Silverfin API
create_test_yaml.py: Get API key and provide input parameters.
The following API global variables need to be updated in this python file to make it work:
    global_firm_id = '1790'
    global_client_id = ''
    global_secret = ''
    redirect_uri = ''

    All input parameters in the test section starting from line 50, most importantly provide_template_url. Currently includes example data from a NL file

CreateTest.py: Generate YAML based on input parameters
The following global variables need to be updated in this python file to make it work.
These are your SF admin username and password, although this is for the scraping of the RF parameters only:
    def_usr_id = ''
    def_usr_pw = ''

Recall that you need a full scope API authorisation + all import packages need to be installed first if you want to run the python script.
