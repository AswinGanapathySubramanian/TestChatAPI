from flask import Flask, session, request, jsonify
from flask_session import Session
import openai
import uuid
import os
import logging


app = Flask(__name__)
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

api_Key=os.getenv("api_Key")
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
    logger.info("Session is successfully created")
    session[session_name] = {"session_data": {"promptResponses":"","customerTemplate":"","agentTemplate":""}}
    logging.info(f"Created Session: \n {session}")
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

    templateBase = f"{ 'You are an agent in a call center. Given the response of the agent, it is your job to write a better response' if isAgent else 'You are a customer having a call with contact center agent. You generate response for the customer based on the scenario' }.\n\n\
Scenario: Lets do a quick role play for a customer {templateSpecifics}\n\n\
Customer:"

    return templateBase

@app.route('/customer', methods=['POST'])
async def customer():
    logger.info("Customer api is invoked successfully")
    #logger.info("Headers received from endpoint \n\n")
    #headers=request.headers

    #logger.info(f"Headers sent to agent api : \n\n{headers}")

    data=request.json
    logger.info(f"Data Received as Input: {data}")
    #print(data)
    session_name=data["session_name"]
    #sessionid=data["session_id"]
    intent = data["intent"]
    #print(sess[sessionid])
    #print(sess)
    #if True:
    logger.info("Checking the session generateed in the sessions available")
    if session_name in session:
        logger.info("Session is present")
        session_data=session[session_name] 
        logger.info(f"Retrieved Session data: {session_data}") 
        customerTemplate = getInitialPrompt(intent, False)
        agentTemplate = getInitialPrompt(intent, True)

        try:
            completion = openai.Completion.create(
                engine="text-davinci-002",
                prompt=f"{customerTemplate}\n\n",
                temperature=0.7,
                max_tokens=100,
                n = 1,
                stop=None,
                frequency_penalty=1,
                presence_penalty=1
            )

            promptResponses = f"Customer: {completion.choices[0].text}\n\n"
            session_data["promptResponses"] = promptResponses
            session_data["customerTemplate"] = customerTemplate
            session_data["agentTemplate"] = agentTemplate
            #print(session_data)
            session[session_name]=session_data
            session.modified = True
            #return jsonify(session)

            logger.info(f"Updated Session Data: \n{session[session_name]}")
            logger.info("Customer Response Generated Successfully")

            #logger.info(f"Prompt Response in Session Data: {session_data['promptResponses']}")
            #logger.info(f"Customer Template in Session Data: {session_data['customerTemplate']}")
            #logger.info(f"Agent Template in Session Data: {session_data['agentTemplate']}")

            return jsonify({ "customer": completion.choices[0].text})
        
        except Exception as e:
            print(e)
            return({"status": "error", "message": "Failed to generate response."})
    else:    
        return jsonify({'status': 'error', 'message': 'Invalid session ID.'})
    

@app.route('/agent', methods=['POST'])
async def agent():
    logger.info("Agent Api Invoked successfully")
    logger.info("Headers received from endpoint")
    headers=request.headers
    logger.info(f"Headers sent to agent api : \n\n{headers}")
    data = request.json
    logger.info(f"Data Received as Input: {data}")
    chat = data["chat"]
    session_name=data["session_name"]
    if session_name in session:
        session_data=session[session_name]
        #logger.info(f"Data Retrieved using sessions: \n{session_data}")
        agentTemplate = session_data.get("agentTemplate")
        customerTemplate = session_data.get("customerTemplate")
        promptResponses = session_data.get("promptResponses", "")

        logger.info(f"agentTemplate Retrieved using sessions: \n{agentTemplate}")

        logger.info(f"customerTemplate Retrieved using sessions: \n{customerTemplate}")

        logger.info(f"promptResponses Retrieved using sessions: \n{promptResponses}")

        prompt = f"{agentTemplate}\n\n{promptResponses} Agent: {chat}\n\nAI:"
        wc = wordCount(chat)

        #logger.info(f"Prompt to Generate agents' better way of responding: {prompt}")

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

            #logger.info(f"Prompt to Generate Customer Response: {prompt2}")

            completion2 =  openai.Completion.create(
                model="text-davinci-003",
                prompt=f"{prompt2}\n\n",
                temperature=0.7,
                max_tokens=100,
                frequency_penalty=1,
                presence_penalty=1
            )

            promptResponses += f" Customer: {completion2.choices[0].text}\n\n"

            session_data["promptResponses"] = promptResponses
            session[session_name]=session_data
            session.modified = True

            #return jsonify(session)
            logger.info(f"Prompt Response in Session Data: {session_data['promptResponses']}")
            logger.info(f"Customer Template in Session Data: {session_data['customerTemplate']}")
            logger.info(f"Agent Template in Session Data: {session_data['agentTemplate']}")

            return jsonify({"coach": completion.choices[0].text,"customer": completion2.choices[0].text})

        except Exception as e:
            print(e)
            return jsonify({"status": "error", "message": "Failed to generate response."})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000,debug=True)