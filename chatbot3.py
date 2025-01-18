# import the required libraries
import os
import json
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

# set the environment variables

os.environ['TAVILY_API_KEY'] = os.environ.get('TAVILY_API_KEY')
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY')

os.environ['GOOGLE_API_KEY'] = os.environ.get('GOOGLE_API_KEY')

# Define the Chatbot class
class Chatbot:
    def __init__(self):
        # Initialize the model and graph here
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0
        )

        self.tool = TavilySearchResults(max_results=1)
        self.tools = [self.tool]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Remove the system message from initialization
        self.builder = StateGraph(MessagesState)
        self.builder.add_node("assistant", self.assistant)
        self.builder.add_node("tools", ToolNode(self.tools))
        self.builder.add_edge(START, "assistant")
        self.builder.add_conditional_edges("assistant", tools_condition)
        self.builder.add_edge("tools", "assistant")

        self.memory = MemorySaver()
        self.graph = self.builder.compile(checkpointer=self.memory)

    def assistant(self, state: MessagesState):
        # Instead of using SystemMessage, prepend the instruction to the first human message
        
        messages = state['messages']
        if messages and isinstance(messages[0], HumanMessage):
            messages[0].content = "You are a helpful assistant. You will reply briefly.\n\n" + messages[0].content
        return {'messages': [self.llm_with_tools.invoke(messages)]}
    
    def invoke_graph(self, user_input, thread_id = "1"):
        # Load the existing conversation history (memory)
        conversation_history = self.load_conversation(thread_id)
        # Add the new user input to the conversation history
        conversation_history.append(HumanMessage(content=user_input))

        config = {'configurable': {'thread_id': thread_id}}

        # Use self.graph to invoke the chatbot
        response = self.graph.invoke({"messages": conversation_history}, config)

        # # Get the AI's response
        # ai_message = response['messages'][-1]
        # return ai_message.content

        # Add the AI's response to the conversation history
        conversation_history.append(response['messages'][-1])

        # Save the updated conversation history
        self.save_conversation(conversation_history, thread_id)

        # Return the AI's message content
        return response['messages'][-1].content
    
    def load_conversation(self, thread_id):
        # Load conversation history from a file or database
        if os.path.exists(f"memory_{thread_id}.json"):
            with open(f"memory_{thread_id}.json", "r") as file:
                data = json.load(file)
                return [
                    HumanMessage(content=msg['content']) if msg['role'] == "user"
                    else AIMessage(content=msg['content'])  # Convert all non-user messages to AIMessage
                    for msg in data
                ]
        return []

    def save_conversation(self, conversation_history, thread_id):
        # Save the conversation history to a file or database
        data = [
            {
                'role': 'user' if isinstance(msg, HumanMessage)
                else 'assistant',  # All non-user messages are saved as assistant
                'content': msg.content
            }
            for msg in conversation_history
        ]
        with open(f"memory_{thread_id}.json", "w") as file:
            json.dump(data, file)


# Test the Chatbot by creating an instance and invoking a query
if __name__ == "__main__":
    chatbot = Chatbot()
    response = chatbot.invoke_graph("Hello, how are you?")
    print(response)

""" Instead of using a separate SystemMessage (which Gemini doesn't support well), we prepend the system instructions to the first human message
This is a workaround because Gemini handles everything as either human or AI messages
3. Conversation History Management:
 Simplified to only handle two types of messages: HumanMessage and AIMessage
Removed SystemMessage handling completely
All non-user messages are treated as AI messages
Saving Conversations:
Simplified the role classification to just 'user' or 'assistant'
Removed the 'system' role option
Makes the conversation storage more compatible with Gemini's expectations
The key concept behind all these changes is that Gemini has a simpler message handling model compared to some other LLMs (like GPT). It primarily works with just human and AI messages, so we adapted the code to work within these constraints while maintaining the functionality."""