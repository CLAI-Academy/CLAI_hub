import asyncio
from typing import Optional
import sys

# Importar los módulos necesarios
# Nota: Asegúrate de tener los archivos cafe_tools.py con las herramientas modificadas 
# (sin valores por defecto) y main.py con los agentes definidos
from main import (
    agente_recepcionista, 
    agente_barista, 
    agente_comida, 
    agente_caja
)
from conversation_history import HistorialConversacion, continuar_conversacion




# Función principal para la demo interactiva
async def demo_interactiva():
    print("\n===== BIENVENIDO AL CAFÉ VIRTUAL =====\n")
    print("Puedes conversar con nuestros agentes virtuales.")
    print("Escribe 'salir' para terminar, 'historial' para ver la conversación anterior.")
    print("Escribe 'agente:nombre' para hablar con un agente específico (recepcionista, barista, comida, caja).")
    print("\n=======================================\n")
    
    # Crear historial de conversación
    historial = HistorialConversacion()
    
    while True:
        try:
            # Obtener entrada del usuario
            mensaje = input("\nTú: ")
            
            # Verificar comandos especiales
            if mensaje.lower() == "salir":
                print("¡Gracias por visitar nuestro café virtual!")
                break
            elif mensaje.lower() == "historial":
                print("\n" + historial.obtener_historial_formateado())
                continue
            elif mensaje.lower().startswith("agente:"):
                partes = mensaje.split(":", 1)
                if len(partes) > 1:
                    nombre_agente = partes[1].strip().lower()
                    mensaje_real = input("Tu mensaje para el agente: ")
                    
                    # Seleccionar agente según nombre
                    agente = None
                    if "recepcionista" in nombre_agente:
                        agente = agente_recepcionista
                    elif "barista" in nombre_agente:
                        agente = agente_barista
                    elif "comida" in nombre_agente:
                        agente = agente_comida
                    elif "caja" in nombre_agente:
                        agente = agente_caja
                    else:
                        print(f"Agente '{nombre_agente}' no reconocido.")
                        continue
                    
                    # Continuar con el agente específico
                    respuesta = await continuar_conversacion(historial, mensaje_real, agente)
                    print(f"\n{agente.name}: {respuesta}")
                    continue
            
            # Procesar mensaje normal
            print("Procesando tu mensaje...")
            respuesta = await continuar_conversacion(historial, mensaje)
            
            # Obtener el nombre del último agente que respondió
            ultimo_agente = historial.obtener_ultimo_agente()
            print(f"\n{ultimo_agente}: {respuesta}")
            
        except KeyboardInterrupt:
            print("\n\nConversación interrumpida. ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"\nError en la conversación: {e}")
            print("Intenta con otro mensaje o escribe 'salir' para terminar.")

# Función para iniciar la conversación con un mensaje predefinido
async def iniciar_con_mensaje(mensaje_inicial: str):
    historial = HistorialConversacion()
    
    print(f"\n===== CAFÉ VIRTUAL =====\n")
    print(f"Iniciando conversación con: '{mensaje_inicial}'")
    
    try:
        respuesta = await continuar_conversacion(historial, mensaje_inicial)
        ultimo_agente = historial.obtener_ultimo_agente()
        print(f"\n{ultimo_agente}: {respuesta}\n")
        
        # Continuar con la conversación interactiva
        while True:
            mensaje = input("Tú: ")
            if mensaje.lower() == "salir":
                print("¡Hasta pronto!")
                break
                
            respuesta = await continuar_conversacion(historial, mensaje)
            ultimo_agente = historial.obtener_ultimo_agente()
            print(f"\n{ultimo_agente}: {respuesta}\n")
            
    except Exception as e:
        print(f"Error: {e}")

# Punto de entrada
if __name__ == "__main__":
    # Si se proporciona un argumento, usarlo como mensaje inicial
    if len(sys.argv) > 1:
        mensaje_inicial = " ".join(sys.argv[1:])
        asyncio.run(iniciar_con_mensaje(mensaje_inicial))
    else:
        # De lo contrario, iniciar la demo interactiva
        asyncio.run(demo_interactiva())