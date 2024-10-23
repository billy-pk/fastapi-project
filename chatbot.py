# import the required libraries
import os
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

# set the environment variables

os.environ['TAVILY_API_KEY'] = os.environ.get('TAVILY_API_KEY')
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY')

# Define the Chatbot class
class Chatbot:
    def __init__(self):
        # Initialize the model and graph here
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_retries=1, n=1)

        tool = TavilySearchResults(max_results=1)
        tools = [tool]
        llm_with_tools = llm.bind_tools(tools)

        sys_msg = SystemMessage(content="You are a helpful assistant, you will reply briefly.")

        def assistant(state: MessagesState):
            return {'messages': [llm_with_tools.invoke([sys_msg] + state['messages'])]}

        builder = StateGraph(MessagesState)
        builder.add_node("assistant", assistant)
        builder.add_node("tools", ToolNode(tools))
        builder.add_edge(START, "assistant")
        builder.add_conditional_edges("assistant", tools_condition)
        builder.add_edge("tools", "assistant")

        memory = MemorySaver()

        # Assign the compiled graph to a class attribute so it can be accessed in other methods
        self.graph = builder.compile(checkpointer=memory)

    def invoke_graph(self, user_input):
        # Add the new user input to the conversation history
        conversation_history = [HumanMessage(content=str(user_input))]
        config = {'configurable': {'thread_id': '1'}}

        # Use self.graph to invoke the chatbot
        response = self.graph.invoke({"messages": conversation_history}, config)

        # Get the AI's response
        ai_message = response['messages'][-1]
        return ai_message.content


# Test the Chatbot by creating an instance and invoking a query
if __name__ == "__main__":
    chatbot = Chatbot()
    response = chatbot.invoke_graph("Hello, how are you?")
    print(response)
