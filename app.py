from flask import Flask, session, request, jsonify
from flask_session import Session
import openai
import uuid
import os


app = Flask(__name__)
app.secret_key = 'supersecretkey'  # replace with your own secret key
app.config['SESSION_TYPE'] = 'filesystem'

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
    sess[session_name] = {"session_id":"123"}
    return jsonify({"session_name": session_name, "session_data": sess[session_name]})



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
    data=request.json
    print(data)
    session_name=data["session_name"]
    sessionid=data["session_id"]
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
            session["promptResponses"] = promptResponses
            session["customerTemplate"] = customerTemplate
            session["agentTemplate"] = agentTemplate
            print(session)
            #return jsonify(session)
            return jsonify({ "customer": completion.choices[0].text})
        
        except Exception as e:
            print(e)
            return({"status": "error", "message": "Failed to generate response."})
    else:    
        return jsonify({'status': 'error', 'message': 'Invalid session ID.'})
    

@app.route('/agent', methods=['POST'])
async def agent():
    data = request.json
    chat = data["chat"]
    agentTemplate = session.get("agentTemplate")
    customerTemplate = session.get("customerTemplate")
    promptResponses = session.get("promptResponses", "")

    prompt = f"{agentTemplate}\n\n{promptResponses} Agent: {chat}\n\nAI:"
    wc = wordCount(chat)

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

        #return jsonify(session)

        return jsonify({"coach": completion.choices[0].text,"customer": completion2.choices[0].text})

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Failed to generate response."})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000,debug=True)