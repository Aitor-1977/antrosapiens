# 0004 · Principios Inmutables + Léxico Canónico

## Principios inmutables (no se rompen aunque cambie la tecnología)
1. **Toda inferencia antropológica ocurre exclusivamente en Motor A.**
2. **RadarHD nunca interpreta evidencia; solo consume y representa.**
3. **Toda decisión metodológica es humana** (la máquina propone, el humano dispone).
4. **La UX refuerza el método** (evidencia → hipótesis → implicación → recomendación).
5. **Ninguna responsabilidad existe duplicada** (una responsabilidad, un único dueño).
6. **Integración solo por contrato HTTP versionado**, dirección única A→RadarHD, sin BD compartida.
7. **Todo freno (Kill Switch) es reversible y auditado.**
8. **Un solo Expediente en Peritaje Activo** (foco pericial).
9. **La vista no piensa** (cero lógica de dominio en React).
10. **El aprendizaje del cierre retorna a Motor A** (loop cerrado).

## INVARIANTE REGLA CERO (candado científico) — regla de negocio de máxima jerarquía
> **Ninguna entidad del BC-II (Prospecto) puede avanzar de estado ni iniciar contacto sin un
> dictamen antropológico validado (Peritaje / DolorMap®) originado en el BC-I. La ciencia es
> el candado de la operación comercial.**

- **Dónde debe implementarse:** guard de dominio en la transición `Detectado → {Siembra…}` del
  Prospecto, exigiendo `peritaje_validado` (veredicto de Motor A ≠ BLOQUEADA) + DolorMap presente.
- **Qué protege:** que no se opere/venda sobre organizaciones sin peritaje científico ("vender sin peritar").
- **Si se elimina:** el laboratorio degrada a CRM de volumen; se pierde el rigor pericial.
- **Capa:** **Dominio** (invariante), aplicada en la Aplicación, reflejada en la Interfaz.

## Qué NUNCA debe hacer RadarHD
1. Inferir Deuda Cultural / ICP / hipótesis (LLM, reglas o React).
2. Clasificar o re-interpretar la evidencia del corpus de A.
3. Emitir dictamen pericial propio paralelo al de A.
4. Calcular inteligencia en componentes.
5. Escribir en Motor A o compartir su BD.
6. Permitir operación comercial sin peritaje + DolorMap (Regla Cero).
7. Duplicar la captura que A ya cubre.

## Léxico canónico (autorizado) vs prohibido
**Autorizado (lenguaje del Laboratorio):** Organización Observada, Prospecto, Caso, Peritaje,
Dictamen, DolorMap®, Bitácora, Sprint Fundacional, Deuda Cultural™, ritual competidor,
hibridación onlife, colapso estructural, deriva narrativa, Cualificación Liminal, Kill Switch.

**Prohibido (léxico no autorizado — rechazo automático):** `lead`, `leads`, `churn`, `funnel`,
`pipeline` (como término genérico de ventas), "UX genérico", "customer", "deal", y cualquier
jerga de CRM/growth que borre la identidad antropológica. Cada término prohibido detectado en
código nuevo o interfaz es motivo de rechazo (ver `0007` · enforcement).
