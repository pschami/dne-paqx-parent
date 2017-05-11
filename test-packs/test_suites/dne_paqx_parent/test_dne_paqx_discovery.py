import os
import time
import json
import pytest
import requests
import requests.exceptions
import af_support_tools
from . import globals as gbl

# Get vars from env ini file
env_file = 'env.ini'
ipaddress = af_support_tools.get_config_file_property(config_file=env_file, heading='Base_OS', property='hostname')
ssh_user = af_support_tools.get_config_file_property(config_file=env_file, heading='Base_OS', property='username')
ssh_pass = af_support_tools.get_config_file_property(config_file=env_file, heading='Base_OS', property='password')

# Get vars from config ini file and set the values
conf_file = 'dne_paqx_parent/core_config.ini'
port = af_support_tools.get_config_file_property(config_file=conf_file, heading='dne_paqx_parent', property='port')
rmq_username = af_support_tools.get_config_file_property(config_file=conf_file, heading='dne_paqx_parent', property='rmq_username')
rmq_password = af_support_tools.get_config_file_property(config_file=conf_file, heading='dne_paqx_parent', property='rmq_password')
node_id = af_support_tools.get_config_file_property(config_file=conf_file, heading='dne_paqx_parent', property='node_id')
rackhd_ip = af_support_tools.get_config_file_property(config_file=conf_file, heading='dne_paqx_parent', property='rackhd_ip')
mac_address = af_support_tools.get_config_file_property(config_file=conf_file, heading='dne_paqx_parent', property='mac_address')

rmq_username = 'guest'
rmq_password = 'guest'
port = 5672
node_id = '111111111111111111111111'

#####################################################################
# These are the main tests.
#####################################################################
@pytest.mark.dne_paqx_parent
@pytest.mark.dne_paqx_parent_mvp_extended
# First Test
def test_preprocess_workflows():
    print("\n=======================Preprocess Work Flow Test Begin=======================\n")

    # Step 1: Invoke /dne/preprocess REST API call to gather the info that will be needed for add node.
    print("POST /dne/preprocess REST API call to gather the info that will be needed for add node...\n")
    preprocess()

    # Step 2: Invoke /dne/preprocess/{jobId} REST API call to get the status
    print("GET /dne/preprocess/<jobId> REST API call to get the preprocess job status...\n")
    preprocess_status()

    print("\n=======================Preprocess Work Flow Test End=======================\n")


@pytest.mark.dne_paqx_parent
@pytest.mark.dne_paqx_parent_mvp_extended
# Second Test (run after the test_preprocess_worksflows)
def test_add_node_workflows():
    print("\n=======================Add Node Work Flow Test Begin=======================\n")
    # Step 1: Register the rackHD adapter end point. (workaround for consul registeration, can be removed later)
    print("Register rackHD adapter end point...\n")
    consulBypassMsg()

    # Step 2: Simulate the discovery of a new node. (replace the rackHD VM discover the dell node)
    print("Simulate discovering a new node by publishing node event...\n")
    simulate_node_discovery()

    # Step 3: Invoke /dne/nodes REST API call to get the discovered node's uuid.
    print("GET /dne/nodes REST API call to get the discovered node and it's uuid...\n")
    gbl.my_data['uuid'] = get_new_node_uuid()
    assert gbl.my_data['uuid']

    # Step 4: Invoke /dne/node REST API call to provision an unallocated node.
    print("POST /dne/nodes REST API call to provision an unallocated node...\n")
    add_node()

    # Step 5: Invoke /dne/nodes/{jobId} REST API call to get the status
    print("GET /dne/nodes/<jobId> REST API call to get the add node job status until unallocated node being found...\n")
    found_node()

    # Step 6: Validate return response from the /dne/complete-add-node REST API call - may not needed anymore.
    # print("Validate return response from the /dne/complete-add-node REST API call\n")
    # validate_complete_add_node()

    print("\n=======================Add Node Work Flow Test End=======================\n")


