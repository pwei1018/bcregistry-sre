# BC Registry SRE Team

## OPs notebooks

To use the notebooks:
- Have VSCode installed
- Have Docker or equivalent services installed
- make sure you have [Remote Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed.

1. Open the **ops** directory in VSCode and choose to use the *devcontainer* when prompted.

1. Setup you *port-forwarding* or service forwarding.

1. Update **bcr-business-setup.ipynb** with the values to connect to the services.

1. Start the server in a VSCode Terminal using ```./run.sh```

1. Go to the notebook index, which will look like *http://127.0.0.1:8080/?token=som-long-token* listed in the terminal window

1. Select the notebook template that most closely aligns the task at hand.

The notebooks, organization of them, descriptions, etc. will be done by the SRE teams as this library is expanded upon.

**NOTE**: remember to update your python libraries from the various projects to use the latest release when working in that area.

