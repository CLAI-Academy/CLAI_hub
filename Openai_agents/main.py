from agents import Agent, handoff, RunContextWrapper, Runner
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# Modelo para transferir información entre agentes
class OrdenCafe(BaseModel):
    bebida: Optional[str] = None
    tamaño: Optional[str] = None
    extras: Optional[List[str]] = None
    para_llevar: Optional[bool] = None
    nombre_cliente: Optional[str] = None
    comida: Optional[str] = None


# Importamos nuestras herramientas
from cafe_tools import (
    consultar_menu,
    verificar_disponibilidad,
    obtener_promociones,
    calcular_precio,
    generar_recibo
)

# Función simple que se ejecuta durante un handoff
async def transferir_a_barista(ctx: RunContextWrapper[None], orden: OrdenCafe):
    print("Transfiriendo con Barista")

async def transferir_a_comida(ctx: RunContextWrapper[None], orden: OrdenCafe):
    print("Transfiriendo con Comida")

async def transferir_a_caja(ctx: RunContextWrapper[None], orden: OrdenCafe):
    print("Transfiriendo con Caja")



# 2. AGENTE BARISTA
agente_barista = Agent(
    name="Barista",
    model="gpt-4o-mini",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    Eres el barista del café. Tu especialidad es:
    
    1. Ayudar a los clientes a elegir la bebida perfecta
    2. Preguntar sobre preferencias específicas (tamaño, intensidad, extras)
    3. Sugerir combinaciones populares y especialidades de la casa
    4. Confirmar si la bebida es para llevar o para consumir en el local
    
    Tienes acceso a herramientas que puedes usar:
    - consultar_menu: Para mostrar opciones de bebidas Utilizala SIEMPRE que el cliente pregunte por las bebidas
    - verificar_disponibilidad: Para comprobar si un producto está disponible
    - calcular_precio: Para informar el costo de las bebidas con extras
    
    Debes utilizar tus herramientas para proporcionar toda la información posible al cliente.
    
    Si el cliente también quiere ordenar comida, transfiere al agente de comida.
    Si la orden está completa, transfiere a caja para finalizar el pago.
    
    Usa un tono entusiasta y conocedor sobre café.
    """,
    tools=[consultar_menu, verificar_disponibilidad, calcular_precio]
)

# 3. AGENTE DE COMIDA
agente_comida = Agent(
    name="Especialista en Comida",
    model="gpt-4o",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    Eres el especialista en comida del café. Tu trabajo es:
    
    1. Recomendar opciones de comida que complementen sus bebidas
    2. Informar sobre ingredientes y alérgenos
    3. Sugerir los especiales del día y postres
    4. Preguntar sobre preferencias dietéticas
    
    Tienes acceso a herramientas que puedes usar:
    - consultar_menu: Para mostrar opciones de comida
    - verificar_disponibilidad: Para comprobar disponibilidad de productos
    - calcular_precio: Para informar el costo de los productos
    
    Ofrece siempre los productos frescos del día y promociones actuales.
    
    Si el cliente ya ha ordenado su bebida con el barista, o no desea
    bebida, transfiere a caja para finalizar el pago.
    
    Si el cliente necesita ayuda con bebidas, transfiere al barista.
    
    Usa un tono descriptivo y apetitoso al hablar de la comida.
    """,
    tools=[consultar_menu, verificar_disponibilidad, calcular_precio, obtener_promociones]
)

# 4. AGENTE DE CAJA
agente_caja = Agent(
    name="Cajero",
    model="gpt-4o",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    Eres el cajero del café. Tu función es:
    
    1. Confirmar la orden completa con el cliente
    2. Informar sobre el total a pagar
    3. Procesar el pago (efectivo o tarjeta)
    4. Agradecer al cliente y despedirlo amablemente
    
    Tienes acceso a herramientas que puedes usar:
    - calcular_precio: Para calcular el total de la orden
    - generar_recibo: Para proporcionar un recibo detallado
    
    Resume siempre la orden completa antes de indicar el total.
    Pregunta si desean algo más antes de finalizar.
    
    Usa un tono eficiente pero amable.
    """,
    tools=[calcular_precio, generar_recibo]
)

# 1. AGENTE RECEPCIONISTA
agente_recepcionista = Agent(
    name="Recepcionista",
    model="gpt-4o",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    Eres el recepcionista de un café. Tu trabajo es:
    
    1. Saludar amablemente a los clientes
    2. Preguntarles qué desean ordenar
    3. Tomar su nombre para la orden
    4. Transferir al cliente al barista para detalles específicos de bebidas
    
    Tienes acceso a herramientas que puedes usar para proporcionar información:
    - consultar_menu: Para ver el menú completo o por categoría
    - obtener_promociones: Para informar sobre promociones actuales
    
    Si el cliente menciona claramente que quiere comida, transfiérelo directamente
    al agente de comida. Si menciona bebidas, transfiérelo al barista.
    
    Usa un tono amigable y acogedor. Tu objetivo es recoger la intencion del cliente y redireccionarlo con el agente
    correspondiente

    IMPORTANTE: Una vez hayas saludado al cliente, debes dejar de hablar, solamente debes ejecutar las acciones
    necesarias para cumplir con la consulta del cliente
    """,
    handoffs = []
)

# Configurar los handoffs para el agente recepcionista
agente_recepcionista.handoffs = [
    handoff(
        agent=agente_barista,
        on_handoff=transferir_a_barista,
        input_type=OrdenCafe,
        tool_name_override="transferir_a_barista",
        tool_description_override="Transfiere al cliente al barista para ordenar y obtener informacion sobre bebidas"
    ),
    handoff(
        agent=agente_comida,
        on_handoff=transferir_a_comida,
        input_type=OrdenCafe,
        tool_name_override="transferir_a_comida",
        tool_description_override="Transfiere al cliente al especialista en comida"
    )
]

# Configurar los handoffs para el agente barista
agente_barista.handoffs = [
    handoff(
        agent=agente_comida,
        on_handoff=transferir_a_comida,
        input_type=OrdenCafe,
        tool_name_override="transferir_a_comida",
        tool_description_override="Transfiere al cliente al especialista en comida"
    ),
    handoff(
        agent=agente_caja,
        on_handoff=transferir_a_caja,
        input_type=OrdenCafe,
        tool_name_override="transferir_a_caja",
        tool_description_override="Transfiere al cliente a caja para finalizar el pago"
    )
]

# Configurar los handoffs para el agente de comida
agente_comida.handoffs = [
    handoff(
        agent=agente_barista,
        on_handoff=transferir_a_barista,
        input_type=OrdenCafe,
        tool_name_override="transferir_a_barista",
        tool_description_override="Transfiere al cliente al barista para ordenar bebidas"
    ),
    handoff(
        agent=agente_caja,
        on_handoff=transferir_a_caja,
        input_type=OrdenCafe,
        tool_name_override="transferir_a_caja",
        tool_description_override="Transfiere al cliente a caja para finalizar el pago"
    )
]

# Función para iniciar la conversación
async def iniciar_conversacion_cafe(mensaje_cliente):
    print(f"Cliente dice: {mensaje_cliente}")
    print("Iniciando conversación con el recepcionista...")
    
    # Usar Runner para ejecutar el agente como se muestra en la documentación
    resultado = await Runner.run(agente_recepcionista, mensaje_cliente)
    return resultado.final_output

# Función principal
async def main(message):
    result = await iniciar_conversacion_cafe(message)
    print(result)

# Punto de entrada al programa
if __name__ == "__main__":
    # Ejemplo de uso:
    asyncio.run(main("Hola soy Saúl, quiero un café, que tipos de café hay?"))