@pytest.mark.dne_paqx_parent
@pytest.mark.dne_paqx_parent_mvp_extended
def test_DellNodeExp():
    print('\nRunning Test on system: ', ipaddress)
    cleanup()
    bindQueues()
    consulBypassMsg()
    time.sleep(3)

    # Step 1: Verify the rackhd.node.discovered.event exchange is bound to paqx.node.discovery.request queue.
    # Test will fail is this isnt done. Format: validate_queues_on_exchange(exchange, expected queue)
    validate_queues_on_exchange('exchange.dell.cpsd.adapter.rackhd.node.discovered.event', 'queue.dell.cpsd.paqx.node.discovery.event')

    # Step 2: Verify the api list is empty
    currentNodes = listDellNodesAPI()
    assert currentNodes == '[]'

    # Step 3: Trigger a delete Node on RackHD. This will remove our test Dell node from RackHD. RachHD will then
    # "discover" it and a node discovered event will be triggered.
    statuscode = delete_rackhd_node_entry(mac_address, rackhd_ip)
    assert statuscode == 204, 'incorrect status code returned'
    print('\nPlease wait: Test Node is being deleted from RackHD')
    print('When rediscovered a New Node Event will be triggered...\n')

    # Step 4: Verify the node was discovered and return the EIDS supplied UUID
    uuid = rmqNodeDiscover()

    # Step 5: Verify the API now lists the discovered UUID
    currentNodes = listDellNodesAPI()
    currentNodes = json.loads(currentNodes, encoding='utf-8')
    apiUuid = currentNodes[0]['symphonyUuid']
    assert uuid == apiUuid
    print('\nTest Pass: Node has been discovered\n')

    cleanup()


#####################################################################
# These are supporting functions called throughout the test.
#####################################################################

def simulate_node_discovery():
    print("Publishing a node event with node id as ", node_id)
    my_routing_key = 'node.discovered.information.' + node_id + '.' + node_id
    filePath = os.environ['AF_TEST_SUITE_PATH'] + '/dne_paqx_parent/fixtures/nodeEvent.json'
    with open(filePath) as fixture:
        my_payload = fixture.read()
        af_support_tools.rmq_publish_message(host=ipaddress, rmq_username=rmq_username, rmq_password=rmq_password,
                                         exchange='on.events',
                                         routing_key=my_routing_key,
                                         headers={
                                             '__TypeId__': ''},
                                         payload=my_payload)


def get_new_node_uuid():
    timeout = 60
    interval = 5
    # Try to get the new node until timeout.
    while timeout >= 0:
        currentNodes = listDellNodesAPI()
        currentNodes = json.loads(currentNodes, encoding='utf-8')
        if (len(currentNodes)):
            for node in currentNodes:
                if node['nodeId']  == node_id:
                    print("Found unallocated new node {} with uuid {}", node['nodeId'], node['symphonyUuid'])
                    return node['symphonyUuid']
        else:
            print("no unallocated node found, retry ...")

        time.sleep(interval)
        timeout -= 5
    # No new node being found.
    print("timeout, no new node being found.")
    return ''


def preprocess():
    headers = {'Content-Type': 'application/json'}
    filePath = os.environ['AF_TEST_SUITE_PATH'] + '/dne_paqx_parent/fixtures/payload_addnode.json'
    with open(filePath) as fixture:
        request_body = json.loads(fixture.read())
        endpoint = "/preprocess"
        url = gbl.my_data['dne_base_url'] + endpoint
        response = requests.post(url, json=request_body, headers=headers)
        # verify the status_code
        assert response.status_code == 200

        data = response.json()
        gbl.my_data['preprocess_workflow_id'] = data['workflowId']
        # Assert (TBD: will add more checkings later ...)
        assert data['workflow'] == 'preProcessWorkflow'
        for link in data['links']:
            if link['rel'] is 'self':
              assert link['href'] == "/nodes/" + data['workflowId'] + "/startPreProcessWorkflow"


def preprocess_status():
    endpoint = "/preprocess/" + gbl.my_data['preprocess_workflow_id']
    url = gbl.my_data['dne_base_url'] + endpoint
    response = requests.get(url)
    # verify the status_code
    assert response.status_code == 200
    data = response.json()
    # Assert
    task_list = ['Find VCluster', 'Find ProtectionDomain', 'Find SystemData', 'Assign Default HostName', 'Assign Default Credentials']
    assert data['workflow'] == 'preProcessWorkflow'
    assert len(data['workflowTasksResponseList']) == len(task_list)
    for task in data['workflowTasksResponseList']:
        print("checking response for task: ", task['workFlowTaskName'])
        if task['workFlowTaskName'] not in task_list:
            print("task: {} is not matching with expected task", task['workFlowTaskName'])
            assert False
        assert task['workFlowTaskStatus'] == 'SUCCEEDED'


