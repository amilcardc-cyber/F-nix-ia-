# FÉNIX AI TRADER — Inicio rápido

## Qué incluye
Primer módulo: escáner de contratos perpetuos USDT-M de Binance Futures.
- Usa endpoints públicos de Binance.
- No requiere API key, contraseña ni permisos de cuenta.
- No abre operaciones, no deposita fondos y no puede retirar dinero.
- Analiza velas de 1m o 5m, EMA 9/21/200, RSI y volumen relativo.
- Muestra candidatos LONG/SHORT para investigar; no son órdenes ni garantías.

## Ejecutarlo desde iPhone
La forma más práctica desde un iPhone es abrir un entorno Python en la nube desde Safari
(por ejemplo, un espacio de desarrollo compatible con Streamlit), subir estos archivos,
instalar `requirements.txt` y ejecutar:

    streamlit run app.py --server.address 0.0.0.0 --server.port 8501

Los proveedores gratuitos cambian sus límites y pueden suspender aplicaciones inactivas.
Este proyecto se puede mover luego a un VPS sin reescribir el escáner.

## Ejecutarlo en una computadora
1. Instalar Python 3.10 o superior.
2. Abrir una terminal en la carpeta del proyecto.
3. Ejecutar:
   `pip install -r requirements.txt`
4. Ejecutar:
   `streamlit run app.py`

## Seguridad y límites
- No pegues claves API en el código, chat, repositorios ni capturas.
- Este módulo no necesita claves API.
- No habilites retiros en ninguna clave API futura.
- El puntaje es una regla técnica inicial, no un modelo predictivo entrenado.
- No se ejecutan trades. Antes de operar en real hay que implementar y probar:
  mínimos de notional, step size, tick size, comisiones, funding, slippage,
  margen aislado, cálculo de tamaño por riesgo, órdenes de protección y manejo de fallos.
- Con un capital equivalente a unos pocos USDT, muchos contratos pueden no cumplir
  los mínimos de Binance o resultar antieconómicos por comisiones. Verificarlo antes
  de depositar.

## Estructura
- `app.py`: aplicación web y escáner.
- `requirements.txt`: dependencias.
