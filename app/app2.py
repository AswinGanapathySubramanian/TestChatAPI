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
    #data={"promptResponses":"","customerTemplate":"","agentTemplate":""}
    #session[session_name] = {"session_data": {"promptResponses":"","customerTemplate":"","agentTemplate":""}}
    #logging.info(f"Created Session: \n {session[session_name]}")
    redis_key = f"session:{session_name}"
    di={'promptResponse':'Session Created','agentTemplate':'','customerTemplate':''}
    redis_client.hmset(redis_key,di)
    return jsonify({"session_name": session_name})

@app.route('/retrievingData', methods=['POST'])
async def retrievingData():
    logger.info("retrievingData  api is invoked successfully")
    data=request.json
    logger.info(f"Data Received as input: {data}")
    session_name=data["session_name"]
    redis_key=f"session:{session_name}"
    logger.info(f"Redis Key: {redis_key}")
    
    #t=y.get("promptResponse")
    #Updating data in Redis
    redis_client.hset(redis_key, "promptResponse", "I have updated the prompt response after creating session")
    #Getting all data from Redis
    session_data = redis_client.hgetall(redis_key)
    prompt_response = session_data.get(b'promptResponse').decode('utf-8')
    logger.info(f"Data Retrieved from redis: \n {prompt_response}")
    return (str(prompt_response))

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000,debug=True)