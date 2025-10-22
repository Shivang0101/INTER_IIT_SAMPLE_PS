#Importing All Required Libraries
from langgraph.graph import StateGraph,START,END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage,HumanMessage,SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3
import json
import os

#Load environment variables(Google API Key)
load_dotenv()

#Initialize Google Gemini LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

#JSON File Path to store user details
USER_DETAILS="user_details1.json"

#Function to user details
def load_user_details():
    if os.path.exists(USER_DETAILS):
        with open(USER_DETAILS,'r' ) as f:
            return json.load(f)
    return {}
        
#Function to save user details
def save_user_details(details):
    with open(USER_DETAILS,'w') as f:
        json.dump(details,f,indent=2)

#Function to extract user details ,current issue and urgency from user input
def extract_user_details(user_input,current_details):

#Creating Prompt for data extraction
    prompt=f""" You are a data extraction assistant for a financial customer support system.
    Your task is to extract relevant user details from the following user input:
    User Input: {user_input}
    Current stored user details:
    {json.dumps(current_details,indent=2)}

    your tasks:
    1. Extract ANY relevant user information from the message. Common fields include:
       - name, email, phone, address, age, occupation
       - account_number, credit_score, income, loan_amount
       - company, account_type, transaction_id
       - Any other relevant financial/personal details

    2. For "current_issue", classify the PRIMARY financial issue/topic into ONE category:
       - loan_query (personal loans, home loans, car loans, loan eligibility)
       - credit_card (credit card applications, limits, issues, rewards)
       - account_services (account opening, closing, balance, statements)
       - transaction_issue (payment problems, failed transactions, refunds)
       - investment_query (investment advice, mutual funds, stocks)  
       - insurance (insurance products, claims, policies)
       - complaint (service complaints, grievances)
       - general_inquiry (general questions, greetings, information)
       - other (anything else)

    3. For "urgency", assess the urgency level and escalation need based on the query:
       - critical (REQUIRES HUMAN AGENT): Fraud alerts, unauthorized transactions, account hacking, identity theft, 
         money lost/stolen, account locked with urgent need, legal/compliance issues, severe service failures, 
         explicit request to speak with human agent, death/emergency financial needs, threats/abusive complaints

         - high: Important issues needing quick resolution but not critical, e.g., payment failures affecting livelihood, service outages,
           significant account discrepancies, urgent account access issues, service disruptions affecting finances, complex queries needing faster response.

         - medium: Standard issues that should be addressed in a timely manner, e.g., general account inquiries, routine transactions, 
              non-urgent service requests, informational queries,non urgent complaints,loan credit card inquiries.

         - low : general information requests ,FAQs, greetings, non urgent queries,product inquiries,interest rate questions


    Important : 
    -"critical" and "high" urgency issues REQUIRE escalation to a human agent.
    -"medium" and "low" urgency issues CAN be handled by AI.
    -update urgency level if new information suggests a change in urgency.
    -if user explicitly requests human agent, set urgency to "critical".
    -If AI cannot provide satisfactory response, escalate to human agent by setting urgency to "critical".

    Return the updated user details as a JSON object including any newly extracted fields, the classified "current_issue", and the assessed "urgency" level. If no new information is found, return an empty object {{}}.
    Only include fields that are explicitely mentioned or assessed. You can include if it is relevent.use lowercase with underscores for field names.
    You can update if any field is already present in current details like income,cibil_score.

    Example 1 : User says "I am John, 30 years old, looking for a personal loan of 50000 with an income of 70000 and cibil score of 750"
    Response : {{"name":"John","age":"30","loan_amount":"50000","income":"70000","credit_score":"750","current_issue":"loan_query","urgency":"medium"}}
    Example 2 : User says "There was a fraudulent transaction on my account and I need help immediately!"
    Response : {{"current_issue":"transaction_issue","urgency":"critical"}}
    Example 3 : User says "What is the interest rate on home loans?"
    Response : {{"current_issue":"general_inquiry","urgency":"low"}}
    Example 4 : User says "I want to speak to a human agent right now!"
    Response : {{'current_issue":"complaint","urgency":"critical"}}
    JSON output only:
    """

#Calling LLM to extract details
    response=llm.invoke([HumanMessage(content=prompt)])
    extracted=response.content.strip()

#Cleaning the extracted JSON
    if extracted.startswith("```json"):
        extracted=extracted.replace("```json","").replace("```","").strip()
    elif extracted.startswith("```"):
        extracted=extracted.replace("```","").strip()

#Parsing and updating user details
    new_details=json.loads(extracted)
    urgency= new_details.get('urgency','low')
    requires_human= urgency in ['critical','high']

    if new_details:
        current_details.update(new_details)
        save_user_details(current_details)
        return True,new_details,requires_human
    return False,{},False


#Defining the State of the Chatbot
class ChatbotState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

#Defining the Chat Node of graph 
#It takes current_prompt and history_of_the_thread
# and generates AI response using LLM
def chat_node(state:ChatbotState):
    messages=state['messages']

    user_details=load_user_details()
    prompt=f""" You are an AI customer support agent for a financial services company.
    Know the user details below:
    {json.dumps(user_details,indent=2)if user_details else "no details available."}
    Use these details to provide personalized assistance.Answer financial Queries Professionally.
    Be short and to the point,no hallucinations

    """
    Combined_Prompt=[SystemMessage(content=prompt)]+messages
    response= llm.invoke(Combined_Prompt)
    return {"messages":[response]}

#Setting up SQLite Database for conversation Memory
conn=sqlite3.connect(database='Chatbot.db',check_same_thread=False)
checkpointer=SqliteSaver(conn=conn)

#Building the Chatbot workflow
graph = StateGraph(ChatbotState)
graph.add_node("chat_node",chat_node)
graph.add_edge(START,"chat_node")
graph.add_edge("chat_node",END)

#Compiling the Chatbot with checkpointer for conversation history
Chatbot=graph.compile(checkpointer=checkpointer)

#Naming the chat thread
CONFIG = {'configurable': {'thread_id': 'terminal_chat_thread'}}

#Loading previous conversation state if exists
state=Chatbot.get_state(config=CONFIG)

print("ChatBot is Ready! Type ['quit','exit','bye'] to exit.\n")

#Main Conversation Loop
while True:
    user_input=input("you : ").strip()
    if user_input.lower() in ['quit','exit','bye']:
        print("Exiting chat !! ")
        break
#Skip Empty Inputs
    if not user_input:
        continue
    
    user_details=load_user_details()
    extracted,new_info,requires_human=extract_user_details(user_input,user_details)

#Calling Chatbot to generate response
    response=Chatbot.invoke(
        {"messages":[HumanMessage(content=user_input)]},
        config=CONFIG)
    
#Extracting bot message
    bot_message=response['messages'][-1].content

    if requires_human:
        print("Bot : I will transfer you to a human agent.\n Please wait...")
    print(f"Bot : {bot_message}\n")



#print(Chatbot.invoke({"messages":[HumanMessage(content="Who is virat kohli")]})['messages'][0].content)