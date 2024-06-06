# aszure-python-signalr
A selfhosted client which uses Azure Function endpoints to get requests form the client and then uses a SignalR service to send replies back.

## Setup
The following setup is done using the terminal in VS Code.

The solution uses a SignalR service in Azure, so set that up in the portal. It can run on the free tier. The important setting is that Service Mode is set to `Serverless`. This is required in order to have the Azure Function use it. Once created add the connectionString for the SignalR service to the local.settings.json file by using this command in the terminal `func settings add AzureSignalRConnectionString "<signalr-connection-string>"`

The solution should run in a vitual environment, VS Code set that up once it detects the python function app.

In order to make the Azure Function run locally we use [Azurite](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite?tabs=visual-studio%2Cblob-storage). Install that and then from the command line (Ctrl+Shift+P) run `Azurtie: Start`.

Once the setup is complete the solution is ready to run.

## Function endpoints.
The app has three functions endpoints `index`, `negotiate` and `modify_message`.
1. Run the `index` function first, this will serve the web client
2. Run the `negotiate` function second, this will initialize a connection between SignalR and the web client.
3. Finally call the `modify_message` endpoint. This can be done using a program like Postman to make a POST call to the endpoint. The function expoects a json object with a `message`. See example below

```
{
    "message": "Hello, world!"
}
```

If all works correctly you should now see `Message received and broadcasted: !dlrow ,olleH` in Postman and the webpage will have a div with the reversed `message` text inside.
