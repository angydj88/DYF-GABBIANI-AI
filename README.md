# 🔷 GABBIANI MASTER AI - v7.0 Enterprise

![Version](https://img.shields.io/badge/Version-7.0_Enterprise-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35.0-red)
![Gemini](https://img.shields.io/badge/Google_AI-Gemini_2.5_Pro-orange)
![Gabbiani](https://img.shields.io/badge/Machine-Gabbiani_WinCut-brightgreen)

Sistema experto de optimización de corte industrial y post-procesador CAM. Automatiza la extracción de despieces desde planos PDF y genera archivos nativos para seccionadoras CNC Gabbiani, aplicando reglas de negocio deterministas.

## 🚀 Arquitectura Híbrida

El sistema utiliza un **Pipeline Dual Concurrente**:
1. **El Ojo (Extracción IA):** Utiliza PyMuPDF para extraer vectores exactos y los inyecta junto con la imagen renderizada en un modelo visual (Google Gemini / Vertex AI) mediante *Prompt Híbrido*.
2. **El Cerebro (Motor de Reglas):** Un sistema determinista en Python que evalúa las piezas extraídas y aplica las leyes físicas de la carpintería y las normativas internas del taller.

## 🧠 Motor de Reglas Industriales (CerebroOperario v7)

El núcleo del sistema aplica 8 reglas de negocio en estricto orden secuencial para garantizar la integridad de la producción:

*   **[R1] Regla Sándwich:** Detecta piezas dobles ("Pegar", "19+19") y aplica márgenes de saneado automáticos (+60mm).
*   **[R2] Cajones QUBE:** Calcula y genera automáticamente las piezas de "Fondo oculto" basándose en el ancho exterior del mueble y la longitud de la guía metálica.
*   **[R3] Aligeramiento (Gradeles):** Fuerza el espesor de puertas y estantes a 16mm para ahorrar peso y costes, corrigiendo errores del delineante.
*   **[R4] Pilastras y Cierres en L:** Ensancha piezas estrechas a 200mm para permitir el mecanizado y plegado posterior en la máquina tupí.
*   **[R5] Veta Continua:** Agrupa múltiples frentes de cajón en un único bloque de 1000mm para asegurar la continuidad del dibujo de la madera al cortar.
*   **[R6] Holgura CNC:** Añade +10mm de margen a las piezas que requieren mecanizados curvos posteriores.
*   **[R7] Optimización 2x1 y Pinzas:** Agrupa tiras finas (<50mm) en cantidades pares o fuerza medidas a un mínimo de 130mm por seguridad de las pinzas de la máquina.
*   **[R8] Canteado Automático:** Descuenta el grosor del canto (ej. 2mm x 2) de la medida final de corte.

## 🏭 Perfiles de Cliente Soportados

El sistema es multi-cliente y adapta sus lógicas según el proyecto seleccionado en la UI:
*   **ESTÁNDAR:** Reglas básicas de seguridad y mecanizado.
*   **APOTHEKA / ILUSION:** Activa la generación matemática de fondos QUBE.
*   **NCA / GRUPO LOBE:** Mapeo de materiales específicos (TEXTIL ATLAS, BLANCO VINTAGE) y espesores de 10mm/30mm.
*   **GRADELES:** Fuerza la regla de aligeramiento de puertas a 16mm.

## 💾 Formatos de Exportación

1.  **CSV de Revisión:** Archivo estándar (separado por `;`) con trazabilidad para la oficina técnica.
2.  **TXT GABBIANI (Nativo):** Genera el código máquina directo.
    *   Incluye la cabecera obligatoria `HDR6,90`.
    *   Mantiene precisión decimal exacta (`.33`, `.67`) para ajustes de holgura en huecos divididos, evitando errores de redondeo.
3.  **Informe de Auditoría:** Un log en texto plano que documenta cada milímetro modificado por la IA, indicando el valor original, el valor final y la regla aplicada.

## 🛠️ Instalación y Requisitos

**Dependencias principales (`requirements.txt`):**
```text
streamlit>=1.35.0
google-generativeai>=0.8.0
pandas>=2.0.0
Pillow>=10.0.0
openpyxl
PyMuPDF>=1.24.0
google-cloud-aiplatform>=1.64.0
google-auth>=2.20.0
typing_extensions>=4.5.0
