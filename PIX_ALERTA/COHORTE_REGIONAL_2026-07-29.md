# Cohorte regional de Santo Antonio — medición del 2026-07-29

Escaneo de un radio de **10 km** alrededor de Santo Antonio para construir una cohorte de
lotes vecinos de cereal de invierno, y comparar el campo del cliente contra ella.

Arnés: `medicion/cohorte_regional.py`. Todo lo que sigue está medido sobre imágenes
reales; lo que no se pudo verificar está marcado.

---

## 1. La escena

**No existe escena del 17/07.** La más cercana totalmente limpia es la del **15/07**
(gránulo T22KEV): 0,0% de nube en metadatos y **100% de píxel válido sobre las 31.041 ha**
del AOI. El AOI cruza dos gránulos MGRS (T22KEV y T22KEU); T22KEU sólo cubre el 33%, así
que se trabaja con T22KEV, que cubre todo.

## 2. Cómo se identificó el trigo vecino — y por qué NO por firma espectral

Una firma espectral de **una** fecha no separa trigo de otras coberturas verdes: en julio
un trigo en llenado, una pastura y un monte tienen NDVI parecido. Lo que sí separa es la
**fenología invertida**. En Paraná, en julio, no hay cultivo de verano creciendo (la soja
se cosechó en febrero-marzo, el maíz de segunda en junio-julio). Entonces:

> lo que en abril estaba desnudo y en julio está pleno = cereal de invierno

**Validado contra los dos lotes de los que SÍ sabemos que son trigo:**

| cobertura | abril | mayo | junio | julio | **amplitud jul−abr** |
|---|---|---|---|---|---|
| SANTO_ANTONIO-01 (trigo) | 0,189 | 0,298 | 0,904 | 0,928 | **0,728** |
| SANTO_ANTONIO-02 (trigo) | 0,236 | 0,197 | 0,725 | 0,918 | **0,662** |
| mediana del paisaje | 0,652 | 0,707 | 0,816 | 0,863 | **0,098** |

La mediana del paisaje **no cambia** (0,098): es monte, pastura y rastrojo. El trigo
conocido salta 0,66–0,73. Reglas finales: NDVI(siembra) ≤ 0,45 **y** NDVI(pleno) ≥ 0,55
**y** amplitud ≥ 0,40.

**Resultado: 11.223 ha clasificadas (36,2% del AOI), 248 unidades de cohorte de 25 ha
cada una, 6.219 ha en total.**

## 3. La comparación

| fecha | cob. AOI | SA-01 NDVI | SA-01 NDMI | SA-02 NDVI | SA-02 NDMI |
|---|---|---|---|---|---|
| 05-01 | 100% | 0,154 (p45) | −0,217 (p30) | 0,182 (p60) | −0,193 (p51) |
| 05-11 | 93% | 0,346 (p79) | −0,073 (p63) | 0,209 (p35) | −0,115 (p36) |
| 05-31 | 100% | 0,881 (p94) | 0,381 (p91) | 0,600 (p50) | 0,076 (p46) |
| 06-05 | 100% | 0,904 (p96) | 0,412 (p92) | 0,725 (p50) | 0,178 (p47) |
| 06-22 | 75% | 0,928 (p100) | 0,530 (p97) | 0,877 (p66) | 0,444 (p63) |
| **07-05** | **79%** | **0,776 (p21)** | **0,436 (p34)** | **0,813 (p25)** | **0,427 (p31)** |
| 07-10 | 100% | 0,928 (p75) | 0,537 (p94) | 0,922 (p60) | 0,485 (p56) |
| 07-15 | 100% | 0,928 (p67) | 0,561 (p92) | 0,927 (p66) | 0,511 (p61) |

**Lectura para el cliente:** en las fechas limpias, Santo Antonio-01 está en el **p92–p97
de NDMI** de sus vecinos y Santo Antonio-02 en el **p56–p63**. El campo está en la parte
alta de su región. Con el sesgo declarado en §5, esa afirmación es conservadora.

---

## 4. INSUMOS PARA EL MOTOR

### 4.1 La cohorte cierra un punto ciego, y es viable

El criterio compara cada píxel contra su propia historia **dentro del lote**, así que es
estructuralmente ciego a un evento que afecte al lote entero. El arreglo estándar
—comparar entre lotes— pide ≥8 lotes y este cliente tiene 2 y nunca va a tener más.

**Medido: la cohorte se puede construir sin ningún inventario del cliente**, sólo con
imagen. 248 unidades comparables en 10 km. Eso da una lectura que el criterio actual no
puede dar: «este campo viene mejor/peor que su región».

### 4.2 ⚠️ La cohorte cruda FABRICA alarmas — y la puerta de cobertura NO alcanza

En la primera corrida, la escena del **07-05 (79% de cobertura sobre el AOI)** hizo que
SA-01 pasara de **p100 a p21**. Es un artefacto, y se prueba con la fecha siguiente:

> NDVI de SA-01: **0,928** (06-22) → **0,776** (07-05) → **0,928** (07-10) → **0,928** (07-15)

Un trigo no pierde 0,15 de NDVI y lo recupera en cinco días. Era bruma sobre el campo que
sobrevivió a la máscara.

