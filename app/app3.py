from flask import Flask, session, request, jsonify
from flask_session import Session
import openai
import uuid
import os
import logging
from redis import Redis


app = Flask(__name__)
app.secret_key = 'supersecretkey'  # replace with your own secret key
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis(host='127.0.0.1', port=6379, password='')
redis_client = Redis(host='127.0.0.1', port=6379, password='')



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


@app.route('/getSession', methods=['get'])
async def getSession():
    session_name = str(uuid.uuid4())
    logger.info("Session is successfully created")
    redis_key = f"session:{session_name}"
    logger.info("Redis key is created")
    redis_client.hmset(redis_key,{'Session Name':f'{session_name}','promptResponse':'','agentTemplate':'','customerTemplate':'','scoringPrompt':''})
    logger.info("Session Stored in Redis")
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

    templateBase = f"{ 'You are an agent in a call center. Given the response of the agent, it is your job to write a better response for agents last response in a formal way based on the scenario.' if isAgent else 'You are a customer having a call with contact center agent. You generate response for the customer based on the scenario' }.\n\n\
Scenario: Lets do a quick role play for a customer {templateSpecifics}\n\n\
Customer:"

    return templateBase

@app.route('/customer', methods=['POST'])
async def customer():
    logger.info("Customer api is invoked successfully")
    data=request.json
    logger.info(f"Data Received as Input: {data}")
    session_name=data["session_name"]
    intent = data["intent"]
    #Redis Key
    redis_key = f"session:{session_name}"
    logger.info("Checking if the session is available")
    if redis_client.exists(redis_key):
        #pulling all data from Redis
        logger.info("Session is available\n\n")
        logger.info("Pulling data of the session")
        session_data = redis_client.hgetall(redis_key)

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
            
            logger.info("Updating Session Data:")
            redis_client.hset(redis_key, "promptResponse", promptResponses)
            redis_client.hset(redis_key, "customerTemplate", customerTemplate)
            redis_client.hset(redis_key,"agentTemplate",agentTemplate)
            
            logger.info(f'Data in Redis After Update: {redis_client.hgetall(redis_key)}')
            logger.info("Customer Response Generated Successfully")
            return jsonify({ "customer": completion.choices[0].text})
        
        except Exception as e:
            print(e)
            return({"status": "error", "message": "Failed to generate response."})
    else:    
        return jsonify({'status': 'error', 'message': 'Invalid session ID.'})


def scoring_Responses(prom:str) -> str:
    prompt3=f'You are a training bot designed to help the agents improve their conversation with a customer. Based on the following interaction between the customer and the agent, give me scores on a scale of 8 for the following topics with reason. Greeting; Discovery; Solutioning.\n{prom}'

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
    data = request.json
    logger.info(f"Data Received as Input: {data}")
    chat = data["chat"]
    session_name=data["session_name"]
    #Redis Key
    redis_key = f"session:{session_name}"
    logger.info("Checking if the session is available")
    if redis_client.exists(redis_key):
        logger.info(f"Redis Session is available\n\n")
        #pulling data from Redis
        session_data = redis_client.hgetall(redis_key)
        promptResponse = session_data.get(b'promptResponse').decode('utf-8')
        logger.info(f"promptResponses Retrieved from Redis: \n{promptResponse}")
        agentTemplate= session_data.get(b'agentTemplate').decode('utf-8')
        logger.info(f"agentTemplate Retrieved from Redis: \n{agentTemplate}")
        customerTemplate= session_data.get(b"customerTemplate").decode('utf-8')
        logger.info(f"customerTemplate Retrieved from Redis: \n{customerTemplate}")
        scoringResponse=session_data.get(b"scoringPrompt").decode('utf-8')
        logger.info(f"Scoring prompt Retrieved from Redis: {scoringResponse}")
        scoringResponse+= f" Agent: {chat}\n\n"
        scores=scoring_Responses(scoringResponse)

        logger.info("Generating prompt for better Response")
        prompt = f"{agentTemplate}\n\n{promptResponse} Agent: {chat}\n\nAI:"
                
        wc = wordCount(chat)

        logger.info(f"Prompt to Generate agents' better way of responding: {prompt}")

        try:
            completion =  openai.Completion.create(
                model="text-davinci-003",
                prompt=f"{prompt}\n\n",
                temperature=0.7,
                max_tokens=100,
                frequency_penalty=1,
                presence_penalty=1
            )

            promptResponse += f" Agent: {completion.choices[0].text}\n\n"

            prompt2 = f"{customerTemplate}\n\n{promptResponse} Customer:"

            logger.info(f"Prompt to Generate Customer Response: {prompt2}")

            completion2 =  openai.Completion.create(
                model="text-davinci-003",
                prompt=f"{prompt2}\n\n",
                temperature=0.7,
                max_tokens=100,
                frequency_penalty=1,
                presence_penalty=1
            )

            promptResponse += f" Customer: {completion2.choices[0].text}\n\n"
            scoringResponse += f" Customer: {completion2.choices[0].text}\n\n"

            logger.info("Updating Redis")
            #Updating data in Redis
            redis_client.hset(redis_key, "promptResponse", promptResponse)
            redis_client.hset(redis_key, "scoringPrompt", scoringResponse)
            
            logger.info("Redis Session Updated")

            return jsonify({"coach": completion.choices[0].text,"customer": completion2.choices[0].text, "score": scores})

        except Exception as e:
            print(e)
            return jsonify({"status": "error", "message": "Failed to generate response."})






if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000,debug=True)