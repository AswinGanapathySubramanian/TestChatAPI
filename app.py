from flask import Flask, session, request, jsonify
from flask_session import Session
import openai
import uuid
import os
import logging

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # replace with your own secret key
app.config['SESSION_TYPE'] = 'filesystem'  # Use file system for session storage
Session(app)

api_Key=os.getenv("api_Key")
openai.api_key = api_Key
#openai.api_base = "https://amplifai-openai.openai.azure.com/" # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
#openai.api_type = 'azure'
#openai.api_version = '2023-05-15' # this may change in the future

#deployment_name='AmplifAI-Chat' #This will correspond to the custom name you chose for your deployment when you deployed a model. 
#deployment_name1="AmplifAI-Customer"
#deployment_name2=""

# Initialize the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)  # Set the desired log level for the handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)



@app.route('/getSession', methods=['GET'])
def getSession():
    header=request.headers
    session_name = str(uuid.uuid4())
    logger.info("Session is successfully created")
    logger.info(session_name)
    session[session_name] = {
        "promptResponses": "X",
        "customerTemplate": "Y",
        "agentTemplate": "",
        "scoringPrompt": ""
    }
    logger.info(session[session_name])
    logger.info(f"Created Session: \n {session[session_name]}")
    logger.info(f"session_name: {session_name}")
    return jsonify({"session_name": session_name})


def wordCount(string):
    return len([w for w in string.split(' ') if w.strip()])


def getInitialPrompt(intent: str, isAgent: bool) -> str:
    templateSpecifics = ""
    if intent == "Billing Issues":
        templateSpecifics = "that is having billing issues."
    elif intent == "Military Discount":
        templateSpecifics = "that is queries about military discount."
    elif intent == "Order Status":
        templateSpecifics = "having issue with his order."
    elif intent == "Product Availability":
        templateSpecifics = "enquiring about availability of the product."
    elif intent == "Refund Questions":
        templateSpecifics = "who has enquiries about refund."
    elif intent == "Shipping or Pickup":
        templateSpecifics = "enquiring details about shipping or pickup."
    elif intent == "Issues with Order":
        templateSpecifics = "enquiring the status of their order."

    templateBase = f"{ 'You are an agent in a call center. Given the response of the agent, it is your job to write a better response for agents last response in a formal way based on the scenario.' if isAgent else 'You are a customer having a call with contact center agent. You generate response for the customer based on the scenario.' }\n\n\
Scenario: Lets do a quick role play for a customer {templateSpecifics}\n\n\
Customer:"

    return templateBase


@app.route('/customer', methods=['POST'])
def customer():
    logger.info("Customer API is invoked successfully")
    data = request.json
    logger.info(f"Data Received as Input: {data}")
    session_name = data["session_name"]
    #logger.info(f"Created Session: \n {session[session_name]}")
    intent = data["intent"]
    logger.info(session)
    #logger.info(f"session details: {session}")
    #logger.info(f"session data present: {session[session_name]}")
    if session_name not in session:
        return jsonify({'status': 'error', 'message': 'Invalid session ID.'})

    customerTemplate = getInitialPrompt(intent, False)
    agentTemplate = getInitialPrompt(intent, True)
    logger.info(f"Customer Template created:\n {customerTemplate}")
    logger.info(f"Agent Template created:\n {agentTemplate}")

    try:
        completion = openai.Completion.create(
            model='text-davinci-003',
            prompt=f"{customerTemplate}\n\n",
            temperature=0.7,
            max_tokens=100,
            n=1,
            stop=None,
            frequency_penalty=1,
            presence_penalty=1
        )

        logger.info("Creating the prompt response:")

        promptResponses = f"Customer: {completion.choices[0].text}\n\n"
        logger.info(f"Prompt Response Generated: {promptResponses}")
        session[session_name]["promptResponses"] = promptResponses
        session[session_name]["customerTemplate"] = customerTemplate
        session[session_name]["agentTemplate"] = agentTemplate

        logger.info(f'Data in Session After Update: {session[session_name]}')
        logger.info("Customer Response Generated Successfully")
        return jsonify({"customer": completion.choices[0].text})

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Failed to generate response."})


def scoring_Responses(prom: str) -> str:
    prompt3 = f'You are a training bot designed to help the agents improve their conversation with a customer. Based on the following interaction between the customer and the agent, give me scores on a scale of 8 for the following topics with reason. Greeting; Discovery; Solutioning.\n{prom}'

    completion3 = openai.Completion.create(
        model='text-davinci-003',
        prompt=f"{prompt3}\n\n",
        temperature=0.7,
        max_tokens=100,
        frequency_penalty=1,
        presence_penalty=1
    )
    return completion3.choices[0].text


@app.route('/agent', methods=['POST'])
def agent():
    logger.info("Agent API Invoked successfully")
    data = request.json
    logger.info(f"Data Received as Input: {data}")
    chat = data["chat"]
    session_name = data["session_name"]

    if session_name not in session:
        return jsonify({'status': 'error', 'message': 'Invalid session ID.'})

    promptResponse = session[session_name]["promptResponses"]
    agentTemplate = session[session_name]["agentTemplate"]
    customerTemplate = session[session_name]["customerTemplate"]
    scoringResponse = session[session_name]["scoringPrompt"]

    scoringResponse += f" Agent: {chat}\n\n"
    scores = scoring_Responses(scoringResponse)

    wc = wordCount(chat)

    prompt = f"{agentTemplate}\n\n{promptResponse} Agent: {chat}\n\nAI:"

    logger.info(f"Prompt to Generate agents' better way of responding: {prompt}")

    try:
        completion = openai.Completion.create(
            model='text-davinci-003',
            prompt=f"{prompt}\n\n",
            temperature=0.7,
            max_tokens=100,
            frequency_penalty=1,
            presence_penalty=1
        )

        promptResponse += f" Agent: {completion.choices[0].text}\n\n"

        ##Generating response for a customer

        prompt2 = f"{customerTemplate}\n\n{promptResponse} Customer:"

        logger.info(f"Prompt to Generate Customer Response: {prompt2}")

        completion2 = openai.Completion.create(
            model='text-davinci-003',
            prompt=f"{prompt2}\n\n",
            temperature=0.7,
            max_tokens=100,
            frequency_penalty=1,
            presence_penalty=1
        )

        promptResponse += f" Customer: {completion2.choices[0].text}\n\n"
        scoringResponse += f" Customer: {completion2.choices[0].text}\n\n"

        session[session_name]["promptResponses"] = promptResponse
        session[session_name]["scoringPrompt"] = scoringResponse

        logger.info("Session Updated")

        return jsonify({
            "coach": completion.choices[0].text,
            "customer": completion2.choices[0].text,
            "score": scores
        })

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Failed to generate response."})


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000,debug=True)
