"""
GABBIANI MASTER AI v7 — Core Engine
Modelos, Extracción, Visión IA, Reglas, Validación, Auditoría
"""
import hashlib
import io
import json
import re
import time
import logging
import typing_extensions as typing
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger("GABBIANI")

# ══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════
class PiezaSchema(typing.TypedDict):
    id: str
    nombre: str
    largo: float
    ancho: float
    espesor: float
    material: str
    cantidad: int
    notas: str

SCHEMA_VERTEX = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "id": {"type": "STRING"}, "nombre": {"type": "STRING"},
            "largo": {"type": "NUMBER"}, "ancho": {"type": "NUMBER"},
            "espesor": {"type": "NUMBER"}, "material": {"type": "STRING"},
            "cantidad": {"type": "INTEGER"}, "notas": {"type": "STRING"}
        },
        "required": ["id","nombre","largo","ancho","espesor","material",
                      "cantidad","notas"]
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# ENUMS + TRAZABILIDAD
# ══════════════════════════════════════════════════════════════════════════════
class OrigenDato(Enum):
    VECTOR_PDF = "PDF_VECTORIAL"
    VISION_IA = "GEMINI_IA"
    REGLA_MOTOR = "REGLA_TALLER"

class NivelConfianza(Enum):
    DETERMINISTA = "DET"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"

@dataclass
class CampoTrazable:
    valor: object
    valor_original: object = None
    origen: OrigenDato = OrigenDato.VISION_IA
    confianza: NivelConfianza = NivelConfianza.MEDIA
    regla_aplicada: str = ""
    def fue_modificado(self) -> bool:
        return self.valor_original is not None and self.valor != self.valor_original

@dataclass
class PiezaIndustrial:
    id: str
    nombre: str
    largo: CampoTrazable
    ancho: CampoTrazable
    espesor: CampoTrazable
    material: CampoTrazable
    cantidad: CampoTrazable
    notas: str = ""
    pagina_origen: int = 0
    hash_pieza: str = ""
    alertas: list = field(default_factory=list)

    def __post_init__(self):
        c = f"{self.nombre}_{self.largo.valor}_{self.ancho.valor}_{self.material.valor}"
        self.hash_pieza = hashlib.md5(c.encode()).hexdigest()[:10]

    def to_row_debug(self) -> dict:
        return {
            "ID": self.id, "Nombre": self.nombre,
            "Largo_IA": self.largo.valor_original or self.largo.valor,
            "Largo_Corte": self.largo.valor,
            "Ancho_IA": self.ancho.valor_original or self.ancho.valor,
            "Ancho_Corte": self.ancho.valor,
            "Espesor": self.espesor.valor, "Material": self.material.valor,
            "Cantidad": self.cantidad.valor,
            "Confianza": self._conf_global().value,
            "Regla": self._reglas_str(),
            "Notas": self.notas, "Pág": self.pagina_origen
        }

    def to_display_row(self) -> dict:
        return {
            "Nombre": self.nombre,
            "Largo": self.largo.valor, "Ancho": self.ancho.valor,
            "Espesor": self.espesor.valor, "Material": self.material.valor,
            "Cantidad": self.cantidad.valor, "Notas": self.notas
        }

    def to_csv_row(self) -> dict:
        def format_dim(val):
            v = float(val)
            return int(v) if v.is_integer() else round(v, 2)
        return {
            "Codigo": self.nombre.upper(),
            "Descripcion": self.notas.upper() if self.notas else "PROYECTO",
            "Longitud": format_dim(self.largo.valor),
            "Ancho": format_dim(self.ancho.valor),
            "Espesor": format_dim(self.espesor.valor),
            "Color": self.material.valor.upper(),
            "Solicitados": int(self.cantidad.valor),
            "Veta": 1, "Var. Cantidad": 0, "M2": ""
        }

    def _conf_global(self) -> NivelConfianza:
        ns = [self.largo.confianza, self.ancho.confianza,
              self.material.confianza, self.cantidad.confianza]
        if NivelConfianza.BAJA in ns: return NivelConfianza.BAJA
        if NivelConfianza.MEDIA in ns: return NivelConfianza.MEDIA
        return NivelConfianza.ALTA

    def _reglas_str(self) -> str:
        r = [c.regla_aplicada for c in
             [self.largo,self.ancho,self.espesor,self.cantidad] if c.regla_aplicada]
        return " | ".join(r) if r else "Corte Neto"

