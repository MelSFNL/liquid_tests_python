import requests
import datetime
import yaml
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

class TestObject:
    """This includes all relevant test data for one test, in the correct YAML format. User only needs to remove data
    which is not to be included in a certain test."""

    global_firm_id = 1790
    api_base = f'https://api.getsilverfin.com/api/v4/f/{global_firm_id}/companies/'
    mock_locale = 'en'
    mock_config = None
    mock_data = {}
    result_data = {}
    time_sleep_std = 3

    def __init__(self, auth, company_id_int, main_period_int, reconciliation_id_int, mock_periods_list,
                    secondary_source_recons=None, account_range_param='WBed', rollforward_period=None, starred=True):
        self.auth = auth
        self.company_id_int = company_id_int
        self.main_period_int = main_period_int
        self.reconciliation_id_int = reconciliation_id_int
        self.mock_periods_list = mock_periods_list
        self.secondary_source_recons = secondary_source_recons
        self.account_range_param = account_range_param
        self.starred_param = starred
        self.rollforward_period = rollforward_period
        self.valid_years_list = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020',
                                 '2021', '2022', '2023', '2024', '2025']

        self.expectation_data = {'results': self.result_data}
        self.full_yaml = {'all_test_data': {'context': self.get_context_data(), 'data': {'periods': self.mock_data},
                                            'expectation': self.expectation_data}}

        # Run append data function
        self.append_data(self.auth, self.company_id_int, self.main_period_int, self.reconciliation_id_int, self.mock_periods_list,
                        self.secondary_source_recons, self.account_range_param, self.starred_param)


    def get_context_data(self):

        locale = 'en'
        config = None
        context_data = {}
        context_data['locale'] = locale

        # A non-scalar item needs to be in the list in order to be shown in block style
        context_data['@removeitem_'] = [None, None]
        if config:
            context_data['configuration'] = config
        if self.rollforward_period:
            rf_period = self.get_period(self.rollforward_period)
            context_data['rollforward_period'] = rf_period

        return context_data

    def get_company_data(self, token, company_id):

        # Get company data
        base_url = f'{self.api_base}{company_id}?access_token={token}'
        obtain_company_data = requests.get(base_url).json()
        print(f'obtain_company_data: {obtain_company_data}')
        unused_keys = ['account_mapping_list_id', 'accountancy_synchronisation_entity_id',
                       'accountancy_synchronisation_reference',
                       'administration_synchronisation_entity_id', 'administration_synchronisation_reference',
                       'company_template_id',
                       'created_at', 'folder_name', 'id', 'visible_for_contributors']
        for key in unused_keys:
            obtain_company_data.pop(key)

        obtain_company_data['vat_identifier'] = obtain_company_data.pop('vat')
        obtain_company_data['company_form'] = obtain_company_data.pop('organisation_form')

        # A non-scalar item needs to be in the list in order to be shown in block style
        obtain_company_data['@removeitem_'] = [None, None]

        # Pop empty items from company data
        copy_dict = obtain_company_data.copy()
        for key in copy_dict:
            if not copy_dict[key]:
                obtain_company_data.pop(key)

        return obtain_company_data

    def get_period_result_data(self, token, company_id, period, reconciliation_id):
        base_url = f'{self.api_base}{company_id}/periods/{period}/reconciliations/{reconciliation_id}/results?access_token={token}'
        obtain_results = requests.get(base_url).json()

        # print(f'obtain_results: {obtain_results}')
        return obtain_results

    def get_period(self, input_period):
        period_base_url = f'{self.api_base}{self.company_id_int}/periods/{input_period}?access_token={self.auth}'
        obtain_period = requests.get(period_base_url).json()
        period_date = datetime.datetime.strptime(obtain_period['end_date'], '%Y-%m-%d').date()
        return period_date

    def append_data(self, auth, company_id_int, main_period_int, reconciliation_id_int, mock_periods_list,
                    secondary_source_recons, account_range_param, starred_param):

        # 'data' section
        company_data = self.get_company_data(token=auth, company_id=company_id_int)
        self.full_yaml['all_test_data']['data']['company'] = {}
        for key in company_data:
            self.full_yaml['all_test_data']['data']['company'][key] = company_data[key]

        # Prepare account range var
        account_range_list = account_range_param.split(',')

        print(f'account_range_list {account_range_list}')

        for current_period in mock_periods_list:

            all_period_accounts = []
            prev_length = 0
            page = 1
            loop_condition = True
            while loop_condition:
                accounts_base_url = f'{self.api_base}{company_id_int}/accounts?per_page=1000&page={page}&access_token={auth}'

                if current_period == main_period_int:
                    main_period = True
                else:
                    main_period = False

                # Get account data
                curr_p_accounts = {}

                all_period_accounts.extend(requests.get(accounts_base_url).json())
                page += 1
                if len(all_period_accounts) == prev_length:
                    loop_condition = False

                prev_length = len(all_period_accounts)

            # print(all_period_accounts)

            for item in all_period_accounts:
                indiv_acc_base_url = f'{self.api_base}{company_id_int}/periods/{current_period}/accounts/{item["id"]}?access_token={auth}'
                try:
                    acc_item = requests.get(indiv_acc_base_url).json()
                except json.decoder.JSONDecodeError:
                    pass

                try:
                    account_value = acc_item["value"]
                except KeyError:
                    account_value = 0
                    pass
                sub_dict = {'value': float(account_value), 'id': int(item['id'])}
                sub_dict['@removeitem_'] = [None, None]

                # Check and include only relevant accounts
                for range in account_range_list:
                    if range in item["number"]:
                        acc_no_string = item['number']
                        curr_p_accounts[acc_no_string] = sub_dict
                        break

            # Get reconciliation data
            curr_p_recons = {}
            recon_array = [reconciliation_id_int]
            if len(secondary_source_recons) != 0:
                pass
            else:
                secondary_source_recons = []

            recon_array.extend(secondary_source_recons)

            for recon in recon_array:
                base_url_handle = f'{self.api_base}{company_id_int}/periods/{current_period}/reconciliations/{recon}?access_token={auth}'
                obtain_handle = requests.get(base_url_handle).json()

                handle = obtain_handle['handle']
                base_url_customs = base_url_handle.replace('?access_token', '/custom?page=1&per_page=1000&access_token')
                obtain_customs = requests.get(base_url_customs).json()

                print(f'obtain_customs {obtain_customs}')

                if obtain_customs:
                    curr_p_recons[handle] = {}
                    curr_p_recons[handle]['custom'] = {}

                    for custom_dict in obtain_customs:
                        # From dictionary curr_p_recons, take the key equal to the obtained handle, take the key called 'custom', for which the values are namespace.key
                        if isinstance(custom_dict["value"], dict):
                            custom_dict["value"]['@removeitem_'] = [None, None]
                        curr_p_recons[handle]['custom'][f'{custom_dict["namespace"]}.{custom_dict["key"]}'] = custom_dict["value"]
                        curr_p_recons[handle]['custom']['@removeitem_'] = [None, None]

                    if main_period:
                        curr_p_recons[handle]['starred'] = starred_param

                # Add results from other RTs in mock
                if recon in secondary_source_recons:
                    base_url_results = base_url_handle.replace('?access_token',
                                                               '/results?page=1&per_page=1000&access_token')
                    obtain_results = requests.get(base_url_results).json()

                    curr_p_recons[handle]['results'] = obtain_results

                    # A non-scalar item needs to be in the list in order to be shown in block style
                    curr_p_recons[handle]['results']['@removeitem_'] = [None, None]



            # Get people data
            curr_p_people = None

            # Comment call get_period function
            period_date = self.get_period(current_period)

            # Mock main period under context section
            if main_period:
                self.full_yaml['all_test_data']['context']['period'] = period_date

            self.full_yaml['all_test_data']['data']['periods'][period_date] = {}
            if curr_p_accounts:
                self.full_yaml['all_test_data']['data']['periods'][period_date]['accounts'] = curr_p_accounts
            if curr_p_recons:
                self.full_yaml['all_test_data']['data']['periods'][period_date]['reconciliations'] = curr_p_recons
            if curr_p_people:
                self.full_yaml['all_test_data']['data']['periods'][period_date]['people'] = curr_p_people

            if main_period == True:

                # 'expectations' section
                period_result_data = self.get_period_result_data(token=auth, company_id=company_id_int, period=main_period_int,
                                                                 reconciliation_id=reconciliation_id_int)

                print(f'period_result_data: {period_result_data}')

                # Transform data items
                if 'None' or None in period_result_data.values():
                    for dict_key in period_result_data.keys():
                        if period_result_data[dict_key] == 'None':
                            period_result_data[dict_key] = None
                if 'NaN' in period_result_data.values():
                    for dict_key in period_result_data.keys():
                        if period_result_data[dict_key] == 'NaN':
                            period_result_data[dict_key] = '.NaN'

                # Add reconciled based on status key (if available)
                try:
                    if period_result_data['status'] == 'reconciled':
                        recon_val = True
                    else:
                        recon_val = False
                except KeyError:
                    recon_val = False
                self.full_yaml['all_test_data']['expectation']['reconciled'] = recon_val

                # Add rollforwards
                rollf_json = self.get_rollforward(self.company_id_int, self.main_period_int, self.reconciliation_id_int)
                if len(list(rollf_json)) != 0:
                    self.full_yaml['all_test_data']['expectation']['rollforward'] = {}
                    self.full_yaml['all_test_data']['expectation']['rollforward']['@removeitem_'] = [None, None]

                print(f'rollf_json {rollf_json}')

                save_key_old = ''
                for item in rollf_json:
                    split_key = item['name'].split('.')
                    if len(split_key) <= 2:
                        self.full_yaml['all_test_data']['expectation']['rollforward'][item['name']] = item['value']
                    elif len(split_key) >= 3:
                        save_key_new = split_key[0]+'.'+split_key[1]
                        if save_key_new == save_key_old:
                            self.full_yaml['all_test_data']['expectation']['rollforward'][save_key_new][split_key[2]] = item['value']
                            self.full_yaml['all_test_data']['expectation']['rollforward'][save_key_new]['@removeitem_'] = [None, None]
                        else:
                            self.full_yaml['all_test_data']['expectation']['rollforward'][save_key_new] = {}
                            self.full_yaml['all_test_data']['expectation']['rollforward'][save_key_new][split_key[2]] = item['value']
                        save_key_old = split_key[0]+'.'+split_key[1]


                # Add results
                self.full_yaml['all_test_data']['expectation']['results'] = period_result_data
                for key in self.full_yaml['all_test_data']['expectation']['results']:
                    if isinstance(self.full_yaml['all_test_data']['expectation']['results'][key], bool) or self.full_yaml['all_test_data']['expectation']['results'][key] in self.valid_years_list:
                        pass
                    else:
                        try:
                            self.full_yaml['all_test_data']['expectation']['results'][key] = float(self.full_yaml['all_test_data']['expectation']['results'][key])
                        except (ValueError, TypeError) as error_tup:
                            pass
                self.full_yaml['all_test_data']['expectation']['results']['@removeitem_'] = [None, None]

    def get_rollforward(self, company_id_int, main_period_int, reconciliation_id_int):

        # Username
        def_usr_id = ''
        def_usr_pw = ''

        chrome_options = Options()
        chrome_options.add_argument("--headless")

        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

        # Navigate to rollforward section in HTML tree
        driver.get(f'https://live.getsilverfin.com/f/1790/{company_id_int}/ledgers/{main_period_int}/reconciliation_texts/{reconciliation_id_int}')
        time.sleep(self.time_sleep_std)
        username = driver.find_element_by_id("global_user_email")
        password = driver.find_element_by_id("global_user_password")
        username.send_keys(def_usr_id)

        # Do not store password in script. Safe + secure
        if def_usr_pw:
            enter_pass_key = def_usr_pw
        else:
            enter_pass_key = input('Enter password for sf main account:')
        password.send_keys(enter_pass_key)
        password.send_keys(Keys.RETURN)

        time.sleep(self.time_sleep_std)
        driver.get(driver.current_url+'?debug=1')
        time.sleep(self.time_sleep_std)
        rollf_tree = driver.find_element_by_xpath('.//*[@id="liquid-debug"]/div/div/div/details[8]/pre')
        time.sleep(self.time_sleep_std)
        attr = rollf_tree.get_attribute('innerHTML')
        rollf_tree_json = json.loads(attr)

        return rollf_tree_json

    def give_yaml(self):

        # Difficulties with dropping '@removeitem_' appropriately, this requires first dumping into text, then parsing the text into lines variable, then conditionally rewriting
        with open(r'/Users/melle/PycharmProjects/Silverfin/store_file_new.txt', 'w') as file:
            yaml.dump(self.full_yaml, file, default_flow_style=None, width=1000, Dumper=NoAliasDumper, default_style=None)

        with open(r'/Users/melle/PycharmProjects/Silverfin/store_file_new.txt', 'r') as output_file:
            lines = output_file.readlines()

        with open(r'/Users/melle/PycharmProjects/Silverfin/store_file_new.yaml', 'w') as yaml_file:
            for line in lines:
                if not '@removeitem_' in line:
                    yaml_file.write(line)



