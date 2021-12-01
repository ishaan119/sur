from draughtsman import parse
import api_requests
import yaml


def request(base_url, http_verb,path,data,params, auth):
    api_request = api_requests.APIRequest(base_url)
    return api_request(http_verb,path,data=data,params=params, auth=auth)


def get_config(filename):
    with open(filename, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc


def parse_apib_blueprint_doc(filename):
    transactions = []
    with open(filename, 'r') as f:
        parsed_result = parse(f.read())
        for elem in parsed_result.api.content:
            for t in elem.transitions[0].transactions:
                api_info = {}
                api_info['api_path'] = elem.href.defract
                api_info['http_method'] = elem.transitions[0].transactions[0].request.method.defract

                api_info['response_code'] = int(t.response.status_code.defract)
                api_info['response_body'] = eval(t.response.defract[0])
                if 'hrefVariables' in t.request.attributes.attributes:
                    attrib = t.request.attributes.attributes['hrefVariables'].defract
                    api_info['params'] = dict(attrib)
                transactions.append(api_info)
        return transactions


def run_test(base_url, transaction, auth=None):
    if 'data' in transaction:
        data = transaction['data']
    else:
        data = None
    if 'params' in transaction:
        params = transaction["params"]
    else:
        params = None
    return request(base_url, transaction['http_method'], transaction['api_path'], data, params, auth)


def validate_response(transaction, response):
    result = {'response_code': False, 'response_body': False}
    if int(transaction['response_code']) == response.status_code:
        result['response_code'] = True

    if response.content:
        if transaction['response_body'] == response.json():
            result['response_body'] = True
    return result


def evaluate_display_results(transaction, response, result):
    res = False
    print("############################")
    if result['response_body'] is True and result['response_code'] is True:
        print("Test for API: {0}: Passed".format(transaction['api_path']))
        res = True
    else:
        print("Test for API: {0}: Failed".format(transaction['api_path']))
        print("Transaction Details:")
        print("Expected Response Code: {}".format(transaction['response_code']))
        print("Actual Response Code Received: {}".format(response.status_code))
        print("Expected Response Body: {}".format(yaml.dump(transaction['response_body'])))
        if response.content:
            print("Actual Response Body Received: {}".format(yaml.dump(response.json())))
        else:
            print("Actual Response Body Received: None")
    print("############################")
    return res


def main():
    config = get_config("sur.yml")
    auth = None
    if 'user' in config and 'password' in config:
        auth = (config.get('user'), config.get('password'))

    transactions = parse_apib_blueprint_doc(config.get('blueprint'))
    total_tests = len(transactions)
    test_passed = 0
    for transaction in transactions:
        response = run_test(config.get('base_url'), transaction, auth)
        result = validate_response(transaction, response)
        if evaluate_display_results(transaction, response, result):
            test_passed += 1
    print("{0} passed out of {1}".format(test_passed, total_tests))

if __name__ == "__main__":
    main()