# ══════════════════════════════════════════════════════════════════════════════
# PERFILES
# ══════════════════════════════════════════════════════════════════════════════
_BASE_PERFIL = {
    "ancho_pinza": 70, "ancho_seguro": 130, "margen_sandwich": 60,
    "margen_cnc": 10, "largo_max": 2850, "ancho_max": 2100, "kerf_mm": 4.2,
    "espesores_validos": [3,4,5,6,8,10,12,15,16,18,19,22,25,30,38,40,50],
    "cajon_qube": False, "descuento_qube": 0,
    "canteado_auto": False, "espesor_canto_mm": 2.0,
    "regla_puertas_16": False,
    "lista_negra": ["PINO","PINTURA","CANTO","TORNILLO","HERRAJE",
                    "PERFIL LED","CATALIZADOR","COLA","SILICONA","TIRADOR","BISAGRA"],
    "alias_material": {
        "BLANCO":"W980","CAOLIN":"W980","W980":"W980","WHITE":"W980",
        "ELEGANCE":"M6317","M6317":"M6317","ROBLE":"M6317","OAK":"M6317",
        "FONDO":"16B","OCULTO":"16B","BACK":"16B",
        "KRION":"KRION (CORTE ESPECIAL)",
        "ALUMINIO":"METAL (NO CORTAR)","METAL":"METAL (NO CORTAR)",
        "ACERO":"METAL (NO CORTAR)"}
}

PERFILES = {
    "ESTÁNDAR": {**_BASE_PERFIL, "display": "Estándar (Sin reglas de cajón)"},
    "APOTHEKA": {**_BASE_PERFIL, "display": "Apotheka / Ilusion (Cajones QUBE)",
                 "cajon_qube": True, "descuento_qube": 59},
    "CANTEADO_AUTO": {**_BASE_PERFIL, "display": "Con descuento de canteado automático",
                      "canteado_auto": True},
    "GRADELES_16": {**_BASE_PERFIL, "display": "Armarios Gradeles (Puertas 16mm)",
                    "espesores_validos": [10, 16, 19, 30],
                    "regla_puertas_16": True,
                    "lista_negra": ["PINO","PINTURA","CANTO","TORNILLO","HERRAJE"],
                    "alias_material": {
                        "BLANCO": "AVA", "AVA": "AVA", "WHITE": "AVA",
                        "FONDO": "10MM", "OCULTO": "10MM",
                        "ROBLE": "M6317", "ELEGANCE": "M6317",
                        "KRION": "KRION (CORTE ESPECIAL)",
                        "ALUMINIO": "METAL (NO CORTAR)", "METAL": "METAL (NO CORTAR)"}},
}

# ══════════════════════════════════════════════════════════════════════════════
# VALIDADOR FÍSICO
# ══════════════════════════════════════════════════════════════════════════════
class ValidadorFisico:
    @classmethod
    def validar(cls, p: dict, perfil: dict) -> tuple:
        al, conf = [], NivelConfianza.ALTA
        l,a,e,n,c = (p.get("largo",0), p.get("ancho",0), p.get("espesor",19),
                      p.get("nombre","?"), p.get("cantidad",1))
        if l>3660: al.append(f"🚫 {n}: Largo {l}mm > máx 3660"); conf=NivelConfianza.BAJA
        if a>2100: al.append(f"🚫 {n}: Ancho {a}mm > máx 2100"); conf=NivelConfianza.BAJA
        if 0<l<50: al.append(f"⚠️ {n}: Largo {l}mm sospechoso"); conf=NivelConfianza.MEDIA
        if 0<a<15: al.append(f"⚠️ {n}: Ancho {a}mm bajo mínimo"); conf=NivelConfianza.MEDIA
        if e not in perfil.get("espesores_validos",[19]):
            ce = min(perfil["espesores_validos"], key=lambda x:abs(x-e))
            al.append(f"⚠️ {n}: Espesor {e}mm no comercial (¿{ce}?)"); conf=NivelConfianza.MEDIA
        if a>0 and l/a>30: al.append(f"⚠️ {n}: Ratio L/A={l/a:.0f}:1 extremo"); conf=NivelConfianza.MEDIA
        if c>50: al.append(f"⚠️ {n}: Cantidad {c} inusual"); conf=NivelConfianza.MEDIA
        if c<=0: return False,al,NivelConfianza.BAJA
        return conf!=NivelConfianza.BAJA, al, conf

# ══════════════════════════════════════════════════════════════════════════════
# DATOS DE PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class DatosPagina:
    num: int
    imagen: Image.Image
    texto: str
    tablas: list
    tiene_texto: bool
    tiene_tablas: bool

