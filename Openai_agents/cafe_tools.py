from agents import function_tool, RunContextWrapper
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Datos hardcodeados para usar en nuestras herramientas
MENU_CAFE = {
    "bebidas": {
        "café": [
            {"nombre": "Espresso", "tamaños": ["pequeño", "doble"], "precios": {"pequeño": 1.50, "doble": 2.50}},
            {"nombre": "Americano", "tamaños": ["pequeño", "mediano", "grande"], "precios": {"pequeño": 2.00, "mediano": 2.50, "grande": 3.00}},
            {"nombre": "Latte", "tamaños": ["pequeño", "mediano", "grande"], "precios": {"pequeño": 3.00, "mediano": 3.50, "grande": 4.00}},
            {"nombre": "Cappuccino", "tamaños": ["pequeño", "mediano", "grande"], "precios": {"pequeño": 3.00, "mediano": 3.50, "grande": 4.00}},
            {"nombre": "Mocha", "tamaños": ["pequeño", "mediano", "grande"], "precios": {"pequeño": 3.50, "mediano": 4.00, "grande": 4.50}}
        ],
        "té": [
            {"nombre": "Té Verde", "tamaños": ["pequeño", "mediano", "grande"], "precios": {"pequeño": 2.00, "mediano": 2.50, "grande": 3.00}},
            {"nombre": "Té Negro", "tamaños": ["pequeño", "mediano", "grande"], "precios": {"pequeño": 2.00, "mediano": 2.50, "grande": 3.00}},
            {"nombre": "Té Chai", "tamaños": ["pequeño", "mediano", "grande"], "precios": {"pequeño": 3.00, "mediano": 3.50, "grande": 4.00}}
        ]
    },
    "comida": {
        "pasteles": [
            {"nombre": "Croissant", "precio": 2.50},
            {"nombre": "Muffin de Arándanos", "precio": 3.00},
            {"nombre": "Brownie", "precio": 3.50},
            {"nombre": "Tarta de Manzana", "precio": 4.00}
        ],
        "sandwiches": [
            {"nombre": "Sandwich de Jamón y Queso", "precio": 5.50},
            {"nombre": "Sandwich Vegetal", "precio": 5.00},
            {"nombre": "Wrap de Pollo", "precio": 6.00}
        ]
    },
    "extras": [
        {"nombre": "Leche de Almendra", "precio": 0.50},
        {"nombre": "Leche de Avena", "precio": 0.50},
        {"nombre": "Sirope de Vainilla", "precio": 0.30},
        {"nombre": "Sirope de Caramelo", "precio": 0.30},
        {"nombre": "Shot Extra de Espresso", "precio": 1.00},
        {"nombre": "Crema Batida", "precio": 0.50}
    ]
}

DISPONIBILIDAD = {
    "café": {
        "Espresso": True,
        "Americano": True,
        "Latte": True,
        "Cappuccino": True,
        "Mocha": True
    },
    "té": {
        "Té Verde": True,
        "Té Negro": True,
        "Té Chai": False  # Ejemplo de producto no disponible
    },
    "pasteles": {
        "Croissant": True,
        "Muffin de Arándanos": True,
        "Brownie": False,  # Ejemplo de producto no disponible
        "Tarta de Manzana": True
    },
    "sandwiches": {
        "Sandwich de Jamón y Queso": True,
        "Sandwich Vegetal": True,
        "Wrap de Pollo": True
    }
}

PROMOCIONES = [
    {
        "nombre": "Combo Desayuno",
        "descripcion": "Cualquier café mediano con un croissant",
        "precio": 4.50,
        "descuento": "Ahorra $1.00"
    },
    {
        "nombre": "Happy Hour",
        "descripcion": "Todos los cafés a mitad de precio de 3pm a 5pm",
        "condiciones": "Solo en tienda, no válido para pedidos para llevar"
    },
    {
        "nombre": "Café del día",
        "descripcion": "Americano grande por el precio de un mediano",
        "disponible_hoy": True
    }
]

# Herramientas para consultar información

