import azure.functions as func
import json
import logging
import os

app = func.FunctionApp()

# Used by client to know where to call the function
@app.route(route="negotiate", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@app.generic_input_binding(arg_name="connectionInfo", type="signalRConnectionInfo", hubName="bdotstsignal", connectionStringSetting="AzureSignalRConnectionString", direction="in")
def negotiate(req: func.HttpRequest, connectionInfo) -> func.HttpResponse:
    logging.info(f"connectionInfo: {connectionInfo}")
    return func.HttpResponse(connectionInfo)

# Hosts the web page
@app.route(route="index", auth_level=func.AuthLevel.ANONYMOUS)
def index(req: func.HttpRequest) -> func.HttpResponse:
    f = open(os.path.dirname(os.path.realpath(__file__)) + '/content/index.html')
    return func.HttpResponse(f.read(), mimetype='text/html')

# Triggers when a request is sent to the endpoint, prints 'arguments'
@app.generic_trigger(arg_name="myTrigger", type="httpTrigger")
@app.generic_output_binding(arg_name="signalRMessages", type="signalR", hubName="bdotstsignal", connectionStringSetting="AzureSignalRConnectionString")
def broadcast(myTrigger: func.HttpRequest, signalRMessages: func.Out[str]) -> None:
    logging.info("Broadcast started")

    signalRMessages.set(json.dumps({
        'target': 'newMessage',
        'arguments': ['This is sent back']
    }))