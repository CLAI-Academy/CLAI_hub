from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate
from colorama import Fore, Back, Style, init
from dotenv import load_dotenv
import os
import argparse
import time  # Importar time para los delays

from main import HedgeFundAgent, get_llm
from tools.api import get_price_data
from utils.display import print_backtest_results, format_backtest_row

init(autoreset=True)

class Backtester:
    def __init__(self, agent, ticker, start_date, end_date, initial_capital, initial_shares=0, api_delay=7):
        """
        Initialize the Backtester with a HedgeFundAgent instance
        
        Args:
            agent: Instance of HedgeFundAgent
            ticker: Stock ticker symbol
            start_date: Start date for backtesting
            end_date: End date for backtesting
            initial_capital: Initial investment amount
            initial_shares: Initial number of shares (default: 0)
            api_delay: Seconds to wait between API calls (default: 7)
        """
        self.agent = agent
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.api_delay = api_delay  # Tiempo de espera entre llamadas a la API
        
        # Inicializar portafolio con efectivo completo primero
        self.portfolio = {"cash": initial_capital, "stock": 0, "portfolio_value": initial_capital}
        
        # Si se especifican acciones iniciales, ajustar el portafolio
        if initial_shares > 0:
            initial_price_data = get_price_data(self.ticker, self.start_date, self.start_date)
            time.sleep(self.api_delay)  # Esperar después de llamar a la API
            
            if not initial_price_data.empty:
                initial_price = initial_price_data.iloc[0]["close"]
                # Asignamos directamente las acciones sin "comprar"
                self.portfolio = {
                    "cash": initial_capital,  # conservas tu efectivo intacto
                    "stock": initial_shares,
                    # El valor total es la suma de tu efectivo + valor de las acciones
                    "portfolio_value": initial_capital + initial_shares * initial_price
                }
                print(
                    f"Portafolio inicializado con {initial_shares} acciones de {self.ticker} a ${initial_price:.2f} "
                    f"(valor: ${initial_shares * initial_price:.2f}) + ${initial_capital:.2f} en efectivo."
                )
            else:
                print(f"Advertencia: No hay datos de precio para {self.start_date}. Iniciando sin acciones.")

        self.portfolio_values = []
        
        # Registrar el estado inicial del portafolio
        if self.portfolio["stock"] > 0:
            # Obtener el precio inicial nuevamente para asegurar consistencia
            initial_price_data = get_price_data(self.ticker, self.start_date, self.start_date)
            time.sleep(self.api_delay)  # Esperar después de llamar a la API
            
            if not initial_price_data.empty:
                initial_price = initial_price_data.iloc[0]["close"]
                self.portfolio_values.append({
                    "Date": pd.to_datetime(self.start_date),
                    "Portfolio Value": self.portfolio["portfolio_value"]
                })

    def execute_trade(self, action, quantity, current_price):
        """Validate and execute trades based on portfolio constraints"""
        if action == "buy" and quantity > 0:
            cost = quantity * current_price
            if cost <= self.portfolio["cash"]:
                self.portfolio["stock"] += quantity
                self.portfolio["cash"] -= cost
                return quantity
            else:
                # Calculate maximum affordable quantity
                max_quantity = int(self.portfolio["cash"] // current_price)
                if max_quantity > 0:
                    self.portfolio["stock"] += max_quantity
                    self.portfolio["cash"] -= max_quantity * current_price
                    return max_quantity
                return 0
        elif action == "sell" and quantity > 0:
            quantity = min(quantity, self.portfolio["stock"])
            if quantity > 0:
                self.portfolio["cash"] += quantity * current_price
                self.portfolio["stock"] -= quantity
                return quantity
            return 0
        return 0

    def run_backtest(self):
        dates = pd.date_range(self.start_date, self.end_date, freq="B")
        table_rows = []
        
        print("\nStarting backtest...")
        
        # Añadir una fila inicial a la tabla para mostrar el estado inicial
        initial_price_data = get_price_data(self.ticker, self.start_date, self.start_date)
        time.sleep(self.api_delay)  # Esperar después de llamar a la API
        
        if not initial_price_data.empty and self.portfolio["stock"] > 0:
            initial_price = initial_price_data.iloc[0]["close"]
            
            # Crear una fila inicial para la tabla
            initial_row = format_backtest_row(
                date=self.start_date,
                ticker=self.ticker,
                action="initial",  # Indicar que es el estado inicial
                quantity=0,        # No hay transacción inicial
                price=initial_price,
                cash=self.portfolio['cash'],
                stock=self.portfolio['stock'],
                total_value=self.portfolio['portfolio_value'],
                bullish_count=0,
                bearish_count=0,
                neutral_count=0
            )
            table_rows.append(initial_row)
            
            # Mostrar la tabla inicial
            print_backtest_results(table_rows)

        for current_date in dates:
            lookback_start = (current_date - timedelta(days=30)).strftime("%Y-%m-%d")
            current_date_str = current_date.strftime("%Y-%m-%d")
            
            # Omitir la primera fecha si ya agregamos una fila inicial
            if current_date_str == self.start_date and len(table_rows) > 0:
                continue
                
            print(f"\nProcesando fecha: {current_date_str}")
            print(f"Esperando {self.api_delay} segundos antes de hacer la siguiente llamada a la API...")
            time.sleep(self.api_delay)  # Esperar antes de analizar la siguiente fecha

            try:
                # Use the analyze method of HedgeFundAgent
                output = self.agent.analyze(
                    ticker=self.ticker,
                    portfolio=self.portfolio,
                    start_date=lookback_start,
                    end_date=current_date_str
                )
                
                agent_decision = output["decision"]
                action, quantity = agent_decision["action"], agent_decision["quantity"]
                
                # Esperar después de la llamada de análisis y antes de obtener datos de precios
                print(f"Esperando {self.api_delay} segundos antes de obtener datos de precios...")
                time.sleep(self.api_delay)
                
                df = get_price_data(self.ticker, lookback_start, current_date_str)
                if df.empty:
                    print(f"No price data available for {current_date_str}. Skipping this date.")
                    continue
                    
                current_price = df.iloc[-1]["close"]

                # Execute the trade with validation
                executed_quantity = self.execute_trade(action, quantity, current_price)

                # Update total portfolio value
                total_value = self.portfolio["cash"] + self.portfolio["stock"] * current_price
                self.portfolio["portfolio_value"] = total_value

                # Count signals
                analyst_signals = output["analyst_signals"]
                bullish_count = len([s for s in analyst_signals.values() if s.get("signal") == "bullish"])
                bearish_count = len([s for s in analyst_signals.values() if s.get("signal") == "bearish"])
                neutral_count = len([s for s in analyst_signals.values() if s.get("signal") == "neutral"])

                # Format and add row
                table_rows.append(format_backtest_row(
                    date=current_date.strftime('%Y-%m-%d'),
                    ticker=self.ticker,
                    action=action,
                    quantity=executed_quantity,
                    price=current_price,
                    cash=self.portfolio['cash'],
                    stock=self.portfolio['stock'],
                    total_value=total_value,
                    bullish_count=bullish_count,
                    bearish_count=bearish_count,
                    neutral_count=neutral_count
                ))

                # Display the updated table
                print_backtest_results(table_rows)

                # Record the portfolio value
                self.portfolio_values.append(
                    {"Date": current_date, "Portfolio Value": total_value}
                )
                
            except Exception as e:
                print(f"Error en la fecha {current_date_str}: {e}")
                print("Esperando tiempo adicional antes de continuar...")
                time.sleep(self.api_delay * 2)  # Esperar el doble de tiempo en caso de error
                continue

    def analyze_performance(self):
        # Convert portfolio values to DataFrame
        performance_df = pd.DataFrame(self.portfolio_values).set_index("Date")

        # Calculate total return
        total_return = (
            self.portfolio["portfolio_value"] - self.initial_capital
        ) / self.initial_capital
        print(f"\nPerformance Analysis:")
        print(f"Total Return: {total_return * 100:.2f}%")

        # Plot the portfolio value over time
        plt.figure(figsize=(12, 6))
        performance_df["Portfolio Value"].plot(
            title=f"Portfolio Value Over Time - {self.ticker}"
        )
        plt.ylabel("Portfolio Value ($)")
        plt.xlabel("Date")
        plt.grid(True)
        plt.show()

        # Compute daily returns
        performance_df["Daily Return"] = performance_df["Portfolio Value"].pct_change()

        # Calculate Sharpe Ratio (assuming 252 trading days in a year)
        mean_daily_return = performance_df["Daily Return"].mean()
        std_daily_return = performance_df["Daily Return"].std()
        sharpe_ratio = (mean_daily_return / std_daily_return) * (252**0.5) if std_daily_return > 0 else 0
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")

        # Calculate Maximum Drawdown
        rolling_max = performance_df["Portfolio Value"].cummax()
        drawdown = performance_df["Portfolio Value"] / rolling_max - 1
        max_drawdown = drawdown.min()
        print(f"Maximum Drawdown: {max_drawdown * 100:.2f}%")

        return performance_df


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run backtesting simulation")
    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol (e.g., AAPL)")
    parser.add_argument(
        "--end-date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=(datetime.now() - relativedelta(months=3)).strftime("%Y-%m-%d"),
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=100000,
        help="Initial capital amount (default: 100000)",
    )
    parser.add_argument(
        "--initial-shares",
        type=int,
        default=0,
        help="Initial number of shares to start with (default: 0)",
    )
    parser.add_argument("--model", type=str, choices=['4o', 'deepseek'], required=True,
                      help="Choose LLM model: '4o' for GPT-4 or 'deepseek' for DeepSeek")
    parser.add_argument(
        "--api-delay",
        type=int,
        default=7,
        help="Seconds to wait between API calls (default: 7)",
    )

    args = parser.parse_args()

    # Get the appropriate LLM based on the model flag
    llm = get_llm(args.model)

    # Create HedgeFundAgent instance
    hedge_fund = HedgeFundAgent(llm)

    # Create an instance of Backtester with the HedgeFundAgent
    backtester = Backtester(
        agent=hedge_fund,
        ticker=args.ticker,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.initial_capital,
        initial_shares=args.initial_shares,
        api_delay=args.api_delay,
    )

    # Run the backtesting process
    backtester.run_backtest()
    performance_df = backtester.analyze_performance()