from flask import Flask, session, request, jsonify,make_response
from flask_session import Session
import openai
import uuid
import os
import logging
from flask_cors import CORS


app = Flask(__name__)

#Added cross origin
CORS(app)
CORS(app, supports_credentials=True)

app.secret_key = 'supersecretkey'  # replace with your own secret key
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)  # Set the desired log level for the handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

Session(app)

#api_Key=os.getenv("api_Key")
api_Key="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"
openai.api_key=api_Key

#sess={
#    'session1':{
#        'id':'123'
#    }
#}

sess={}

@app.route('/getSession', methods=['get'])
async def getSession():
    session_name = str(uuid.uuid4())
    sess[session_name] = {"session_id":"123"}
    logger.info("Session is successfully created")
    
    response=jsonify({"session_name": session_name, "session_data": sess[session_name]})
    #response.set_cookie('session', "5ff70385-f7a4-4010-9bb0-36a1a948fb8a")
    #session["sessionname"]="5ff70385-f7a4-4010-9bb0-36a1a948fb8a"

    logger.info(f"response: \n {response.json}")
    logger.info(f"Cookies: {request.cookies.get('session')}")
    return response

def wordCount(string):
    return len([w for w in string.split(' ') if w.strip()])

def getInitialPrompt(intent: str, isAgent: bool) -> str:
    templateSpecifics = ""
    if intent == "Billing Issues":
        templateSpecifics = "that is having billing issues."
    elif intent == "Military Discount":
        templateSpecifics = "having queries about military discount."
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

    templateBase = f"{ 'You are an agent in a call center. Given the response of the agent, it is your job to write a better response for agents last response in a formal way based on the scenario.' if isAgent else 'You are a customer having a call with contact center agent. You generate response for the customer based on the scenario' }.\n\n\
Scenario: Lets do a quick role play for a customer {templateSpecifics}.\n\n\
Customer:"

    return templateBase

@app.route('/customer', methods=['POST'])
async def customer():
    logger.info("Customer api is invoked successfully")
    logger.info("Headers received from endpoint \n\n")
    headers=request.headers

    logger.info(f"Headers sent to agent api : \n\n{headers}")


    data=request.json
    print(data)
    logger.info(f"Data Received as Input: {data}")
    session_name=data["session_name"]
    #sessionid=data["session_id"]
    #session_name=session.get("session_name")
    #session_name="5ff70385-f7a4-4010-9bb0-36a1a948fb8a"
    intent = data["intent"]
    #print(sess[sessionid])
    print(sess)
    if True:
    #if session_name in sess:   
        customerTemplate = getInitialPrompt(intent, False)
        agentTemplate = getInitialPrompt(intent, True)

        try:
            completion = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"{customerTemplate}\n\n",
                temperature=0.7,
                max_tokens=100,
                n = 1,
                stop=None,
                frequency_penalty=1,
                presence_penalty=1
            )

            promptResponses = f"Customer: {completion.choices[0].text}\n\n"
            session["promptResponses"] = promptResponses
            session["customerTemplate"] = customerTemplate
            session["agentTemplate"] = agentTemplate
            print(session)
            #return jsonify(session)
            logger.info("Customer Response Generated Successfully")

            return jsonify({ "customer": completion.choices[0].text})
        
            # Create a response object
            #response = jsonify({"customer": completion.choices[0].text})

            # Set the session cookie
            #response.set_cookie('session', "aee7947f-bea7-436d-bd88-7a5bb2559fa5")

            #return response

        except Exception as e:
            print(e)
            return({"status": "error", "message": "Failed to generate response."})
    else:    
        return jsonify({'status': 'error', 'message': 'Invalid session ID.'})

def scoring_Responses(prom:str) -> str:
    prompt3=f'You are a training bot designed to help the agents improve their conversation with a customer. Based on the following interaction between the customer and the agent, give me scores in stringent manner on a scale of 5 for the following topics with reason in a line. Greeting; Discovery; Solutioning.\n{prom}'

    completion3 =  openai.Completion.create(
                model="text-davinci-003",
                prompt=f"{prompt3}\n\n",
                temperature=0.7,
                max_tokens=100,
                frequency_penalty=1,
                presence_penalty=1
            )
    return(completion3.choices[0].text)



@app.route('/agent', methods=['POST'])
async def agent():
    logger.info("Agent Api Invoked successfully")
    logger.info("Headers received from endpoint")
    headers=request.headers

    logger.info(f"Headers sent to agent api : \n\n{headers}")


    data = request.json
    logger.info(f"Data Received as Input: {data}")
    chat = data["chat"]
    #session_name=data["session_name"]
    
    agentTemplate = session.get("agentTemplate")
    customerTemplate = session.get("customerTemplate")
    promptResponses = session.get("promptResponses", "")
    scoring_promptResponses = session.get("promptResponses", "")
    scoring_promptResponses+= f" Agent: {chat}\n\n"
    scores=scoring_Responses(scoring_promptResponses)

    prompt = f"{agentTemplate}\n\n{promptResponses} Agent: {chat}\n\nAI:"
    wc = wordCount(chat)

    logger.info(f"Prompt to Generate Agents' better way of responding: {prompt}")

    try:
        completion =  openai.Completion.create(
            model="text-davinci-003",
            prompt=f"{prompt}\n\n",
            temperature=0.7,
            max_tokens=100,
            frequency_penalty=1,
            presence_penalty=1
        )

        promptResponses += f" Agent: {completion.choices[0].text}\n\n"

        prompt2 = f"{customerTemplate}\n\n{promptResponses} Customer:"

        logger.info(f"Prompt to Generate Customer Response: {prompt2}")

        completion2 =  openai.Completion.create(
            model="text-davinci-003",
            prompt=f"{prompt2}\n\n",
            temperature=0.7,
            max_tokens=100,
            frequency_penalty=1,
            presence_penalty=1
        )

        promptResponses += f" Customer: {completion2.choices[0].text}\n\n"

        session["promptResponses"] = promptResponses

        logger.info(f"Response from API: coach: {completion.choices[0].text}, customer: {completion2.choices[0].text}")

        logger.info("Agent Response generated successfully")

        #return jsonify(session)

        #return jsonify({"coach": completion.choices[0].text,"customer": completion2.choices[0].text}).set_cookie('session',session_name)
        response=jsonify({"coach": completion.choices[0].text,"customer": completion2.choices[0].text,"scoring":scores})
        
        return(response)

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Failed to generate response."})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000,debug=True)