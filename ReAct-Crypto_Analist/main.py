from tool import tool
from agent import ReactAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import math


@tool
def get_actual_data(moneda: str) -> dict:
    

    class Scraper:
        def __init__(self, moneda: str):
            self.moneda = moneda
            self.url = f"https://coinmarketcap.com/es/currencies/{self.moneda}/"
            self.options = webdriver.ChromeOptions()
            self.options.add_argument("--headless")
        
        def run(self) -> str:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.options
            )
            driver.get(self.url)
            try:
                # Se busca el elemento que contiene el precio
                span = driver.find_element(By.CLASS_NAME, "sc-65e7f566-0.WXGwg.base-text")
                resultado = span.text
            except Exception as e:
                resultado = f"Error: {e}"
            driver.quit()
            return resultado

    resultado = Scraper(moneda).run()
    if resultado.startswith("Error:"):
        return {"error": resultado}
    return {"Precio": resultado}


@tool
def get_historic_data(moneda: str, fecha: str) -> dict:
    
    class Scraper:
        def __init__(self, moneda: str, fecha: str):
            self.moneda = moneda
            self.fecha = fecha
            self.url = f"https://coinmarketcap.com/es/currencies/{self.moneda}/historical-data/"
            self.options = webdriver.ChromeOptions()
            self.options.add_argument("--headless")
        
        def run(self) -> dict:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.options
            )
            driver.get(self.url)
            wait = WebDriverWait(driver, 10)
            try:
                # Se localiza la fila que contiene la fecha indicada
                fila = wait.until(
                    EC.visibility_of_element_located(
                        (By.XPATH, f"//tbody/tr[td[normalize-space(text())='{self.fecha}']]")
                    )
                )
                columnas = fila.find_elements(By.TAG_NAME, "td")
                resultado = {
                    "Apertura": columnas[1].text,
                    "Alza": columnas[2].text,
                    "Baja": columnas[3].text,
                    "MarketCap": columnas[6].text
                }
            except Exception as e:
                resultado = {"error": str(e)}
            driver.quit()
            return resultado

    return Scraper(moneda, fecha).run()

@tool
def indicators_tool(moneda: str, fecha: str, Apertura: str, Alza: str, Baja: str, MarketCap: str):
    """
    Recibe los siguientes parámetros:
      - moneda: str (ej. "USD")
      - fecha: str (ej. "2025-02-09")
      - Apertura: precio de apertura (ej. '$32.18')
      - Alza: precio máximo del día (ej. '$32.56')
      - Baja: precio mínimo del día (ej. '$26.42')
      - MarketCap: capitalización de mercado (ej. '$11,353,366,736')
      
    Calcula y retorna un diccionario con:
      - volatilidad: ((Alza - Baja) / Apertura) * 100
      - potencial_ganancia: ((Alza - Apertura) / Apertura) * 100
      - potencial_perdida: ((Apertura - Baja) / Apertura) * 100
      - ratio_riesgo_beneficio: potencial_ganancia / potencial_perdida
      - indice_riesgo_simple: volatilidad / ln(MarketCap)
      
    Además, se incluyen los parámetros 'moneda' y 'fecha' en el resultado.
    """
    # Función auxiliar para limpiar el valor y convertirlo a float
    def limpiar_valor(valor_str):
        return float(valor_str.replace('$', '').replace(',', ''))
    
    # Convertir los valores recibidos a números
    apertura = limpiar_valor(Apertura)
    alza = limpiar_valor(Alza)
    baja = limpiar_valor(Baja)
    marketcap = limpiar_valor(MarketCap)
    
    # Calcular indicadores
    volatilidad = ((alza - baja) / apertura) * 100
    potencial_ganancia = ((alza - apertura) / apertura) * 100
    potencial_perdida = ((apertura - baja) / apertura) * 100
    ratio_riesgo_beneficio = (potencial_ganancia / potencial_perdida) if potencial_perdida != 0 else None
    indice_riesgo_simple = volatilidad / math.log(marketcap) if marketcap > 0 else None
    
    # Retornar los resultados junto con la moneda y la fecha
    return {
        'moneda': moneda,
        'fecha': fecha,
        'volatilidad': volatilidad,
        'potencial_ganancia': potencial_ganancia,
        'potencial_perdida': potencial_perdida,
        'ratio_riesgo_beneficio': ratio_riesgo_beneficio,
        'indice_riesgo_simple': indice_riesgo_simple
    }



agent = ReactAgent(
    model="llama-3.3-70b-versatile",
    tools=[get_historic_data, get_actual_data, indicators_tool]
)

if __name__ == "__main__":
    user_msg = input("¿Qué necesitas? ")
    output = agent.run(user_msg)
    print(output)