**Y lo importante: esa escena PASÓ una puerta de cobertura del 70% sobre el lote.** O sea
que subir el umbral de cobertura no la habría filtrado. La cohorte necesita otra defensa.

### 4.3 ⚠️ HALLAZGO QUE CONTRADICE UN SUPUESTO DEL CRITERIO

Con las unidades correctas, el 07-05 los **tres índices caen juntos**: NDVI p21, NDMI p34,
NDRE p30. No se separan.

Eso significa que **la bruma deprime todos los índices de forma coherente**, y por lo
tanto **exigir que los dos ejes se muevan juntos NO protege contra contaminación
atmosférica**. El docstring de `informe_focos` dice al cliente que «exigir que los dos se
muevan juntos es lo que evita marcar ruido»: eso es cierto para ruido independiente del
sensor, y **falso para nube fina**, que es el artefacto dominante.

No es una sorpresa aislada: encaja con lo ya medido en julio, cuando los 3 focos
reportados al cliente eran borde de nube **y habían pasado la conjunción de dos ejes**.

**Consecuencia para el motor:** la conjunción de ejes no es una defensa contra artefactos
atmosféricos. Lo que defiende es el enmascarado (SCL + dilatación + CloudScore+) y una
**verificación de plausibilidad temporal**: una caída que se recupera en la escena
siguiente no es del cultivo.

Y de paso queda **refutada una regla que yo mismo propuse** en esta misma medición: el
«desacuerdo entre índices como firma de artefacto». Con las unidades malas parecía que en
el 07-05 los índices se separaban (NDVI p23 contra NDMI p56); con las unidades correctas
caen juntos. **Esa separación era un artefacto de la unidad de comparación, no una señal.**

### 4.4 La unidad de comparación importa, y la primera estaba mal

Las componentes conectadas de la máscara **no son lotes**: lotes vecinos que se tocan se
fusionan, y salió una componente de **2.074 ha**. Su mediana es un promedio regional y
pesaba lo mismo en la cohorte que un lote de 5 ha.

**La unidad correcta es una grilla de celdas de tamaño comparable al lote del cliente**:
500 × 500 m = 25 ha, exigiendo ≥70% de cereal. Con eso, 248 unidades uniformes.

Y el cambio de unidad **movió las conclusiones**, no sólo los decimales: SA-01 en el 06-22
pasó de p100 a p100 (igual), pero en el 07-15 de p93 a p67. No es cosmético.

### 4.5 Hace falta ALINEAR POR FENOLOGÍA, no por fecha de calendario

SA-01 está **adelantado** respecto de su cohorte: el 05-31 tenía NDVI 0,881 (p94) cuando
la mediana de los vecinos era 0,607. Un lote adelantado llega antes al pico y **declina
antes**, así que en la fase de caída aparece bajo en el percentil sin que nada esté mal.

Comparar por fecha de calendario confunde «adelantado» con «peor». **El motor ya tiene la
técnica**: `estratos.desfase` compara el día en que cada bloque alcanza el mismo NDVI. Lo
mismo aplica a la cohorte.

### 4.6 Para la comparación regional, NDVI no sirve — NDMI sí

En julio la cohorte tiene el NDVI aplastado contra el techo: **p10 = 0,874 y p90 = 0,938**,
toda la distribución dentro de 0,06. Con eso los percentiles son ruido.

NDMI tiene rango real (p10 0,401 → p90 0,554) y discrimina: SA-01 queda en p92 con NDMI y
en p67 con NDVI el mismo día. **Para la capa regional, el eje es NDMI.**

### 4.7 Sesgo de selección, declarado

Un trigo vecino que **falló** tiene amplitud baja y **no entra** en la cohorte. Entonces la
cohorte es una referencia de «trigo que emergió y creció», no de «trigo sembrado», y está
sesgada hacia arriba. Comparar contra ella hace que el campo se vea **peor** de lo que se
vería contra la población real: es el lado conservador del error, pero hay que decirlo al
informar.

### 4.8 No es «trigo»: es cereal o cobertura de invierno

Avena, cebada, triticale y un nabo forrajero tienen la misma fenología y Sentinel-2 no los
separa. Se podrían separar por la senescencia de cosecha (el trigo se seca en agosto, una
cobertura no), pero eso exige imágenes que en julio todavía no existen.

---

## 5. Qué se implementó y qué NO

**Implementado:** el arnés de medición, con los dos defectos corregidos (unidad de grilla,
puerta de cobertura sobre el lote además del AOI).

**NO implementado en el motor, a propósito.** La capa regional necesita antes:

1. **Alineación fenológica** (§4.5) — sin eso genera falsas alarmas en la fase de declive.
2. **Verificación de plausibilidad temporal** (§4.2, §4.3) — es la única defensa que
   habría atrapado el 07-05, y no está construida ni calibrada.
3. **Tasa de falsa alarma de la capa**, medida sobre fechas sin evento, como se hizo con
   el criterio. Hoy no existe.

Encender la cohorte sin 1 y 2 sería agregar una capa que ya se demostró capaz de fabricar
un derrumbe del p100 al p21. **La medición dice que la idea sirve y que la
implementación todavía no está.**
