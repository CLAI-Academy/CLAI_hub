from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from colorama import Fore, Back, Style, init
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from langchain_openai import ChatOpenAI
from openai import OpenAI
import os
from agents.fundamentals import fundamentals_agent
from agents.portfolio_manager import portfolio_management_agent
from agents.technicals import technical_analyst_agent
from agents.risk_manager import risk_management_agent
from agents.sentiment import sentiment_agent
from graph.state import AgentState
from agents.valuation import valuation_agent
from utils.display import print_trading_output

class HedgeFundAgent:
    def __init__(self, llm):
        """Initialize the hedge fund agent with a language model.
        
        Args:
            llm: Language model instance to be used for analysis
        """
        self.llm = llm
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        init(autoreset=True)

    def _parse_hedge_fund_response(self, response):
        """Parse the JSON response from the hedge fund.
        
        Args:
            response: Raw response string from the hedge fund
            
        Returns:
            dict: Parsed response or None if parsing fails
        """
        try:
            return json.loads(response)
        except:
            print(f"Error parsing response: {response}")
            return None

    def _create_workflow(self):
        """Create the workflow graph for the hedge fund.
        
        Returns:
            StateGraph: Configured workflow graph
        """
        workflow = StateGraph(AgentState)

        # Define the start node
        def start(state: AgentState):
            """Initialize the workflow with the input message."""
            return state

        # Add nodes
        workflow.add_node("start_node", start)
        workflow.add_node("technical_analyst_agent", technical_analyst_agent)
        workflow.add_node("fundamentals_agent", fundamentals_agent)
        workflow.add_node("sentiment_agent", sentiment_agent)
        workflow.add_node("risk_management_agent", risk_management_agent)
        workflow.add_node("portfolio_management_agent", 
                         lambda state: portfolio_management_agent(state, self.llm))
        workflow.add_node("valuation_agent", valuation_agent)

        # Define the workflow
        workflow.set_entry_point("start_node")
        workflow.add_edge("start_node", "technical_analyst_agent")
        workflow.add_edge("start_node", "fundamentals_agent")
        workflow.add_edge("start_node", "sentiment_agent")
        workflow.add_edge("start_node", "valuation_agent")
        workflow.add_edge("technical_analyst_agent", "risk_management_agent")
        workflow.add_edge("fundamentals_agent", "risk_management_agent")
        workflow.add_edge("sentiment_agent", "risk_management_agent")
        workflow.add_edge("valuation_agent", "risk_management_agent")
        workflow.add_edge("risk_management_agent", "portfolio_management_agent")
        workflow.add_edge("portfolio_management_agent", END)

        return workflow

    def analyze(self, ticker: str, portfolio: dict, 
                start_date: str = None, end_date: str = None, 
                show_reasoning: bool = False):
        """Analyze a stock and make trading decisions.
        
        Args:
            ticker: Stock ticker symbol
            portfolio: Dictionary containing current portfolio state
            start_date: Analysis start date (YYYY-MM-DD)
            end_date: Analysis end date (YYYY-MM-DD)
            show_reasoning: Whether to show detailed agent reasoning
            
        Returns:
            dict: Analysis results and trading decision
        """
        # Set default dates if not provided
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            start_date = (end_date_obj - relativedelta(months=3)).strftime("%Y-%m-%d")

        # Validate dates
        for date_str in [start_date, end_date]:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Date {date_str} must be in YYYY-MM-DD format")

        final_state = self.app.invoke({
            "messages": [
                HumanMessage(
                    content="Make a trading decision based on the provided data.",
                )
            ],
            "data": {
                "ticker": ticker,
                "portfolio": portfolio,
                "start_date": start_date,
                "end_date": end_date,
                "analyst_signals": {},
            },
            "metadata": {
                "show_reasoning": show_reasoning,
            },
        })

        return {
            "decision": self._parse_hedge_fund_response(final_state["messages"][-1].content),
            "analyst_signals": final_state["data"]["analyst_signals"],
        }

def get_llm(model_flag: str):
    """Get the appropriate LLM based on the model flag.
    
    Args:
        model_flag: String indicating which model to use ('4' or 'deepseek')
        
    Returns:
        LLM instance
    """
    if model_flag == "4o":
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0
        )
    elif model_flag == "deepseek":
        return ChatOpenAI(
            model="deepseek-reasoner",
            temperature=0,
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
    else:
        raise ValueError("Invalid model flag. Must be '4o' or 'deepseek'")

# Example usage in main.py:
if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    import os

    # Load environment variables
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run the hedge fund trading system")
    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--show-reasoning", action="store_true", help="Show reasoning from each agent")
    parser.add_argument("--model", type=str, choices=['4o', 'deepseek'], required=True,
                      help="Choose LLM model: '4o' for GPT-4 or 'deepseek' for DeepSeek")

    args = parser.parse_args()

    # Get the appropriate LLM based on the model flag
    llm = get_llm(args.model)

    # Initialize the hedge fund agent with the selected LLM
    hedge_fund = HedgeFundAgent(llm)

    # Set up the portfolio
    portfolio = {
        "cash": 100000.0,  # $100,000 initial cash
        "stock": 0,  # No initial stock position
    }

    # Run the analysis
    result = hedge_fund.analyze(
        ticker=args.ticker,
        start_date=args.start_date,
        end_date=args.end_date,
        portfolio=portfolio,
        show_reasoning=args.show_reasoning
    )
    
    print_trading_output(result)