# ══════════════════════════════════════════════════════════════════════════════
# EXTRACTOR VECTORIAL
# ══════════════════════════════════════════════════════════════════════════════
class ExtractorVectorial:
    MAPEO = {
        "nombre": ["nombre","pieza","descripcion","desc","name","part",
                    "elemento","denominación","denominacion"],
        "largo":  ["largo","longitud","length","l","long","alto","altura"],
        "ancho":  ["ancho","anchura","width","w","a","prof","profundidad"],
        "espesor":["espesor","grosor","thickness","e","esp","th","grueso"],
        "cantidad":["cantidad","cant","qty","quantity","ud","uds","pcs",
                     "n","nº","num"],
        "material":["material","mat","acabado","color","ref","referencia"]
    }

    @classmethod
    def parsear_tablas(cls, tablas: list, num_pag: int) -> list:
        for df in tablas:
            if len(df) < 2 or len(df.columns) < 3: continue
            piezas = cls._parsear_df(df, num_pag)
            if piezas: return piezas
        return []

    @classmethod
    def _parsear_df(cls, df, num_pag):
        headers = [str(h).strip().lower() for h in df.columns]
        cmap = {}
        for campo, vars_ in cls.MAPEO.items():
            for idx, h in enumerate(headers):
                if any(v in h for v in vars_):
                    cmap[campo] = idx; break
        if "largo" not in cmap or "ancho" not in cmap: return []
        piezas = []
        for ri, row in df.iterrows():
            try:
                vals = list(row)
                nombre = str(vals[cmap["nombre"]]).strip() if "nombre" in cmap else f"Pieza_{ri}"
                lr = re.search(r'(\d+\.?\d*)', str(vals[cmap["largo"]]).replace(",","."))
                ar = re.search(r'(\d+\.?\d*)', str(vals[cmap["ancho"]]).replace(",","."))
                if not lr or not ar: continue
                largo, ancho = float(lr.group(1)), float(ar.group(1))
                if largo==0 and ancho==0: continue
                espesor = 19.0
                if "espesor" in cmap:
                    em = re.search(r'(\d+\.?\d*)', str(vals[cmap["espesor"]]).replace(",","."))
                    if em: espesor = float(em.group(1))
                cantidad = 1
                if "cantidad" in cmap:
                    cm = re.search(r'(\d+)', str(vals[cmap["cantidad"]]))
                    if cm: cantidad = int(cm.group(1))
                material = str(vals[cmap["material"]]).strip() if "material" in cmap else ""
                piezas.append({
                    "id":f"V{num_pag}_{ri}","nombre":nombre,"largo":largo,"ancho":ancho,
                    "espesor":espesor,"cantidad":cantidad,"material":material,"notas":""})
            except (ValueError,IndexError,TypeError): continue
        return piezas

# ══════════════════════════════════════════════════════════════════════════════
# MOTOR VISIÓN IA
# ══════════════════════════════════════════════════════════════════════════════
MAX_TEXTO_VECTORIAL = 5000

PROMPT_BASE = """Eres técnico de oficina técnica experto en despieces de mobiliario industrial.

INSTRUCCIONES ESTRICTAS:
1. Extrae TODAS las piezas de madera/tablero visibles.
2. Las cotas principales más grandes = largo y ancho en mm.
3. Si NO puedes leer una medida con certeza, pon 0.
4. Espesor por defecto: 19mm. Cantidad por defecto: 1.
5. NO inventes medidas. Si no las ves, pon 0.
6. NO incluyas herrajes, tornillos, cantos, pinturas, accesorios.
7. Si hay tabla con columnas (ID/DESCRIPCION/UDS) extrae TODAS las filas.
8. En notas incluye: si dice Qube, Pegar, Doble, Radio, Krion, etc.
"""

def _preparar_imagen(img: Image.Image) -> bytes:
    g = img.convert("L")
    c = ImageEnhance.Contrast(g).enhance(1.5)
    s = c.filter(ImageFilter.SHARPEN).convert("RGB")
    buf = io.BytesIO(); s.save(buf, format="PNG"); buf.seek(0)
    return buf.getvalue()


