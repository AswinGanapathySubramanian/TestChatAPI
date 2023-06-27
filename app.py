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

sess={"5ff70385-f7a4-4010-9bb0-36a1a948fb8a":{'id':'123'}}

@app.route('/getSession', methods=['get'])
async def getSession():
    session_name = str(uuid.uuid4())
    session_name=request.cookies.get('session')
    sess[session_name] = {"session_id":"123"}
    logger.info("Session is successfully created")
<<<<<<< HEAD
    #return jsonify({"session_name": session_name, "session_data": sess[session_name]})
    
    response=jsonify({"session_name": session_name, "session_data": sess[session_name]})
    #response.set_cookie('session', "5ff70385-f7a4-4010-9bb0-36a1a948fb8a")
    #session["sessionname"]="5ff70385-f7a4-4010-9bb0-36a1a948fb8a"

    logger.info(f"response: \n {response.json}")
    logger.info(f"Cookies: {request.cookies.get('session')}")
    return response
=======
    return jsonify({"session_name": session_name, "session_data": sess[session_name]})


>>>>>>> parent of 39b9afc (Added CORS)

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
    #session_name=data["session_name"]
    sessionid=data["session_id"]
    #session_name=session.get("session_name")
    session_name="5ff70385-f7a4-4010-9bb0-36a1a948fb8a"
    intent = data["intent"]
    #print(sess[sessionid])
    #print(sess)
    #if True:
    if session_name in sess:   
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
            session["promptResponses"] = {session_name:promptResponses}
            session["customerTemplate"] = {session_name:customerTemplate}
            session["agentTemplate"] = {session_name:agentTemplate}
            ag=agentTemplate
            cust=customerTemplate
            pro=promptResponses
            print(session)
            #return jsonify(session)
            logger.info("Customer Response Generated Successfully")

            return jsonify({ "customer": completion.choices[0].text})
        
<<<<<<< HEAD
            # Create a response object
            response = jsonify({"customer": completion.choices[0].text})

            # Set the session cookie
            response.set_cookie('session', "aee7947f-bea7-436d-bd88-7a5bb2559fa5")

            return response

=======
>>>>>>> parent of 39b9afc (Added CORS)
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
<<<<<<< HEAD
    #session_name=data["session_name"]
    
    #agentTemplate = session.get("agentTemplate")["5ff70385-f7a4-4010-9bb0-36a1a948fb8a"]
    #customerTemplate = session.get("customerTemplate")["5ff70385-f7a4-4010-9bb0-36a1a948fb8a"]
    #promptResponses = session.get("promptResponses", "")["5ff70385-f7a4-4010-9bb0-36a1a948fb8a"]
    agentTemplate=ag
    customerTemplate=cust
    promptResponses=pro
=======
    agentTemplate = session.get("agentTemplate")
    customerTemplate = session.get("customerTemplate")
    promptResponses = session.get("promptResponses", "")
>>>>>>> parent of 39b9afc (Added CORS)

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

        session["promptResponses"] = {"5ff70385-f7a4-4010-9bb0-36a1a948fb8a":promptResponses}

        logger.info(f"Response from API: coach: {completion.choices[0].text}, customer: {completion2.choices[0].text}")

        logger.info("Agent Response generated successfully")

        #return jsonify(session)

<<<<<<< HEAD
        #return jsonify({"coach": completion.choices[0].text,"customer": completion2.choices[0].text}).set_cookie('session',session_name)
        response=jsonify({"coach": completion.choices[0].text,"customer": completion2.choices[0].text})
        response.set_cookie("session","aee7947f-bea7-436d-bd88-7a5bb2559fa5")
        return(response)
=======
        return jsonify({"coach": completion.choices[0].text,"customer": completion2.choices[0].text})
>>>>>>> parent of 39b9afc (Added CORS)

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Failed to generate response."})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000,debug=True)