def add_node():
    headers = {'Content-Type': 'application/json'}
    filePath = os.environ['AF_TEST_SUITE_PATH'] + '/dne_paqx_parent/fixtures/payload_addnode.json'
    with open(filePath) as fixture:
        request_body = json.loads(fixture.read())
        response = requests.post(gbl.my_data['add_node_url'], json=request_body, headers=headers)
        # verify the status_code
        assert response.status_code == 200

        # Check response content and save it to shared variable.
        data = response.json()
        gbl.my_data['add_node_resp'] = data
        gbl.my_data['workflow_id'] = data['workflowId']
        assert gbl.my_data['workflow_id']
        print("addnode workflow id is", gbl.my_data['workflow_id'])

        # Assert
        assert resp_dict['workflow'] == 'addNode'
        for link in resp_dict['links']:
            if link['rel'] is 'self':
              assert link['href'] == "/workflows/" + gbl.my_data['workflow_id'] + "/startAddNodeWorkflow"


def addnode_status():
    status = ''
    nodeInfo = []
    task_list = ['findDiscoveredNodesTaskHandler']

    print("Get the addnode status...")
    endpoint = "/nodes/" + gbl.my_data['preprocess_workflow_id']
    url = gbl.my_data['dne_base_url'] + endpoint
    response = requests.get(url)
    # verify the status_code
    assert response.status_code == 200
    data = response.json()
    assert data['workflow'] == 'addNode'
    assert len(data['workflowTasksResponseList']) == len(task_list)
    assert data['workflowTasksResponseList'][0]['workFlowTaskName'] == task_list[0]

    # Unallocated node should be found when the "workflowTaskStatus" is "SUCCEEDED" for "findDiscoveredNodesTaskHandler"
    print("Checking workflowtaskstatus for findDiscoveredNodesTaskHandler...")
    status = data['workflowTasksResponseList'][0]['workFlowTaskStatus']
    nodesInfo = data['workflowTasksResponseList'][0]['nodesInfo']
    return status, nodesInfo


def found_node():
    timeout = 10
    nodeInfo = []
    exp_str = "SUCCEEDED"
    status, nodesInfo = addnode_status()
    while (status is not exp_str) and (timeout >= 0):
        # retry...
        time.sleep(1)
        status, nodesInfo = addnode_status()
        print("Current findDiscoveredNode task status is ", status)
        timeout-=1

    if (status == exp_str) and len(nodesInfo):
        for node in nodesInfo:
            if (node['nodeId'] == node_id) and (node['symphonyUuid'] ==gbl.my_data['uuid']):
                print("Found expected node with node id {} and uuid {}", node_id, node['symphonyUuid'])
                assert True
                return
    else:
        print("No unallocated node with uuid as {} being found within {} seconds.", node['symphonyUuid'], timeout)
        assert False


def validate_complete_add_node():
    headers = {'Content-Type': 'application/json'}
    endpoint = "/workflows/" + gbl.my_data['workflow_id'] + "/complete-add-node"
    url = gbl.my_data['dne_base_url'] + endpoint
    request_body = ''
    response = requests.post(url, json=request_body, headers=headers)
    # verify the status_code
    assert response.status_code == 200
    data = response.json()

    # Assert
    assert data['workflow'] == 'addNode'
    for link in data['links']:
        if link['rel'] is 'self':
          assert link['href'] == "/workflows/" + gbl.my_data['workflow_id'] + '/complete-add-node'
        if link['rel'] is 'next-step':
          assert link['href'] == "/workflows/" + gbl.my_data['workflow_id']


def validate_found_node():
    # looking for the "Found available nodes" and UUID.
    exp_str = "Found available nodes"
    exp_uuid = gbl.my_data['uuid']
    cmd = 'grep -i ' + exp_str + ' /opt/dell/cpsd/dne-paqx/logs/dne-paqx-info.log'
    output = af_support_tools.send_ssh_command(host=ipaddress, username=ssh_user, password=ssh_pass, command=cmd, return_output=True)
    print("output is ", output)

    assert output
    if exp_str in output and exp_uuid in output:
        print("Found unallocated node with uuid ", exp_uuid)
        assert True
    else:
        print("No unallocated node being found, expecting node with uuid ", exp_uuid)
        assert False


