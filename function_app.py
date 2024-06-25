import azure.functions as func
import os
import json 
import logging
import time
import requests
import uuid
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

app = func.FunctionApp()

StatusFuncUrl = os.environ["StatusFuncUrl"]

@app.function_name(name="index")
@app.route(route="index", auth_level=func.AuthLevel.ANONYMOUS)
def index(req: func.HttpRequest) -> func.HttpResponse:
    f = open(os.path.dirname(os.path.realpath(__file__)) + '/content/index.html')
    return func.HttpResponse(f.read(), mimetype='text/html')

@app.function_name(name="negotiate")
@app.route(route="negotiate", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@app.generic_input_binding(
    arg_name="connectionInfo", 
    type="signalRConnectionInfo", 
    hubName="bdotstsignal", 
    connectionStringSetting="AzureSignalRConnectionString")
def negotiate(req: func.HttpRequest, connectionInfo) -> func.HttpResponse:
    logging.info(f"connectionInfo: {connectionInfo}")
    return func.HttpResponse(connectionInfo)

@app.function_name(name="send-status")
@app.route(route="send-status", auth_level=func.AuthLevel.ANONYMOUS)
@app.generic_output_binding(
    arg_name="signalRMessages", 
    type="signalR", 
    hubName="bdotstsignal", 
    connectionStringSetting="AzureSignalRConnectionString")
def send_status(req: func.HttpRequest, signalRMessages: func.Out[str]) -> str:
    """
    Sends status to SignalR
    """
    logging.info("Starting send_status")
    req_body = req.get_json()
    status = req_body.get('status')
    signalRMessages.set(json.dumps({
        'target': 'newMessage',
        'arguments': ['Status: ' + status]
    }))
    return "ok"

@app.function_name(name="mock-query")
@app.route(route="mock-query", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@app.generic_output_binding(
    arg_name="signalRMessages", 
    type="signalR", hubName="bdotstsignal", 
    connectionStringSetting="AzureSignalRConnectionString")
def mock_query(req: func.HttpRequest, signalRMessages: func.Out[str]) -> str:
    logging.info("Starting mock")
    req_body = req.get_json()
    waitTime1 = int(req_body.get('wait1'))
    waitTime2 = int(req_body.get('wait2'))
    json_data = json.dumps({
        'target': 'status1',
        'status': 'Query started'
    })

    funcUrl = StatusFuncUrl
    response = requests.post(url=funcUrl, data=json_data)
    logging.info(response)
    logging.info(f"waiting for {waitTime1}")
    time.sleep(waitTime1)

    json_data = json.dumps({
        'target': 'status2',
        'status': 'Getting sources'
    })
    response = requests.post(url=funcUrl, data=json_data)
    logging.info(f"waiting for {waitTime2}")
    time.sleep(waitTime2)

    signalRMessages.set(json.dumps({
        'target': 'newMessage',
        'arguments': ['Query complete']
    }))
    return "Query complete"

@app.function_name(name="send-to-user")
@app.route(route="send-to-user", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@app.generic_output_binding(
    arg_name="signalRMessages",
    type="signalR", 
    hubName="bdotstsignal", 
    connectionStringSetting="AzureSignalRConnectionString")
def main(req: func.HttpRequest, signalRMessages: func.Out[str]) -> func.HttpResponse:
    body_json = req.get_json()
    userId = body_json.get('userId')
    message = f"Hello userId {userId}, this is for you only."
    signalRMessages.set(json.dumps({
        #message will only be sent to this user ID
        'userId': userId,
        'target': 'newMessage',
        'arguments': [ message ]
    }))

@app.function_name(name="post-query")
@app.route(route="post-query", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@app.cosmos_db_output(
    arg_name="outputDocument",
    database_name="QueriesDb",
    container_name="NewQueries",
    connection="CosmosDbConnectionSetting")
def posts_query(req: func.HttpRequest, outputDocument: func.Out[func.Document]) -> func.HttpResponse:
    logging.info('Python HTTP trigger function "send-query" processed a request.')
    
    req_body = req.get_json()
    userId = req_body.get('userId')
    query = req_body.get('query')
    password = req_body.get('password')
    docId = uuid.uuid4()
    str_doc_id = docId.hex

    json_data = json.dumps({
        'status': f'Creating document; UserId: {userId} - Query: {query}'
    })

    response = requests.post(url=StatusFuncUrl, data=json_data)
    logging.info(response)

    outputDocument.set(func.Document.from_dict({"id": str_doc_id, "userId": userId, "query": query}))

    #Query AI
    searchUrl = os.environ["SearchUrl"]
    key = os.environ["SearchKey"]
    credential = AzureKeyCredential(key)
    index_name = "documents-index"

    search_client = SearchClient(searchUrl, index_name, credential=credential)
    results = search_client.search(search_text=query, top=1)

    for result in results:
        encoded_path = result['metadata_storage_path'] # Id of document within data lake
        logging.info(f"Content: {result['content']}")
        json_content_data = json.dumps({
            'status': result['content']
        })
        _ = requests.post(url=StatusFuncUrl, data=json_content_data)

    return func.HttpResponse(
        "Query sent"
    )