import azure.functions as func
import os
import json 
import logging
import time
import requests

app = func.FunctionApp()

@app.route(route="index", auth_level=func.AuthLevel.ANONYMOUS)
def index(req: func.HttpRequest) -> func.HttpResponse:
    f = open(os.path.dirname(os.path.realpath(__file__)) + '/content/index.html')
    return func.HttpResponse(f.read(), mimetype='text/html')

@app.route(route="negotiate", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@app.generic_input_binding(arg_name="connectionInfo", type="signalRConnectionInfo", hubName="bdotstsignal", connectionStringSetting="AzureSignalRConnectionString")
def negotiate(req: func.HttpRequest, connectionInfo) -> func.HttpResponse:
    logging.info(f"connectionInfo: {connectionInfo}")
    return func.HttpResponse(connectionInfo)

@app.function_name(name="send_status")
@app.route(route="send_status", auth_level=func.AuthLevel.ANONYMOUS)
@app.generic_output_binding(arg_name="signalRMessages", type="signalR", hubName="bdotstsignal", connectionStringSetting="AzureSignalRConnectionString")
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

@app.function_name(name="mock_query")
@app.route(route="mock_query", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@app.generic_output_binding(arg_name="signalRMessages", type="signalR", hubName="bdotstsignal", connectionStringSetting="AzureSignalRConnectionString")
def mock_query(req: func.HttpRequest, signalRMessages: func.Out[str]) -> str:
    # req_body = req.get_json()
    # user = req_body.get('user')
    # user = req.params.get("user")
    logging.info("Starting mock")
    req_body = req.get_json()
    waitTime1 = int(req_body.get('wait1'))
    waitTime2 = int(req_body.get('wait2'))
    json_data = json.dumps({
        'target': 'status1',
        'status': 'Query started'
    })
    # funcUrl = "http://localhost:7071/api/send_status
    # funcUrl = "https://bdo-blp-functst2.azurewebsites.net/api/send_status"
    response = requests.post(url=funcUrl, data=json_data)
    logging.info(response)
    logging.info(f"waiting for {waitTime1}")
    time.sleep(waitTime1)

    json_data = json.dumps({
        'target': 'status2',
        'status': 'Getting sources'
    })
    # funcUrl = "http://localhost:7071/api/send_status"
    # funcUrl = "https://bdo-blp-functst2.azurewebsites.net/api/send_status"
    response = requests.post(url=funcUrl, data=json_data)
    logging.info(f"waiting for {waitTime2}")
    time.sleep(waitTime2)

    signalRMessages.set(json.dumps({
        'target': 'newMessage',
        'arguments': ['Query complete']
    }))
    return "Query complete"

@app.function_name(name="send_to_user")
@app.route(route="send_to_user", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@app.generic_output_binding(arg_name="signalRMessages", type="signalR", hubName="bdotstsignal", connectionStringSetting="AzureSignalRConnectionString")
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
