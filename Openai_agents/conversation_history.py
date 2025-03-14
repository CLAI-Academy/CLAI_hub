from agents import Agent, handoff, RunContextWrapper, Runner
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
import uuid

from main import (
    agente_recepcionista,
    agente_barista,
    agente_comida,
    agente_caja
)

# Clase para representar un mensaje en la conversación
class Mensaje(BaseModel):
    id: str
    remitente: str  # "usuario" o "agente"
    agente_nombre: Optional[str] = None  # Nombre del agente si remitente es "agente"
    contenido: str
    timestamp: float
    metadatos: Dict[str, Any] = {}

# Clase para gestionar el historial de conversación
class HistorialConversacion:
    def __init__(self, session_id=None):
        self.session_id = session_id or str(uuid.uuid4())
        self.mensajes: List[Mensaje] = []
        self.contexto_actual = {}  # Para almacenar información relevante entre mensajes
    
    def agregar_mensaje_usuario(self, contenido: str) -> Mensaje:
        """Añade un mensaje del usuario al historial."""
        import time
        mensaje = Mensaje(
            id=str(uuid.uuid4()),
            remitente="usuario",
            contenido=contenido,
            timestamp=time.time()
        )
        self.mensajes.append(mensaje)
        return mensaje
    
    def agregar_mensaje_agente(self, contenido: str, agente_nombre: str, metadatos: Dict[str, Any] = {}) -> Mensaje:
        """Añade un mensaje de un agente al historial."""
        import time
        mensaje = Mensaje(
            id=str(uuid.uuid4()),
            remitente="agente",
            agente_nombre=agente_nombre,
            contenido=contenido,
            timestamp=time.time(),
            metadatos=metadatos
        )
        self.mensajes.append(mensaje)
        return mensaje
    
    def obtener_ultimo_agente(self) -> Optional[str]:
        """Obtiene el nombre del último agente que envió un mensaje."""
        for mensaje in reversed(self.mensajes):
            if mensaje.remitente == "agente" and mensaje.agente_nombre:
                return mensaje.agente_nombre
        return None
    
    def obtener_historial_formateado(self, num_mensajes: Optional[int] = None) -> str:
        """Obtiene el historial formateado para mostrar."""
        if num_mensajes:
            mensajes = self.mensajes[-num_mensajes:]
        else:
            mensajes = self.mensajes
        
        resultado = "HISTORIAL DE CONVERSACIÓN:\n\n"
        for mensaje in mensajes:
            if mensaje.remitente == "usuario":
                resultado += f"Usuario: {mensaje.contenido}\n\n"
            else:
                resultado += f"{mensaje.agente_nombre}: {mensaje.contenido}\n\n"
        
        return resultado
    
    def actualizar_contexto(self, clave: str, valor: Any):
        """Actualiza el contexto de la conversación."""
        self.contexto_actual[clave] = valor
    
    def obtener_contexto(self, clave: str) -> Any:
        """Obtiene un valor del contexto de la conversación."""
        return self.contexto_actual.get(clave)


def formatear_prompt_con_historial(agent, historial: HistorialConversacion, mensaje_usuario: str) -> str:
    # Agrega las instrucciones del agente
    prompt = agent.instructions.strip() + "\n\n"
    
    # Agrega un encabezado o texto para dar contexto
    prompt += "Historial hasta ahora:\n"
    prompt += historial.obtener_historial_formateado()
    
    # Agrega el nuevo mensaje del usuario
    prompt += f"\nEl usuario dice: {mensaje_usuario}\n"
    
    return prompt

# Función para continuar conversación con el último agente o un agente específico
async def continuar_conversacion(historial: HistorialConversacion, mensaje_usuario: str, agente=None):
    # Añadir mensaje del usuario al historial
    historial.agregar_mensaje_usuario(mensaje_usuario)
    
    # Determinar agente...
    if agente is None:
        ultimo_agente_nombre = historial.obtener_ultimo_agente()
        agente = agente_recepcionista
        if ultimo_agente_nombre:
            if ultimo_agente_nombre == "Recepcionista":
                agente = agente_recepcionista
            elif ultimo_agente_nombre == "Barista":
                agente = agente_barista
            elif ultimo_agente_nombre == "Especialista en Comida":
                agente = agente_comida
            elif ultimo_agente_nombre == "Cajero":
                agente = agente_caja
    
    # En caso extremo de no tener un agente
    if agente is None:
        print("Error: No se pudo determinar un agente válido")
        agente = agente_recepcionista

    print(f"Continuando conversación con agente: {agente.name}")
    
    # Aquí es donde SÍ pasamos todo el historial al agente
    prompt_completo = formatear_prompt_con_historial(agente, historial, mensaje_usuario)
    
    # Ejecutar el agente con el prompt que incluye historial
    resultado = await Runner.run(agente, prompt_completo)
    
    # Añadir respuesta del agente al historial
    historial.agregar_mensaje_agente(
        contenido=resultado.final_output,
        agente_nombre=agente.name,
        metadatos={"run_result": resultado}
    )
    
    return resultado.final_output

# Ejemplo de uso con una conversación simple
async def demo_conversacion():
    # Crear un nuevo historial
    historial = HistorialConversacion()
    
    # Primera interacción
    respuesta = await continuar_conversacion(historial, "Hola, quiero un café")
    print(f"Recepcionista: {respuesta}\n")
    
    # Segunda interacción
    respuesta = await continuar_conversacion(historial, "Quiero un latte grande con leche de almendra")
    print(f"Agente: {respuesta}\n")
    
    # Mostrar historial
    print(historial.obtener_historial_formateado())

agente_recepcionista = agente_recepcionista
agente_barista = agente_barista
agente_comida = agente_comida 
agente_caja = agente_caja
agente_recepcionista,

if __name__ == "__main__":
    print("Este módulo debe ser importado desde el archivo principal")