@function_tool
async def consultar_menu(ctx: RunContextWrapper[Any], categoria: Optional[str] = None) -> str:
    """Consulta el menú del café.
    
    Args:
        categoria: Categoría específica a consultar. Puede ser 'bebidas', 'comida', o 'extras'.
                 Si no se especifica, se devuelve todo el menú.
    """
    if categoria:
        if categoria == "bebidas":
            return f"MENÚ DE BEBIDAS:\n{format_menu_items(MENU_CAFE['bebidas'])}"
        elif categoria == "comida":
            return f"MENÚ DE COMIDA:\n{format_menu_items(MENU_CAFE['comida'])}"
        elif categoria == "extras":
            extras_str = "\n".join([f"- {extra['nombre']}: ${extra['precio']:.2f}" for extra in MENU_CAFE['extras']])
            return f"EXTRAS DISPONIBLES:\n{extras_str}"
        else:
            return f"Categoría '{categoria}' no encontrada. Las categorías disponibles son 'bebidas', 'comida', y 'extras'."
    else:
        # Devolver todo el menú
        return f"""MENÚ COMPLETO DEL CAFÉ:
        
BEBIDAS:
{format_menu_items(MENU_CAFE['bebidas'])}

COMIDA:
{format_menu_items(MENU_CAFE['comida'])}

EXTRAS:
{", ".join([extra['nombre'] for extra in MENU_CAFE['extras']])}
"""

def format_menu_items(items_dict):
    result = []
    for category, items in items_dict.items():
        result.append(f"\n{category.upper()}:")
        for item in items:
            if "tamaños" in item:
                tamaños_precio = ", ".join([f"{size} ${item['precios'][size]:.2f}" for size in item['tamaños']])
                result.append(f"- {item['nombre']} ({tamaños_precio})")
            else:
                result.append(f"- {item['nombre']}: ${item['precio']:.2f}")
    return "\n".join(result)

@function_tool
async def verificar_disponibilidad(ctx: RunContextWrapper[Any], producto: str, categoria: Optional[str] = None) -> str:
    """Verifica si un producto está disponible.
    
    Args:
        producto: Nombre del producto a verificar.
        categoria: Categoría del producto (café, té, pasteles, sandwiches).
                  Si no se especifica, se busca en todas las categorías.
    """
    if categoria:
        if categoria in DISPONIBILIDAD:
            if producto in DISPONIBILIDAD[categoria]:
                disponible = DISPONIBILIDAD[categoria][producto]
                return f"{producto} {'está disponible' if disponible else 'NO está disponible actualmente'}"
            else:
                return f"No encontramos '{producto}' en nuestra categoría de {categoria}"
        else:
            return f"Categoría '{categoria}' no válida. Las categorías son: {', '.join(DISPONIBILIDAD.keys())}"
    else:
        # Buscar en todas las categorías
        for cat, productos in DISPONIBILIDAD.items():
            if producto in productos:
                disponible = DISPONIBILIDAD[cat][producto]
                return f"{producto} {'está disponible' if disponible else 'NO está disponible actualmente'}"
        
        return f"No encontramos '{producto}' en nuestro inventario"

@function_tool
async def obtener_promociones(ctx: RunContextWrapper[Any], solo_disponibles_hoy: Optional[bool] = None) -> str:
    # Dentro de la función, manejar el caso None
    if solo_disponibles_hoy is None:
        solo_disponibles_hoy = False

    if solo_disponibles_hoy:
        promos_filtradas = [p for p in PROMOCIONES if p.get("disponible_hoy", False)]
    else:
        promos_filtradas = PROMOCIONES
    
    if not promos_filtradas:
        return "No hay promociones disponibles actualmente"
    
    result = "PROMOCIONES DISPONIBLES:\n\n"
    for promo in promos_filtradas:
        result += f"- {promo['nombre']}: {promo['descripcion']}\n"
        if "descuento" in promo:
            result += f"  {promo['descuento']}\n"
        if "condiciones" in promo:
            result += f"  Condiciones: {promo['condiciones']}\n"
        result += "\n"
    
    return result