class MotorVision:
    def __init__(self, backend, model_name, secrets_dict):
        """
        secrets_dict: diccionario con las claves necesarias
        (evita acoplar con st.secrets)
        """
        self.backend = backend
        self.model_name = model_name
        if self.backend == "vertex_ai":
            self._init_vertex(secrets_dict)
        else:
            self._init_google_ai(secrets_dict)
        logger.info(f"MotorVision: backend={self.backend}, model={model_name}")

    def _init_vertex(self, secrets):
        import vertexai
        from google.oauth2 import service_account
        from vertexai.generative_models import GenerativeModel
        creds = service_account.Credentials.from_service_account_info(
            secrets["gcp_service_account"])
        vertexai.init(project=secrets["GCP_PROJECT"],
                      location=secrets.get("GCP_LOCATION","europe-west1"),
                      credentials=creds)
        self._model = GenerativeModel(self.model_name)

    def _init_google_ai(self, secrets):
        import google.generativeai as genai
        genai.configure(api_key=secrets["GEMINI_API_KEY"])
        self._genai = genai
        self._model = genai.GenerativeModel(self.model_name)

    def analizar(self, imagen: Image.Image, texto_vectorial: str = "",
                 max_intentos: int = 3) -> list:
        img_bytes = _preparar_imagen(imagen)
        prompt = PROMPT_BASE
        if texto_vectorial and texto_vectorial.strip():
            prompt += f"""
FUENTE SECUNDARIA — TEXTO VECTORIAL EXACTO DEL PDF:
'''
{texto_vectorial[:MAX_TEXTO_VECTORIAL]}
'''
Usa este texto para verificar nombres, cantidades y medidas.
Si hay discrepancia entre texto e imagen, prioriza el texto vectorial.
"""
        texto_respuesta = None
        for intento in range(max_intentos):
            try:
                if self.backend == "vertex_ai":
                    texto_respuesta = self._call_vertex(prompt, img_bytes)
                else:
                    texto_respuesta = self._call_google_ai(prompt, img_bytes)
                datos = json.loads(texto_respuesta)
                if isinstance(datos, dict): datos = [datos]
                logger.info(f"  ✓ IA: {len(datos)} piezas (intento {intento+1})")
                return datos
            except json.JSONDecodeError:
                logger.warning(f"  ⚠ JSON inválido (intento {intento+1})")
                if intento < max_intentos-1: time.sleep(2**intento); continue
                try: return self._fallback_fix(texto_respuesta or "")
                except Exception: return [{"error":"JSON irreparable"}]
            except Exception as e:
                logger.error(f"  ✗ Error API (intento {intento+1}): {e}")
                if intento < max_intentos-1: time.sleep(2**intento); continue
                return [{"error": str(e)}]
        return []

    def _call_vertex(self, prompt, img_bytes):
        from vertexai.generative_models import Part, GenerationConfig
        img_part = Part.from_data(data=img_bytes, mime_type="image/png")
        resp = self._model.generate_content(
            [prompt, img_part],
            generation_config=GenerationConfig(
                temperature=0.1, response_mime_type="application/json",
                response_schema=SCHEMA_VERTEX))
        return resp.text

    def _call_google_ai(self, prompt, img_bytes):
        resp = self._model.generate_content(
            [prompt, {"mime_type":"image/png","data":img_bytes}],
            generation_config=self._genai.GenerationConfig(
                temperature=0.1, response_mime_type="application/json",
                response_schema=list[PiezaSchema]))
        return resp.text

    def _fallback_fix(self, texto_roto):
        pf = f"Corrige este JSON y devuelve SOLO el array JSON válido:\n{texto_roto}"
        if self.backend == "vertex_ai":
            from vertexai.generative_models import GenerationConfig
            resp = self._model.generate_content([pf],
                generation_config=GenerationConfig(
                    temperature=0.0, response_mime_type="application/json",
                    response_schema=SCHEMA_VERTEX))
        else:
            resp = self._model.generate_content([pf],
                generation_config=self._genai.GenerationConfig(
                    temperature=0.0, response_mime_type="application/json",
                    response_schema=list[PiezaSchema]))
        d = json.loads(resp.text)
        return [d] if isinstance(d,dict) else d

