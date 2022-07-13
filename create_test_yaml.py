"""
PSEUDOCODE FOR CREATE_TEST_YAML

(1) Calls API and create API object

(2) Build YAML in correct format line-for-line based on all available data
- Periods should be current and previous
- Mock all accounts in the scheme, determine which ones to collapse (!)
- Mock all custom variables

"""

global_firm_id = '1790'
global_client_id = ''
global_secret = ''
redirect_uri = ''

# Initial auth code - this one needs8 to be manually renewed to run the app again
authorization_url_code = 'B7_FHLJBrcR6iPsNX5zdEjgM4sXXJBmyhMailwDZZqg'

import requests
import CreateTest

def get_authorisation_new(firm_id=global_firm_id, client_id=global_client_id, redirect_uri=redirect_uri, scope='user:profile user:email webhooks administration:write permanent_documents:write communication:write financials:write financials:transactions:write workflows:write'):
    try:
        with open('refresh_token.txt', 'r') as file:
            old_refr_token = file.read()
            print(f'OLD refresh token: {old_refr_token}')
        access_resp = requests.post(f"https://live.getsilverfin.com/f/:{firm_id}/oauth/token?client_id={client_id}&client_secret={global_secret}&redirect_uri={redirect_uri}&grant_type=refresh_token&refresh_token={old_refr_token}").json()
        print(access_resp)
        refresh_token = access_resp['refresh_token']
        with open('refresh_token.txt', 'w') as file:
            file.write(refresh_token)
            print(f'NEW refresh token: {refresh_token}')
        return access_resp['access_token']
    except (KeyError, FileNotFoundError) as auth_error_tup:
        token_request = requests.post(
            f"https://live.getsilverfin.com/f/:{firm_id}/oauth/token?client_id={client_id}&client_secret={global_secret}&redirect_uri={redirect_uri}&grant_type=authorization_code&code={authorization_url_code}")
        token_dict = token_request.json()
        print(f'token_dict: {token_dict}')
        first_refresh_token = token_dict['refresh_token']
        access_resp = requests.post(
            f"https://live.getsilverfin.com/f/:{firm_id}/oauth/token?client_id={client_id}&client_secret={global_secret}&redirect_uri={redirect_uri}&grant_type=refresh_token&refresh_token={first_refresh_token}").json()
        re_use_refresh_token = access_resp['refresh_token']
        with open('refresh_token.txt', 'w') as file:
            file.write(re_use_refresh_token)
        return access_resp['access_token']


if __name__ == "__main__":
    # Preliminary stuff
    auth = get_authorisation_new()

    company_id_int = 00
    main_period_int = 00
    reconciliation_id_int = 00
    mock_periods_list = [00, 00]
    secondary_source_recons = [40058346, 31224659]
    range_param = "BLas,WFbe"

    # Optional: add_url
    provide_template_url = 'https://live.getsilverfin.com/f/1790/1123869/ledgers/22080499/workflows/1603806/reconciliation_texts/31224678'
    try:
        if provide_template_url:
            company_id = provide_template_url.replace('https://live.getsilverfin.com/f/1790/', '')[0:7]
            company_id_int = int(company_id.replace('/', ''))
            main_period = provide_template_url.replace(
                f'https://live.getsilverfin.com/f/1790/{company_id_int}/ledgers/', '')[0:8]
            main_period_int = int(main_period.replace('/', ''))
            reconciliation_id_int = int(provide_template_url[-8:])
            mock_periods_list = [main_period_int]
    except NameError:
        pass

    # Create actual test / check parameters! company_id_int, main_period_int, reconciliation_id_int, mock_periods_list,
    #                     secondary_source_recons=None, account_range_param='WBed', rollforward_period=None

    # Test line for direct API calls
    # print('test')
    # print(requests.get(f'http://api.getsilverfin.com/api/v4/f/1790/companies/1123869/periods/26555732/reconciliations/40058346?access_token={auth}').json())

    obj = CreateTest.TestObject(auth, company_id_int, main_period_int, reconciliation_id_int, mock_periods_list, secondary_source_recons, range_param)
    test = obj.give_yaml()
