**AI Financial Customer Support Chatbot**
An intelligent conversational agent built with LangGraph and Google Gemini that provides personalized financial customer support with automatic escalation capabilities.

 **Technical Stack**
#  Component                    Technology
 LLM                          Google Gemini 2.5 Flash
 Framework                    LangGraph
 Conversation Memory          SQLite (via LangGraph Checkpointer)
 User Data Storage            JSON file
 API Management               python-dotenv


 **Features**

Persistent User Memory: Remembers user details across conversations (name, income, loan amounts, credit scores, etc.)
Intelligent Issue Classification: Automatically categorizes queries .
Conversation History: Thread-based chat memory using SQLite checkpointing
Personalized Responses: Context-aware answers based on stored user information
Natural Language Understanding: Extracts structured data from unstructured user input


**Prerequisites**
Python 3.8+
Google API Key (for Gemini access)

**Required dependencies:**
pip install langgraph langchain-google-genai python-dotenv