# ══════════════════════════════════════════════════════════════════════════════
# CEREBRO OPERARIO V5
# ══════════════════════════════════════════════════════════════════════════════
class CerebroOperarioV5:
    def __init__(self, perfil_nombre: str):
        self.p = PERFILES.get(perfil_nombre, PERFILES["ESTÁNDAR"])
        self.hash_vistos = {}

    def normalizar_material(self, texto):
        mat = str(texto).upper().strip()
        for k,v in self.p["alias_material"].items():
            if k in mat: return v, NivelConfianza.ALTA
        return (texto, NivelConfianza.MEDIA) if mat and len(mat)>1 else ("SIN MATERIAL", NivelConfianza.BAJA)

    def es_basura(self, nombre, material):
        t = f"{nombre} {material}".upper()
        return any(x in t for x in self.p["lista_negra"])

    def procesar(self, datos, num_pag, origen):
        piezas, alertas = [], []
        for idx, raw in enumerate(datos):
            nombre = raw.get("nombre","Sin Nombre")
            mat_raw = raw.get("material","")
            if self.es_basura(nombre, mat_raw): continue
            try:
                largo=float(raw.get("largo",0)); ancho=float(raw.get("ancho",0))
                espesor=float(raw.get("espesor",19)); cantidad=int(float(raw.get("cantidad",1)))
            except (ValueError,TypeError):
                alertas.append(f"⚠️ Pág {num_pag}: '{nombre}' no numérico"); continue
            if largo==0 and ancho==0: continue
            if largo<ancho: largo,ancho=ancho,largo
            material,conf_mat = self.normalizar_material(mat_raw)
            notas = str(raw.get("notas","")).upper()
            conf_dim = NivelConfianza.DETERMINISTA if origen==OrigenDato.VECTOR_PDF else NivelConfianza.MEDIA
            id_p = f"P{num_pag}_{raw.get('id',idx)}"
            pieza = PiezaIndustrial(
                id=id_p, nombre=nombre,
                largo=CampoTrazable(largo,origen=origen,confianza=conf_dim),
                ancho=CampoTrazable(ancho,origen=origen,confianza=conf_dim),
                espesor=CampoTrazable(espesor,origen=origen,confianza=conf_dim),
                material=CampoTrazable(material,valor_original=mat_raw,origen=origen,confianza=conf_mat),
                cantidad=CampoTrazable(cantidad,origen=origen,confianza=conf_dim),
                notas=notas, pagina_origen=num_pag)

            nombre_up = nombre.upper()
            nombre_norm = nombre_up.replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")

            # R1: Sándwich
            if any(k in notas for k in ["PEGAR","DOBLE","APLACAR","SANDWICH"]):
                m=self.p["margen_sandwich"]
                pieza.largo.valor_original=largo; pieza.largo.valor+=m; pieza.largo.regla_aplicada=f"Sándwich +{m}"
                pieza.ancho.valor_original=ancho; pieza.ancho.valor+=m; pieza.ancho.regla_aplicada=f"Sándwich +{m}"
                if "DOBLE" in notas and cantidad==1:
                    pieza.cantidad.valor_original=1; pieza.cantidad.valor=2; pieza.cantidad.regla_aplicada="Sándwich x2"
                alertas.append(f"🥪 Pág {num_pag} — {nombre}: Sándwich +{m}mm")

            # R2: Cajón Qube
            if self.p["cajon_qube"] and ("CAJÓN" in nombre_up or "CAJON" in nombre_up) and "QUBE" in notas:
                d=self.p["descuento_qube"]; lf=280 if "300" in notas else 480; af=pieza.largo.valor-d
                fondo = PiezaIndustrial(
                    id=f"{id_p}_F", nombre=f"Fondo {nombre}",
                    largo=CampoTrazable(af,origen=OrigenDato.REGLA_MOTOR,confianza=NivelConfianza.ALTA,regla_aplicada=f"Qube -{d}"),
                    ancho=CampoTrazable(lf,origen=OrigenDato.REGLA_MOTOR,confianza=NivelConfianza.ALTA),
                    espesor=CampoTrazable(16,origen=OrigenDato.REGLA_MOTOR,confianza=NivelConfianza.DETERMINISTA),
                    material=CampoTrazable("16B",origen=OrigenDato.REGLA_MOTOR,confianza=NivelConfianza.DETERMINISTA),
                    cantidad=CampoTrazable(pieza.cantidad.valor,origen=OrigenDato.REGLA_MOTOR,confianza=NivelConfianza.ALTA),
                    notas="AUTO: Fondo Qube", pagina_origen=num_pag)
                piezas.append(fondo); pieza.nombre=f"Frente {nombre}"
                nombre_up = pieza.nombre.upper()
                nombre_norm = nombre_up.replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")
                alertas.append(f"✨ Pág {num_pag} — {nombre}: Fondo Qube generado")

            # R3: Gradeles 16mm
            if self.p.get("regla_puertas_16"):
                claves_16 = ["PUERTA", "ESTANTE", "TAPETA", "FRENTE"]
                exclusiones_16 = ["CAJON", "CAJÓN", "ESTRUCTURA", "LATERAL"]
                if any(k in nombre_up for k in claves_16) and not any(k in nombre_up for k in exclusiones_16):
                    if pieza.espesor.valor != 16:
                        pieza.espesor.valor_original = pieza.espesor.valor
                        pieza.espesor.valor = 16
                        pieza.espesor.regla_aplicada = "Gradel (Forzado 16mm)"
                        pieza.espesor.confianza = NivelConfianza.ALTA
                        alertas.append(f"🗜️ Pág {num_pag} — {nombre}: Espesor forzado a 16mm")

            # R4: Pilastras / Cierres
            claves_pilastra = ["CIERRE", "PILASTRA", "FORRO"]
            if any(k in nombre_norm for k in claves_pilastra) and pieza.ancho.valor < 150:
                pieza.ancho.valor_original = pieza.ancho.valor
                pieza.ancho.valor = 200
                pieza.ancho.regla_aplicada = "Pilastra/L (Forzado 200mm)"
                pieza.ancho.confianza = NivelConfianza.ALTA
                alertas.append(f"📐 Pág {num_pag} — {nombre}: Ensanchado a 200mm para plegado en L")

            # R5: Veta Continua
            if "FRENTE" in nombre_norm and "CAJON" in nombre_norm and pieza.largo.valor < 400:
                pieza.largo.valor_original = pieza.largo.valor
                pieza.largo.valor = 1000
                pieza.largo.regla_aplicada = "Veta Continua (Bloque 1000mm)"
                pieza.largo.confianza = NivelConfianza.ALTA
                pieza.notas = (pieza.notas + " VETA CONTINUA").strip()
                alertas.append(f"🪵 Pág {num_pag} — {nombre}: Bloque 1000mm para veta continua")

            # R6: CNC / Curva
            if any(k in notas for k in ["RADIO","CURVA"]) or (notas.startswith("R") and any(c.isdigit() for c in notas)):
                mc=self.p["margen_cnc"]
                pieza.largo.valor_original=pieza.largo.valor_original or pieza.largo.valor; pieza.largo.valor+=mc
                pieza.largo.regla_aplicada=((pieza.largo.regla_aplicada+" ") if pieza.largo.regla_aplicada else "")+f"CNC +{mc}"
                pieza.ancho.valor_original=pieza.ancho.valor_original or pieza.ancho.valor; pieza.ancho.valor+=mc
                pieza.ancho.regla_aplicada=((pieza.ancho.regla_aplicada+" ") if pieza.ancho.regla_aplicada else "")+f"CNC +{mc}"

            # R7: 2x1
            if pieza.ancho.valor<50 and pieza.cantidad.valor>=2 and pieza.cantidad.valor%2==0:
                pieza.ancho.valor_original=pieza.ancho.valor; pieza.ancho.valor=self.p["ancho_seguro"]; pieza.ancho.regla_aplicada="2x1"
                pieza.cantidad.valor_original=pieza.cantidad.valor; pieza.cantidad.valor//=2; pieza.cantidad.regla_aplicada="2x1 (÷2)"
                alertas.append(f"✂️ Pág {num_pag} — {nombre}: Optimización 2x1")
            elif pieza.ancho.valor<self.p["ancho_pinza"]:
                alertas.append(f"🚨 Pág {num_pag} — {nombre}: Ancho {pieza.ancho.valor}mm < pinza")
                pieza.ancho.confianza=NivelConfianza.BAJA

            # R8: Canteado
            if self.p["canteado_auto"] and "SIN CANTO" not in notas and "OCULTO" not in notas:
                ec=self.p["espesor_canto_mm"]
                pieza.largo.valor_original=pieza.largo.valor_original or pieza.largo.valor; pieza.largo.valor-=ec*2
                pieza.largo.regla_aplicada=((pieza.largo.regla_aplicada+" ") if pieza.largo.regla_aplicada else "")+f"Canto -{ec*2}"
                pieza.ancho.valor_original=pieza.ancho.valor_original or pieza.ancho.valor; pieza.ancho.valor-=ec*2
                pieza.ancho.regla_aplicada=((pieza.ancho.regla_aplicada+" ") if pieza.ancho.regla_aplicada else "")+f"Canto -{ec*2}"

            # Excede tablero
            if pieza.largo.valor>self.p["largo_max"]:
                alertas.append(f"📏 Pág {num_pag} — {nombre}: Largo {pieza.largo.valor}mm > tablero")

            # Validación física
            ok,af,cf = ValidadorFisico.validar(
                {"largo":pieza.largo.valor,"ancho":pieza.ancho.valor,
                 "espesor":pieza.espesor.valor,"cantidad":pieza.cantidad.valor,"nombre":nombre}, self.p)
            alertas.extend(af)
            if not ok: pieza.largo.confianza=NivelConfianza.BAJA; pieza.ancho.confianza=NivelConfianza.BAJA

            # Deduplicación
            if pieza.hash_pieza in self.hash_vistos:
                alertas.append(f"🔄 Pág {num_pag} — '{nombre}' duplicada (pág {self.hash_vistos[pieza.hash_pieza]})")
                continue
            self.hash_vistos[pieza.hash_pieza] = num_pag
            piezas.append(pieza)
        return piezas, alertas

