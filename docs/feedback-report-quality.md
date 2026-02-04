# Feedback: Calidad del Reporte HTML de Code Doctor

## Fecha: 2026-02-03
## Version: v0.2.0

Este documento captura feedback real sobre la calidad de los reportes generados, para
guiar mejoras futuras. Debe consultarse al modificar templates, static_findings, o reporters.

---

## Feedback Ronda 1: Vista Colapsada

### Problemas Identificados

1. **Warnings genericos y repetitivos**
   - Los 5 warnings dicen lo mismo: "Descomponer X() en funciones mas pequenas"
   - No hay informacion especifica sobre QUE bloques extraer o COMO dividir
   - Sin AI review, el fix es template text sin valor accionable real

2. **Top Acciones duplica Warnings**
   - La seccion "Top Acciones Prioritarias" es identica al contenido de Warnings
   - No agrega informacion nueva, solo ruido visual
   - Deberia diferenciar: Top Actions = resumen ejecutivo, Warnings = detalle tecnico

3. **Sin diferenciacion de urgencia dentro del grupo**
   - CC=27 y CC=13 se presentan visualmente iguales (ambos WARNING amarillos)
   - CC=27 es significativamente peor que CC=13 pero no se distingue
   - Considerar: gradientes de color, iconos, o sub-niveles

4. **Sin codigo (code_before/code_after)**
   - Findings de complejidad no tienen code diffs
   - El boton "Copiar fix" nunca aparece para estos findings
   - El desarrollador no tiene nada concreto para copy-paste

5. **Falta lo positivo**
   - El reporte solo muestra problemas
   - No destaca: 90.6% coverage, 0 vulnerabilidades, 29/40 funciones testeadas
   - Reportes que solo critican generan rechazo del usuario

6. **"3 untested" sin decir cuales**
   - La card dice "3 untested" pero no identifica las funciones
   - INFO findings estan filtrados por default (--severity critical,warning)
   - El usuario tiene que cambiar flags para ver esa informacion

7. **CC sin contexto**
   - CC = Cyclomatic Complexity, pero un desarrollador promedio no sabe que significa
   - No hay tooltip, leyenda, ni explicacion del umbral (10 = flag, 20 = high, 50 = very high)
   - Los numeros CC=14, CC=27 no comunican severidad relativa

---

## Feedback Ronda 2: Vista Expandida (Detalle de Findings)

### Nuevos Problemas al Ver Detalle

8. **Descripcion con umbral contradictorio**
   - Texto: "Funciones con CC>20 son dificiles de testear y mantener"
   - Pero la funcion tiene CC=13 o CC=14, que estan DEBAJO de 20
   - El umbral de flagging real es CC>10 (COMPLEXITY_MEDIUM en analyzer)
   - El texto menciona COMPLEXITY_HIGH (20) porque static_findings.py usa esa constante
   - Esto confunde: "si CC>20 es el problema, por que me flageas CC=13?"

9. **Fix explanation es generico**
   - "Extraer bloques logicos en funciones auxiliares para reducir la complejidad de 14 a menos de 20"
   - No identifica CUALES bloques logicos, ni sugiere nombres de funciones extraidas
   - Es consejo valido pero no accionable — el desarrollador ya sabia esto

10. **Code Analysis muestra datos sospechosos**
    - "Average Complexity: 0.0" — imposible si hay funciones con CC=14, 27, etc.
    - "Total Lines of Code: 0" — el proyecto tiene 5724 LOC segun terminal output
    - Estos ceros provienen del AnalysisReport que calcula metricas solo para funciones parseadas
    - BUG: avg_complexity y total_loc no se estan calculando correctamente

11. **Footer sin valor**
    - "5 advertencias, 5 notas." — ya se vio en las cards arriba
    - No agrega informacion util
    - Podria mostrar: "Siguiente paso: ejecutar con --fix para aplicar correcciones automaticas"

12. **INFO findings invisibles**
    - El reporte dice "5 notas" pero no las muestra (filtro de severidad)
    - No hay indicador visual de que hay contenido oculto
    - No hay link o instruccion para ver los INFO findings

---

## Mejoras Propuestas (Priorizadas)

### P0 - Bugs que rompen credibilidad
- [ ] Corregir "CC>20" en descripcion — debe decir "CC>10" o adaptar el texto
- [ ] Investigar avg_complexity=0.0 y total_loc=0 — posible bug en AnalysisReport

### P1 - Valor accionable
- [ ] Agregar seccion "Lo positivo" al reporte (coverage, funciones testeadas, 0 criticals)
- [ ] Diferenciar Top Acciones de Findings (Top = resumen ejecutivo con prioridad clara)
- [ ] Mostrar nombre de las 3 funciones untested en la card o link a INFO findings
- [ ] Agregar leyenda/tooltip para CC: "CC = Complejidad Ciclomatica. >10 = alto, >20 = muy alto"

### P2 - Presentacion
- [ ] Gradiente visual para urgencia: CC=27 deberia verse mas urgente que CC=13
- [ ] Footer util: "Ejecutar `autotest diagnose --fix` para aplicar correcciones"
- [ ] Indicador de contenido filtrado: "5 notas ocultas — usar --severity info para verlas"
- [ ] Hacer expandibles las acciones en Top Actions (click -> scroll al finding)

### P3 - Contenido (requiere AI o analisis mas profundo)
- [ ] Con AI habilitado: generar fixes especificos con code_before/code_after para complejidad
- [ ] Sin AI: al menos mostrar la firma de la funcion y su tamanho (lineas)
- [ ] Sugerir nombres concretos para funciones extraidas basado en el qualified_name

---

## Notas para Claude

Cuando modifiques el template HTML o static_findings.py, consulta este documento.
Prioridad: no generar texto que contradiga los datos (como "CC>20" para funciones con CC=13).
El reporte debe ser accionable — si el desarrollador no sabe que hacer despues de leerlo, fallo.