def listDellNodesAPI():
    print('\nListing Dell Nodes on API')
    endpoint = '/nodes'
    my_url = gbl.my_data['dne_base_url'] + endpoint
    print('GET:', my_url)

    try:
        url_response=requests.get(my_url)
        url_response.raise_for_status()

    except requests.exceptions.HTTPError as err:
        # Return code error (e.g. 404, 501, ...)
        print(err)
        print('\n')
        assert False

    except requests.exceptions.Timeout as err:
        # Not an HTTP-specific error (e.g. connection refused)
        print(err)
        print('\n')
        assert False

    else:
        # 200
        print(url_response)
        the_response = url_response.text
        print('API Return Data:', the_response)
        return the_response


def rmqNodeDiscover():
    # Step 1: Verify the Node Discovered Event
    # Receive the node discover message

    waitForMsg('test.rackhd.node.discovered.event')
    return_message = af_support_tools.rmq_consume_message(host=ipaddress, port=port, rmq_username=rmq_username,
                                                              rmq_password=rmq_password,
                                                              queue='test.rackhd.node.discovered.event')

    print('from: dell.cpsd.adapter.rackhd.node.discovered.event')
    checkForErrors(return_message)
    checkForFailures(return_message)

    return_json = json.loads(return_message, encoding='utf-8')

    #TODO verify the message
    assert return_json['action']=='discovered'
    assert return_json['type']=='node'
    assert return_json['data']['ipMacAddresses']
    assert return_json['data']['nodeId']
    assert return_json['data']['nodeType']=='compute'

    nodeIPAddress = return_json['data']['ipMacAddresses'][0]['ipAddress']
    nodeMACAddress = return_json['data']['ipMacAddresses'][0]['macAddress']

    print('\nNew Node IP Addres', nodeIPAddress,'\nNew Node MAC Addres', nodeMACAddress)

    # Step 2: Verify the EIDS Messages sequence and get UUID for new node
    uuid = verifyEidsMessage()
    return uuid


def bindQueues():
    af_support_tools.rmq_bind_queue(host=ipaddress,
                                    port=port, rmq_username=rmq_username, rmq_password=rmq_password,
                                    queue='test.rackhd.node.discovered.event',
                                    exchange='exchange.dell.cpsd.adapter.rackhd.node.discovered.event',
                                    routing_key='#')

    af_support_tools.rmq_bind_queue(host=ipaddress, port=port, rmq_username=rmq_username, rmq_password=rmq_password,
                                    queue='test.eids.identity.request',
                                    exchange='exchange.dell.cpsd.eids.identity.request',
                                    routing_key='#')

    af_support_tools.rmq_bind_queue(host=ipaddress, port=port, rmq_username=rmq_username, rmq_password=rmq_password,
                                    queue='test.eids.identity.response',
                                    exchange='exchange.dell.cpsd.eids.identity.response',
                                    routing_key='#')

def cleanup():
    print('Cleaning up...')
    af_support_tools.rmq_delete_queue(host=ipaddress, port=port, rmq_username=rmq_username, rmq_password=rmq_password,
                                       queue='test.rackhd.node.discovered.event')

    af_support_tools.rmq_delete_queue(host=ipaddress, port=port, rmq_username=rmq_username, rmq_password=rmq_password,
                                      queue='test.eids.identity.request')

    af_support_tools.rmq_delete_queue(host=ipaddress, port=port, rmq_username=rmq_username, rmq_password=rmq_password,
                                      queue='test.eids.identity.response')


def waitForMsg(queue):
    # This function keeps looping untill a message is in the specified queue. We do need it to timeout and throw an error
    # if a message never arrives. Once a message appears in the queue the function is complete and main continues.

    # The length of the queue, it will start at 0 but as soon as we get a response it will increase
    q_len = 0

    # Represents the number of seconds that have gone by since the method started
    timeout = 0

    # Max number of seconds to wait
    max_timeout = 500

    # Amount of time in seconds that the loop is going to wait on each iteration
    sleeptime = 1

    while q_len < 1:
        time.sleep(sleeptime)
        timeout += sleeptime

        q_len = af_support_tools.rmq_message_count(host=ipaddress,
                                                   port=port,
                                                   rmq_username=rmq_username,
                                                   rmq_password=rmq_password,
                                                   queue=queue)
        if timeout > max_timeout:
            print('ERROR: Message took too long to return. Something is wrong')
            cleanup()
            break


