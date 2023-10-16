import base64

from cloudevents.http import CloudEvent
import functions_framework


# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def subscribe(cloud_event: CloudEvent) -> None:
    """ """
    # Print out the data from Pub/Sub, to prove that it worked
    print(
        cloud_event.data["message"]
    )

@functions_framework.cloud_event
def send_to_teams(cloud_event: CloudEvent) -> None:
    # Extract the Pub/Sub message data.
    print(event)
    pubsub_data = json.loads(name)

    # Define your Microsoft Teams webhook URL here.
    teams_webhook_url = ("Your_MS_Teams_Webhook URL")

    headers = {
        'Content-Type': "application/json",
    }

    # Extracts the values from json object
    title = pubsub_data['finding']['category']
    Severity = pubsub_data['finding']['severity']
    Resource = pubsub_data['finding']['resourceName']
    Description = pubsub_data['finding']['description']
    Project_Name = pubsub_data['resource']['projectDisplayName']
    Explanation = pubsub_data['finding']['sourceProperties']['Explanation']
    externalUri = pubsub_data['finding']['externalUri']

    message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": title,
            "sections": [{
                "activityTitle": title,
                "facts": [{
                    "name": "Resource:",
                    "value": Resource
                }, {
                    "name": "Severity:",
                    "value": Severity

                },
                    {
                        "name": "Description:",
                        "value": Description
                },
                    {
                        "name": "Project_Name:",
                        "value": Project_Name
                },
                    {
                        "name": "Explanation:",
                        "value": Explanation
                    }],
                "markdown": True
            }],
             "potentialAction": [{
                 "@type": "OpenUri",
                 "name": "Learn More",
                 "targets": [{
                     "os": "default",
                     "uri": externalUri
                 }]
             }]
        }

    # Send the message to Microsoft Teams.
    response = requests.post(teams_webhook_url, data=json.dumps(message),headers=headers)

    if response.status_code == 200:
        print("Message sent to Teams successfully.")
    else:
        print(f"Error sending message to Teams: {response.text}")