# ══════════════════════════════════════════════════════════════════════════════
# WORKER (thread-safe)
# ══════════════════════════════════════════════════════════════════════════════
def worker_pagina(datos_pag: DatosPagina, motor: MotorVision) -> tuple:
    num = datos_pag.num + 1
    if datos_pag.tiene_tablas:
        piezas_v = ExtractorVectorial.parsear_tablas(datos_pag.tablas, num)
        if piezas_v:
            return (num, piezas_v, OrigenDato.VECTOR_PDF,
                    f"VECTORIAL ({len(piezas_v)} pzs)")
    datos_ia = motor.analizar(datos_pag.imagen, datos_pag.texto)
    if datos_ia and not (isinstance(datos_ia[0], dict) and "error" in datos_ia[0]):
        fuente = "HÍBRIDO" if datos_pag.tiene_texto else "VISIÓN"
        return (num, datos_ia, OrigenDato.VISION_IA,
                f"GEMINI {fuente} ({len(datos_ia)} pzs)")
    err = datos_ia[0].get("error","?") if datos_ia else "sin datos"
    return (num, [{"error": err}], OrigenDato.VISION_IA, "ERROR")

# ══════════════════════════════════════════════════════════════════════════════
# EXTRACCIÓN PDF
# ══════════════════════════════════════════════════════════════════════════════
def pdf_a_datos(archivo, dpi=300) -> list:
    import fitz
    pdf_bytes = archivo.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    resultado = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        texto = page.get_text("text")
        tablas = []
        try:
            tabs = page.find_tables()
            if tabs and tabs.tables:
                for t in tabs.tables:
                    df = t.to_pandas()
                    if len(df) >= 2 and len(df.columns) >= 3:
                        tablas.append(df)
        except Exception:
            pass
        resultado.append(DatosPagina(
            num=i, imagen=img, texto=texto, tablas=tablas,
            tiene_texto=len(texto.strip()) > 20,
            tiene_tablas=len(tablas) > 0))
    doc.close()
    return resultado