def checkForErrors(return_message):
    checklist = 'errors'
    if checklist in return_message:
        print('\nBUG: Error in Response Message\n')
        assert False  # This assert is to fail the test


def checkForFailures(return_message):
    checklist = 'failureReasons'
    if checklist in return_message:
        return_json = json.loads(return_message, encoding='utf-8')
        errorMsg = return_json['failureReasons'][0]['message']
        print('The following error has been returned :',errorMsg)
        print('Possible component validation issue')
        assert False  # This assert is to fail the test


def verifyEidsMessage():
    # We need to verify that the triggered eids.identity.request is valid.
    # Check the EIDS request messages
    print('\nVerifying Identity Service request & response for UUID')

    waitForMsg('test.eids.identity.request')
    return_message = af_support_tools.rmq_consume_message(host=ipaddress, port=port, rmq_username=rmq_username,
                                                          rmq_password=rmq_password,
                                                          queue='test.eids.identity.request')

    return_json = json.loads(return_message, encoding='utf-8')

    assert return_json['correlationId']
    # assert return_json['replyTo']
    assert return_json['timestamp']
    assert return_json['elementIdentities'][0]['correlationUuid']
    assert return_json['elementIdentities'][0]['identity']['elementType']=='computeServer'
    assert return_json['elementIdentities'][0]['identity']['contextualKeyAccuracy']== 1

    # Check the EIDS response message
    waitForMsg('test.eids.identity.response')
    return_message = af_support_tools.rmq_consume_message(host=ipaddress, port=port, rmq_username=rmq_username,
                                                          rmq_password=rmq_password,
                                                          queue='test.eids.identity.response')

    return_json = json.loads(return_message, encoding='utf-8')

    assert return_json['correlationId']
    # assert return_json['replyTo']
    assert return_json['timestamp']
    assert return_json['elementIdentifications'][0]['correlationUuid']
    assert return_json['elementIdentifications'][0]['elementUuid']

    uuid = return_json['elementIdentifications'][0]['elementUuid']

    print('\nTest Pass: EIDS requests & response messages received for new node')
    print('New Node UUID:', uuid)

    return uuid


def rest_queue_list(user=rmq_username, password=rmq_password, host=ipaddress, port=15672, virtual_host=None, exchange=None):
    url = 'http://%s:%s/api/exchanges/%s/%s/bindings/source' % (host, port, virtual_host, exchange)
    response = requests.get(url, auth=(user, password))
    queues = [q['destination'] for q in response.json()]
    return queues


def validate_queues_on_exchange(suppliedExchange, suppliedQueue):
    queues = rest_queue_list(user=rmq_username, password=rmq_password, host=ipaddress, port=15672, virtual_host='%2f', exchange =suppliedExchange )
    queues = json.dumps(queues)

    assert suppliedQueue in queues
    #print('\n',suppliedQueue,'\nis bound to\n',suppliedExchange)


def delete_rackhd_node_entry(macAddress, rackHDHost):
    successFlag = 500
    nodeId = get_rackhd_node_entry(macAddress, rackHDHost)

    if nodeId:
        apipath = "/api/current/nodes/" + nodeId
        url = 'http://' + rackHDHost + ':8080' + apipath
        resp = requests.delete(url)
        successFlag = resp.status_code
    else:
        successFlag = 500  # error

    return successFlag


def get_rackhd_node_entry(macAddress, rackHDHost):
    testNodeId = ""
    apipath = "/api/current/nodes/"
    url = 'http://' + rackHDHost + ':8080' + apipath
    resp = requests.get(url)
    data = json.loads(resp.text)

    for nodes in data:
        if macAddress in nodes['name']:
            testNodeId = nodes['id']

    return testNodeId


def consulBypassMsg():
    # Until consul is  working properly & integrated with the rackhd adapter in the same environment we need to register
    # it manually by sending this message.
    url = 'http://' + rackhd_ip + ':8080'
    the_payload = '{"endpoint":{"type":"rackhd","instances":[{"url":url}]}}'

    af_support_tools.rmq_publish_message(host=ipaddress, rmq_username=rmq_username, rmq_password=rmq_password,
                                         exchange='exchange.dell.cpsd.endpoint.registration.event',
                                         routing_key='dell.cpsd.endpoint.discovered',
                                         headers={
                                             '__TypeId__': 'com.dell.cpsd.endpoint-registry.endpointsdiscoveredevent'},
                                         payload=the_payload)