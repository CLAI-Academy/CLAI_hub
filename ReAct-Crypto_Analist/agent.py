import os
import re
import math
import json
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime
from colorama import Fore
from colorama import Style
from tool import Tool
from tool import validate_arguments
from utils.completions import build_prompt_structure
from utils.completions import ChatHistory
from utils.completions import completions_create
from utils.completions import update_chat_history
from utils.extraction import extract_tag_content


# cargamos las variables de entorno, ahi debera estar nuestra API de Groq
load_dotenv()

fecha_actual = datetime.now()

# Formatear la fecha como desees
fecha_formateada = fecha_actual.strftime("%Y-%m-%d")  # Formato: Año-Mes-Día

MODEL = "llama-3.3-70b-versatile"
GROQ_CLIENT = Groq()

BASE_SYSTEM_PROMPT = ""   

# Define the System Prompt as a constant
REACT_SYSTEM_PROMPT = f"""
You are a function calling AI model. You operate by running a loop with the following steps: Thought, Action, Observation.
You are provided with function signatures within <tools></tools> XML tags.
You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. Pay special attention to the properties 'types'. You should use those types as in a Python dict.

For each function call return a JSON object with the function name and arguments within <tool_call></tool_call> XML tags as follows:

<tool_call> {{"name": "<function-name>", "arguments": "<args-dict>", "id": "<monotonically-increasing-id>"}} </tool_call>

Here are the available tools / actions:

<tools> %s </tools>
Example session:

<question>What is the current price of Solana?</question>
<thought>I need to get the current price of solana</thought>
<tool_call>{{"name": "get_actual_data", "arguments": {{"moneda": "solana"}}, "id": 0}}</tool_call>

You will be called again with this:

<observation>{{0: {{"Precio": "$96,065.33"}}}}</observation>

You then output:

<response>The current price of Solana is $96,065.33</response>

Example session 2:

<question>What was the price of Ethereum on January 12, 2024?</question>
<thought>I need to get the historical data for ethereum on January 12, 2024</thought>
<tool_call>{{"name": "get_historic_data", "arguments": {{"moneda": "ethereum", "fecha": "Jan 12, 2024"}}, "id": 0}}</tool_call>

ALWAYS in the tool call, you need to put the data in this format, if the date is January 12, 2024, you put Jan 12, 2024.

If the user requests data from a week ago, subtract the necessary days from this date: {fecha_formateada}. 
Once adjusted, format it exactly as before. For example, if the current date is 09-02-2025, and they ask for data from a week ago, provide data for 02-02-2025 (Feb 02, 2025). 
If they ask for data from a month ago and the date is 09-02-2025, provide 09-01-2025 (Jan 09, 2025). 
Always ensure the date follows the same format.

You will be called again with this:

<observation>{{0: {{"Apertura": "$189.76", "Alza": "$203.15", "Baja": "$188.48", "MarketCap": "$93,740,476,812"}}}}</observation>

You then output:

<response>The stock opened at $189.76, reached a high of $203.15, a low of $188.48, and has a market cap of $93.74 billion.</response>

Additional constraints:

- If the user asks you something unrelated to any of the tools above, answer freely enclosing your answer with <response></response> tags.
"""


class ReactAgent:
    """
    A class that represents an agent using the ReAct logic that interacts with tools to process
    user inputs, make decisions, and execute tool calls. The agent can run interactive sessions,
    collect tool signatures, and process multiple tool calls in a given round of interaction.

    Attributes:
        client (Groq): The Groq client used to handle model-based completions.
        model (str): The name of the model used for generating responses. Default is "llama-3.1-70b-versatile".
        tools (list[Tool]): A list of Tool instances available for execution.
        tools_dict (dict): A dictionary mapping tool names to their corresponding Tool instances.
    """

    def __init__(
        self,
        tools: Tool | list[Tool],
        model: str = "llama-3.1-70b-versatile",
        system_prompt: str = BASE_SYSTEM_PROMPT,
    ) -> None:
        self.client = Groq()
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools if isinstance(tools, list) else [tools]
        self.tools_dict = {tool.name: tool for tool in self.tools}

    def add_tool_signatures(self) -> str:
        """
        Collects the function signatures of all available tools.

        Returns:
            str: A concatenated string of all tool function signatures in JSON format.
        """
        return "".join([tool.fn_signature for tool in self.tools])

    def process_tool_calls(self, tool_calls_content: list) -> dict:
        """
        Processes each tool call, validates arguments, executes the tools, and collects results.

        Args:
            tool_calls_content (list): List of strings, each representing a tool call in JSON format.

        Returns:
            dict: A dictionary where the keys are tool call IDs and values are the results from the tools.
        """
        observations = {}
        for tool_call_str in tool_calls_content:
            tool_call = json.loads(tool_call_str)
            tool_name = tool_call["name"]
            tool = self.tools_dict[tool_name]

            print(Fore.GREEN + f"\nUsing Tool: {tool_name}")

            # Validate and execute the tool call
            validated_tool_call = validate_arguments(
                tool_call, json.loads(tool.fn_signature)
            )
            print(Fore.GREEN + f"\nTool call dict: \n{validated_tool_call}")

            result = tool.run(**validated_tool_call["arguments"])
            print(Fore.GREEN + f"\nTool result: \n{result}")

            # Store the result using the tool call ID
            observations[validated_tool_call["id"]] = result

        return observations

    def run(
        self,
        user_msg: str,
        max_rounds: int = 10,
    ) -> str:
        """
        Executes a user interaction session, where the agent processes user input, generates responses,
        handles tool calls, and updates chat history until a final response is ready or the maximum
        number of rounds is reached.

        Args:
            user_msg (str): The user's input message to start the interaction.
            max_rounds (int, optional): Maximum number of interaction rounds the agent should perform. Default is 10.

        Returns:
            str: The final response generated by the agent after processing user input and any tool calls.
        """
        user_prompt = build_prompt_structure(
            prompt=user_msg, role="user", tag="question"
        )
        if self.tools:
            self.system_prompt += (
                "\n" + REACT_SYSTEM_PROMPT % self.add_tool_signatures()
            )

        chat_history = ChatHistory(
            [
                build_prompt_structure(
                    prompt=self.system_prompt,
                    role="system",
                ),
                user_prompt,
            ]
        )

        if self.tools:
            # Run the ReAct loop for max_rounds
            for _ in range(max_rounds):

                completion = completions_create(self.client, chat_history, self.model)

                response = extract_tag_content(str(completion), "response")
                if response.found:
                    return response.content[0]

                thought = extract_tag_content(str(completion), "thought")
                tool_calls = extract_tag_content(str(completion), "tool_call")

                update_chat_history(chat_history, completion, "assistant")

                print(Fore.MAGENTA + f"\nThought: {thought.content[0]}")

                if tool_calls.found:
                    observations = self.process_tool_calls(tool_calls.content)
                    print(Fore.BLUE + f"\nObservations: {observations}")
                    update_chat_history(chat_history, f"{observations}", "user")

        return completions_create(self.client, chat_history, self.model)