# ══════════════════════════════════════════════════════════════════════════════
# EXTRACTOR DXF (añadir en core.py)
# ══════════════════════════════════════════════════════════════════════════════

def extraer_datos_dxf(archivo_dxf) -> list:
    """
    Extrae datos de un archivo DXF y devuelve lista de DatosPagina.
    
    Estrategia: NO intentamos parsear geometría (demasiado ambiguo).
    Extraemos textos + cotas como 'texto vectorial' y renderizamos
    imagen para que Gemini haga el trabajo de identificación.
    
    Requiere: pip install ezdxf matplotlib
    """
    import ezdxf
    from ezdxf.addons.drawing import matplotlib as ezdxf_mpl
    import matplotlib
    matplotlib.use('Agg')  # Sin GUI
    import matplotlib.pyplot as plt

    if hasattr(archivo_dxf, 'read'):
        # Streamlit UploadedFile → guardar temporalmente
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
            tmp.write(archivo_dxf.read())
            tmp_path = tmp.name
        doc = ezdxf.readfile(tmp_path)
        os.unlink(tmp_path)
    else:
        doc = ezdxf.readfile(archivo_dxf)

    msp = doc.modelspace()

    # ── 1. Extraer todos los textos ──
    textos = []
    for entity in msp:
        if entity.dxftype() == "TEXT":
            textos.append(entity.dxf.text)
        elif entity.dxftype() == "MTEXT":
            textos.append(entity.text)  # MTEXT usa .text no .dxf.text

    # ── 2. Extraer todas las cotas ──
    cotas = []
    for entity in msp:
        if entity.dxftype() == "DIMENSION":
            try:
                valor = entity.dxf.actual_measurement
                if valor and valor > 0:
                    cotas.append(round(valor, 1))
            except Exception:
                pass

    # ── 3. Extraer textos de bloques (INSERT) ──
    for entity in msp:
        if entity.dxftype() == "INSERT":
            try:
                block = doc.blocks.get(entity.dxf.name)
                if block:
                    for sub in block:
                        if sub.dxftype() == "TEXT":
                            textos.append(sub.dxf.text)
                        elif sub.dxftype() == "MTEXT":
                            textos.append(sub.text)
                        elif sub.dxftype() == "DIMENSION":
                            try:
                                v = sub.dxf.actual_measurement
                                if v and v > 0:
                                    cotas.append(round(v, 1))
                            except Exception:
                                pass
            except Exception:
                pass

    # ── 4. Construir texto vectorial ──
    texto_vectorial_parts = []
    if textos:
        # Filtrar textos vacíos y duplicados, mantener orden
        textos_limpio = []
        vistos = set()
        for t in textos:
            t_clean = str(t).strip()
            if t_clean and t_clean not in vistos:
                textos_limpio.append(t_clean)
                vistos.add(t_clean)
        texto_vectorial_parts.append("TEXTOS DEL DXF:")
        texto_vectorial_parts.extend(textos_limpio)

    if cotas:
        # Ordenar cotas de mayor a menor para contexto
        cotas_unicas = sorted(set(cotas), reverse=True)
        texto_vectorial_parts.append(f"\nCOTAS ENCONTRADAS ({len(cotas_unicas)}):")
        texto_vectorial_parts.append(
            ", ".join(f"{c}mm" for c in cotas_unicas[:50])  # Limitar
        )

    texto_vectorial = "\n".join(texto_vectorial_parts)

    # ── 5. Renderizar imagen ──
    imagen = _renderizar_dxf(doc)

    # ── 6. Intentar parseo directo de tablas en texto ──
    tablas = _buscar_tablas_en_textos_dxf(textos)

    return [DatosPagina(
        num=0,
        imagen=imagen,
        texto=texto_vectorial,
        tablas=tablas,
        tiene_texto=len(texto_vectorial) > 20,
        tiene_tablas=len(tablas) > 0
    )]


