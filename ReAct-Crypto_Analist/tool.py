import json
from typing import Callable
# --- Utilidades para definir herramientas (tools) ---

def get_fn_signature(fn: Callable) -> dict:
    """
    Genera la firma de una función, incluyendo nombre, descripción y tipos de parámetros.
    """
    fn_signature: dict = {
        "name": fn.__name__,
        "description": fn.__doc__,
        "parameters": {"properties": {}},
    }
    schema = {
        k: {"type": v.__name__}
        for k, v in fn.__annotations__.items()
        if k != "return"
    }
    fn_signature["parameters"]["properties"] = schema
    return fn_signature

def validate_arguments(tool_call: dict, tool_signature: dict) -> dict:
    """
    Valida y convierte los argumentos para que coincidan con los tipos esperados según la firma.
    """
    properties = tool_signature["parameters"]["properties"]
    type_mapping = {
        "int": int,
        "str": str,
        "bool": bool,
        "float": float,
    }
    for arg_name, arg_value in tool_call["arguments"].items():
        expected_type = properties[arg_name].get("type")
        if not isinstance(arg_value, type_mapping[expected_type]):
            tool_call["arguments"][arg_name] = type_mapping[expected_type](arg_value)
    return tool_call

class Tool:
    """
    Representa una herramienta que envuelve una función y su firma.
    """
    def __init__(self, name: str, fn: Callable, fn_signature: str):
        self.name = name
        self.fn = fn
        self.fn_signature = fn_signature

    def __str__(self):
        return self.fn_signature

    def run(self, **kwargs):
        return self.fn(**kwargs)

def tool(fn: Callable):
    """
    Decorador que convierte una función en una herramienta (Tool).
    """
    def wrapper():
        fn_signature = get_fn_signature(fn)
        return Tool(
            name=fn_signature.get("name"),
            fn=fn,
            fn_signature=json.dumps(fn_signature)
        )
    return wrapper()

