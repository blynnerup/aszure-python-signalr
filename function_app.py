import azure.functions as func
import json
import logging
import os

app = func.FunctionApp()

# Used by client to know where to call the function
@app.route(route="negotiate", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@app.generic_input_binding(arg_name="connectionInfo", type="signalRConnectionInfo", hubName="bdotstsignal", connectionStringSetting="AzureSignalRConnectionString")
def negotiate(req: func.HttpRequest, connectionInfo) -> func.HttpResponse:
    logging.info(f"connectionInfo: {connectionInfo}")
    return func.HttpResponse(connectionInfo)

# Hosts the web page
@app.route(route="index", auth_level=func.AuthLevel.ANONYMOUS)
def index(req: func.HttpRequest) -> func.HttpResponse:
    f = open(os.path.dirname(os.path.realpath(__file__)) + '/content/index.html')
    return func.HttpResponse(f.read(), mimetype='text/html')


@app.function_name(name="modify_message")
@app.route(route="modify_message", methods=["POST"])
@app.generic_output_binding(
    arg_name="signalRMessages",
    type="signalR",
    hub_name="bdotstsignal",
    connection_string_setting="AzureSignalRConnectionString"
)
def modify_message(req: func.HttpRequest, signalRMessages: func.Out[str]) -> func.HttpResponse:
    logging.info('modify_message function received a request.')

    try:
        # Parse the JSON body
        req_body = req.get_json()
        message = req_body.get('message')

        if message is None:
            return func.HttpResponse(
                "Please pass a message in the request body",
                status_code=400
            )

        # Reverse the message
        reversed_message = message[::-1]

        # Create a SignalR message
        signalr_message = {
            'target': 'newMessage',
            'arguments': [reversed_message]
        }

        # Set the SignalR message output
        signalRMessages.set(json.dumps(signalr_message))

        return func.HttpResponse(f"Message received and broadcasted: {reversed_message}")

    except ValueError:
        return func.HttpResponse(
            "Invalid JSON body",
            status_code=400
        )

    except Exception as e:
        logging.error(f"Error processing the request: {str(e)}")
        return func.HttpResponse(
            "An error occurred processing the request",
            status_code=500
        )