def _renderizar_dxf(doc, dpi=200) -> Image.Image:
    """Renderiza DXF a imagen PIL usando ezdxf backend."""
    try:
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        import matplotlib.pyplot as plt

        fig = plt.figure(dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1])

        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(doc.modelspace())

        ax.set_aspect('equal')
        ax.axis('off')

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                    pad_inches=0.1, facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf).copy()

    except Exception as e:
        logger.warning(f"Renderizado DXF falló ({e}), generando placeholder")
        # Fallback: imagen blanca con texto
        img = Image.new('RGB', (800, 600), 'white')
        return img


def _buscar_tablas_en_textos_dxf(textos: list) -> list:
    """
    Intenta detectar si los textos del DXF forman una tabla de despiece.
    Busca patrones como "PIEZA 800x450x19 2uds W980"
    Retorna lista de DataFrames compatibles con ExtractorVectorial.
    """
    import pandas as pd

    # Patrón: número x número (opcionalmente x número)
    patron_medidas = re.compile(
        r'(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)'
        r'(?:\s*[xX×]\s*(\d+(?:[.,]\d+)?))?'
    )
    # Patrón cantidad: 2uds, 3 ud, x4, qty:5
    patron_cant = re.compile(
        r'(\d+)\s*(?:ud|uds|pcs|pzs|unid)|[xX](\d+)|qty[:\s]*(\d+)',
        re.IGNORECASE
    )

    filas = []
    for texto in textos:
        m = patron_medidas.search(str(texto))
        if m:
            largo = float(m.group(1).replace(",", "."))
            ancho = float(m.group(2).replace(",", "."))
            espesor = float(m.group(3).replace(",", ".")) if m.group(3) else 19.0

            # Buscar cantidad
            cant = 1
            mc = patron_cant.search(str(texto))
            if mc:
                cant = int(next(g for g in mc.groups() if g))

            # El nombre es el texto limpio sin las medidas
            nombre = patron_medidas.sub("", str(texto))
            nombre = patron_cant.sub("", nombre).strip(" -·:,")
            if not nombre:
                nombre = f"Pieza DXF"

            filas.append({
                "nombre": nombre, "largo": largo, "ancho": ancho,
                "espesor": espesor, "cantidad": cant, "material": ""
            })

    if filas:
        df = pd.DataFrame(filas)
        return [df]
    return []

# ══════════════════════════════════════════════════════════════════════════════
# AUDITORÍA
# ══════════════════════════════════════════════════════════════════════════════
class Auditoria:
    @staticmethod
    def generar(piezas, alertas, perfil, archivo, backend="", model="", workers=1):
        sep="="*70
        lns=[sep,"AUDITORÍA — GABBIANI MASTER AI v7.0 ENTERPRISE",sep,
             f"Fecha:   {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
             f"Archivo: {archivo}", f"Perfil:  {perfil}",
             f"Backend: {backend} · Modelo: {model}",
             f"Workers: {workers} · Piezas: {len(piezas)} · Alertas: {len(alertas)}",
             "-"*70,"","MODIFICACIONES:",""]
        mod=0
        for p in piezas:
            cambios=[]
            if p.largo.fue_modificado(): cambios.append(f"  L: {p.largo.valor_original}→{p.largo.valor} [{p.largo.regla_aplicada}]")
            if p.ancho.fue_modificado(): cambios.append(f"  A: {p.ancho.valor_original}→{p.ancho.valor} [{p.ancho.regla_aplicada}]")
            if p.espesor.fue_modificado(): cambios.append(f"  E: {p.espesor.valor_original}→{p.espesor.valor} [{p.espesor.regla_aplicada}]")
            if p.cantidad.fue_modificado(): cambios.append(f"  C: {p.cantidad.valor_original}→{p.cantidad.valor} [{p.cantidad.regla_aplicada}]")
            if cambios:
                mod+=1; lns.append(f"[{p.id}] {p.nombre} (Pág {p.pagina_origen})")
                lns.extend(cambios); lns.append("")
        lns.extend([f"Modificadas: {mod}","","-"*70,"ALERTAS:",""])
        lns.extend([f"  • {a}" for a in alertas])
        lns.extend(["",sep,"FIN",sep])
        return "\n".join(lns)