@function_tool
async def calcular_precio(ctx: RunContextWrapper[Any], bebida: Optional[str] = None, tamaño: Optional[str] = None, 
                         extras: Optional[List[str]] = None, comida: Optional[str] = None) -> str:
    """Calcula el precio total de una orden.
    
    Args:
        bebida: Nombre de la bebida.
        tamaño: Tamaño de la bebida (pequeño, mediano, grande, doble).
        extras: Lista de extras a añadir.
        comida: Nombre del producto de comida.
    """
    precio_total = 0.0
    desglose = []
    
    # Calcular precio de bebida
    if bebida and tamaño:
        encontrado = False
        for categoria, items in MENU_CAFE['bebidas'].items():
            for item in items:
                if item['nombre'].lower() == bebida.lower():
                    if tamaño.lower() in [t.lower() for t in item['tamaños']]:
                        precio_bebida = item['precios'][tamaño.lower()]
                        precio_total += precio_bebida
                        desglose.append(f"{bebida} {tamaño}: ${precio_bebida:.2f}")
                        encontrado = True
                        break
            if encontrado:
                break
        
        if not encontrado:
            return f"No encontramos la combinación de {bebida} en tamaño {tamaño}"
    
    # Calcular precio de extras
    if extras:
        for extra_nombre in extras:
            encontrado = False
            for extra in MENU_CAFE['extras']:
                if extra['nombre'].lower() == extra_nombre.lower():
                    precio_total += extra['precio']
                    desglose.append(f"Extra {extra['nombre']}: ${extra['precio']:.2f}")
                    encontrado = True
                    break
            
            if not encontrado:
                return f"No encontramos el extra '{extra_nombre}'"
    
    # Calcular precio de comida
    if comida:
        encontrado = False
        for categoria, items in MENU_CAFE['comida'].items():
            for item in items:
                if item['nombre'].lower() == comida.lower():
                    precio_comida = item['precio']
                    precio_total += precio_comida
                    desglose.append(f"{comida}: ${precio_comida:.2f}")
                    encontrado = True
                    break
            if encontrado:
                break
        
        if not encontrado:
            return f"No encontramos '{comida}' en nuestro menú de comida"
    
    # Verificar si aplica alguna promoción
    descuento_aplicado = False
    if bebida and comida:
        if bebida.lower() in ["americano", "latte", "cappuccino"] and tamaño.lower() == "mediano" and comida.lower() == "croissant":
            precio_con_descuento = 4.50
            ahorro = precio_total - precio_con_descuento
            desglose.append(f"Promoción 'Combo Desayuno' aplicada: -${ahorro:.2f}")
            precio_total = precio_con_descuento
            descuento_aplicado = True
    
    # Formatear respuesta
    if desglose:
        resultado = "DESGLOSE DE PRECIO:\n" + "\n".join(desglose) + f"\n\nTOTAL: ${precio_total:.2f}"
        if descuento_aplicado:
            resultado += " (incluye descuento por promoción)"
        return resultado
    else:
        return "No se ha especificado ningún producto para calcular el precio"

# Esta clase podría usarse si prefieres una herramienta más compleja que utilice Pydantic
class OrdenCompleta(BaseModel):
    bebida: Optional[str] = None
    tamaño: Optional[str] = None
    extras: List[str] = []
    comida: Optional[str] = None
    para_llevar: bool = False
    nombre_cliente: str = ""

@function_tool
async def generar_recibo(
    ctx: RunContextWrapper[Any],
    bebida: str,
    tamaño: str,
    nombre_cliente: str,
    para_llevar: bool,
    comida: Optional[str] = None
) -> str:
    """Genera un recibo para la orden.
    
    Args:
        bebida: Nombre de la bebida ordenada.
        tamaño: Tamaño de la bebida (pequeño, mediano, grande).
        nombre_cliente: Nombre del cliente.
        para_llevar: Si la orden es para llevar (True) o consumir en local (False).
        comida: Nombre del producto de comida (opcional).
    """
    # Crear el recibo formateado
    recibo = f"""
=================================
        CAFÉ RECIBO
=================================
Cliente: {nombre_cliente}
Modalidad: {'Para llevar' if para_llevar else 'Consumo en local'}
---------------------------------
Bebida: {bebida} ({tamaño})
"""
    
    if comida:
        recibo += f"Comida: {comida}\n"
    
    # Simular un cálculo de precio
    precio_bebida = 0
    if tamaño == "pequeño":
        precio_bebida = 2.50
    elif tamaño == "mediano":
        precio_bebida = 3.00
    else:  # grande
        precio_bebida = 3.50
        
    precio_comida = 4.00 if comida else 0
    total = precio_bebida + precio_comida
    
    recibo += f"""
---------------------------------
TOTAL: ${total:.2f}
=================================
¡Gracias por su visita!
"""
    return recibo