# Ascendancy — Design da cidade v2 (spec para implementar nos geradores)

Coordenadas: Godot (x, z) em metros, como em `tools_src/build_hub_scene.py`. +X = sentido catedral (real NE), −Z = lado da Av. Índio Bandeira (avenida do jogo), +Z = lado da Av. Irmãos Pereira. Praça Getúlio Vargas (GV) centro (−34, 0), São José (SJ) centro (34, 0), meia-praça (30, 48). Seções da catedral usam as coordenadas Blender de `build_cathedral.py` (x = través, y = ao longo da nave, z = altura).

Como medi: girei `maps_aerial_praca_z19.png` em −41° (avenida na horizontal), escala 5,55 px/m real; jogo = real × ~0,6. Posições abaixo são a foto medida e depois arredondada/simetrizada.

---

## A. Praças: o que a foto mostra × o que o jogo tem

### A.1 Como é a GV real
1. **Esplanada reta e larga** (≈13 m reais → **8 m no jogo**) cruzando a praça inteira no eixo oeste–leste, passando pelo chafariz e apontando para a fachada da catedral. É o elemento dominante da foto oblíqua.
2. **Largo do chafariz**: disco pavimentado (raio ≈10 m jogo) com tanque **lobulado (quadrifólio)**, não redondo liso.
3. **Não existe** eixo norte–sul reto, nem "X" de canto a canto, nem passeio em anel. Do largo saem **4 caminhos diagonais curtos/longos** que terminam em **4 largos secundários**:
   - lado leste (perto da catedral): dois **rondéis redondos** (raio ≈4 m) com marco/poste no centro, a ≈(+10, ∓16) do chafariz;
   - lado oeste: dois **largos maiores** (raio ≈5 m) a ≈(−9, ∓28) do chafariz, de onde saem 3 ramos cada (para o canto da praça, para a borda oeste e para a borda norte/sul).
4. **Coreto**: a noroeste do chafariz, ≈(−12, −13) dele, **no meio do gramado**, com só um caminho curto de acesso; não fica num disco pavimentado grande.
5. **Canteiros**: grandes, de forma irregular (resto entre os caminhos), bordas arredondadas junto aos largos, cercados de sebe baixa.
6. **Palmeiras**: em fileiras dos dois lados dos caminhos diagonais e das bordas da esplanada, e em volta dos largos (≈50 no total). Não em anel regular em volta do chafariz.
7. **Árvores de copa grande**: faixa contínua na borda norte (avenida) e sul; duas faixas diagonais densas na metade leste (formam um "V" que fecha na direção da catedral, deixando só o eixo da esplanada aberto); borda da Rua Brasil. Borda oeste: árvores menores floridas (rosa/lilás).
8. **Marco no eixo**: pequena rotatória com monumento branco (obelisco) na Rua Brasil, entre chafariz e catedral.

### A.2 Como é a SJ real
- Catedral no eixo, fachada para a Rua Brasil, recuada; adro pavimentado na frente; passeio colado em volta do prédio.
- **Todo o resto é bosque**: copas de 15–25 m reais encostadas umas nas outras, sem céu entre elas, dos dois lados do adro e ao longo de toda a lateral. (Na aérea atual o lado norte virou terreno de feira; a foto oblíqua do usuário mostra bosque dos dois lados. Usar bosque dos dois lados.)

### A.3 O que está errado hoje (`square_paths()`, `palm_spots()`, `add_trees()`)
| Hoje | Correto |
|---|---|
| Layout "union jack": eixo N–S + eixo L–O de 4 m + 2 diagonais de canto a canto | Só esplanada L–O de 8 m + 4 diagonais curtas até largos + ramos |
| `("ring", GV, 18.5, 21.5)` passeio em anel | **Remover** (não existe) |
| 4 rondéis de r 3,4 nas diagonais longas (`rondel_centers`) | 2 rondéis r 4 a leste + 2 largos r 5 a oeste, nas posições abaixo |
| Coreto em (−50, −12) dentro de disco pavimentado r 7,5 | Coreto em (−46, −13) no gramado, avental r 4,6 + 1 caminho |
| Tanque do chafariz redondo | Tanque quadrifólio (4 lóbulos) |
| 8 palmeiras em anel + pares no eixo N–S | Fileiras ao longo dos caminhos (regra A.5) |
| Árvores `CommonTree` ×0,85–1,45 (copa 3–5 m), espalhadas em grade | Árvores velhas copa 12–18 m (seção B), em faixas/bosque |
| SJ com caminho central N–S e gramado aberto | SJ = bosque fechado, sem caminho central |
| Sebe só no lado da rua, 0,8 m | Sebe 0,5 m em volta de todo canteiro (seção H) |

### A.4 Layout numérico — substituir `square_paths()` por isto
```python
PATH_WIDTH = 4.0                      # passeio do perímetro (LAWN_RECTS continua = praça − 4 m)
ESPLANADE_WIDTH = 8.0
PLAZA_RADIUS = 10.0
NODE_NW, NODE_SW = (-43.0, -28.0), (-43.0, 28.0)      # largos oeste, raio 5.0
RONDEL_NE, RONDEL_SE = (-24.0, -16.0), (-24.0, 16.0)  # rondéis leste, raio 4.0
NODE_RADIUS, RONDEL_RADIUS = 5.0, 4.0
COREO_POSITION = (-46.0, -13.0)
COREO_APRON_RADIUS = 4.6
PLAYER_SPAWN = (-38.4, -13.0)         # pé da escada do coreto, já em cima da diagonal NW
MARCO = (0.0, 0.0)                    # obelisco na Rua Brasil, no eixo
CATHEDRAL_FACADE_X = 13.0             # ver seção G (catedral maior)

def square_paths():
    gv = GETULIO_VARGAS
    paths = [
        ("disc", gv, PLAZA_RADIUS),
        ("strip", (-64.0, 0.0), (-4.0, 0.0), ESPLANADE_WIDTH),          # esplanada
        ("disc", NODE_NW, NODE_RADIUS), ("disc", NODE_SW, NODE_RADIUS),
        ("disc", RONDEL_NE, RONDEL_RADIUS), ("disc", RONDEL_SE, RONDEL_RADIUS),
        ("disc", COREO_POSITION, COREO_APRON_RADIUS),
        ("strip", COREO_POSITION, (-38.2, -13.0), 2.5),                 # acesso do coreto
    ]
    for sign in (-1.0, 1.0):                                            # −1 = norte, +1 = sul (espelhado)
        node, rondel = (-43.0, sign * 28.0), (-24.0, sign * 16.0)
        paths += [
            ("strip", gv, node, 3.5),                                   # chafariz -> largo oeste
            ("strip", node, (-60.0, sign * 44.0), 3.5),                 # largo -> canto da praça
            ("strip", node, (-60.0, sign * 21.0), 3.0),                 # largo -> borda oeste
            ("strip", node, (-23.0, sign * 39.5), 3.0),                 # largo -> ramo norte/sul
            ("strip", gv, rondel, 3.5),                                 # chafariz -> rondel leste
            ("strip", rondel, (-23.0, sign * 44.0), 3.0),               # rondel -> borda norte/sul
            ("strip", rondel, (-8.0, sign * 27.0), 3.0),                # rondel -> borda leste (inferido: fica sob as copas na foto)
        ]
    # São José (catedral nova: fachada x=13, meia-largura 13, fundo x≈60.6)
    paths += [
        ("strip", (4.0, 0.0), (13.0, 0.0), 22.0),                       # adro (z ±11)
        ("strip", (13.0, 0.0), (64.0, 0.0), 32.0),                      # passeio em volta da catedral (3 m livres de cada lado)
        ("strip", (4.0, -30.0), (64.0, -30.0), 3.0), ("strip", (4.0, 30.0), (64.0, 30.0), 3.0),
        ("strip", (8.0, -48.0), (8.0, -11.0), 3.0), ("strip", (8.0, 11.0), (8.0, 48.0), 3.0),
        ("strip", (61.0, -48.0), (61.0, -16.0), 3.0), ("strip", (61.0, 16.0), (61.0, 48.0), 3.0),
    ]
    return paths
```
Remover: `RING_RADII`, `RONDEL_ALONG`, `rondel_centers()`, o strip N–S da GV, as duas diagonais de canto, o strip `(sao_jose_x, ∓half_z)`.

Extras de layout:
- **Marco (0, 0)**: disco pavimentado r 4,5 já é rua; pôr canteiro em anel r 1,2–2,6 com sebe e obelisco branco de 5 m (base quadrada 1,2 m, fuste 0,7→0,35, ponta piramidal). `add_market`: manter barracas fora de |z| < 8 (já está).
- **Tanque quadrifólio** (`build_large_fountain`): contorno = círculo r 4,2 + 4 lóbulos semicirculares r 2,1 centrados a 3,9 m nos eixos (N, S, L, O); largura total ≈12 m. Colisor: manter cilindro r 6,1.
- **Incrustação** no largo do chafariz: anel de pedra clara r 8,6–9,2 e estrela de 8 pontas discreta (já existe `build_inlays`, só reposicionar).
- Postes: os 8 do anel r 9 ficam; esplanada: 2 fileiras em z = ±4,6, x de −60 a −46 e de −22 a −8, passo 7 m; 4 em cada largo/rondel (raio + 0,8, a 45°); remover os de perímetro que caírem a < 2 m de outro.
- Bancos: 8 no largo do chafariz (r 8,6, de costas para a sebe); esplanada: z = ±3,4, x = −56, −50, −18, −12, virados para o eixo; 3 em cada largo oeste, 2 em cada rondel.
- Revalidar com `on_lawn()` todos os pontos de NPC (`TalkerA/B`, `fountain_loop` está ok, `perimeter_loop` ok) e o tour de câmera `Key2` (coreto mudou).

### A.5 Regras de posicionamento de palmeiras e árvores
**Regra dura (vale para toda árvore, palmeira, arbusto e canteiro de flor; ver seção J):** só entra na cena se `bed_field(p) >= 1.2 + raio_do_tronco`. Nenhum tronco em piso. As listas abaixo são candidatas; o filtro decide.
**Palmeiras** (determinístico, seed 311):
1. Para cada strip diagonal da GV (os 14 do laço acima) : pontos a cada 6,0 m ao longo do eixo, dos dois lados, deslocados `largura/2 + 1,3 m`, jitter ±0,6 m ao longo.
2. Esplanada: z = ±5,4, x de −60 a −46 e de −22 a −8, passo 7 m.
3. 5 em volta de cada largo/rondel, raio + 1,6, ângulos com jitter ±12°.
4. Adro SJ: 2 em (11,3, ±14).
5. Filtro: `can_plant(p, "palm")` (seção J), ≥ 6,5 m do centro do coreto, ≥ 3,2 m de outra palmeira, ≥ 4 m de tronco de árvore grande. Se sobrar mais de 52, descartar por seed até 52.

**Árvores grandes GV** (lista explícita, depois filtro `can_plant(p, "tree_old")`, seção J):
- Borda norte: z = −41, x = −57, −48, −39, −30 (e espelho z = +41). Faixa leste da borda norte/sul já entra nas diagonais abaixo.
- Faixas diagonais do "V": (−33, −40), (−27, −33), (−20, −27), (−14, −21) e segunda linha (−18, −38), (−11, −32); espelhar em z.
- Borda Rua Brasil: x = −9,5, z = ∓40, ∓12 (os outros z já estão cobertos pelas diagonais).
- Total GV ≈ 24. Mantêm o quadrante do coreto e o eixo da esplanada abertos (nenhuma copa a menos de 9 m do eixo z = 0).
- Borda oeste: 6 árvores médias floridas (variante `tree_bloom`, copa 6–7 m rosa #E9A6C0 / lilás #B79AD6) em x = −58,5, z = ∓38, ∓30, ∓10.

**Bosque SJ**: amostragem Poisson (seed 907) sobre os canteiros da SJ, distância mínima 8,5 m entre troncos, `can_plant(p, "tree_old")` (seção J). Esperado 34–40 árvores. Forçar antes da amostragem: (13,5, ±19,5), (13,5, ±24,5) (as gigantes que emolduram a fachada), (20, ±21), (16, ±40). Copas devem se sobrepor 20–30% (teto contínuo). Escala 1,0–1,12 no bosque; 0,9–1,0 na GV.

Canteiro central da avenida: trocar `CommonTree` por `tree_bloom` a cada 16 m (já é esse passo; `tree_old` não cabe, seção J). Quintais: 1 `tree_old` 0,8 por quadra.

---

## B. Árvores e palmeiras (modelos)

Novo gerador `tools_src/build_trees.py` (Blender, bmesh; reusar `make_frustum`/`make_cylinder` de `build_plaza_props.py`) → `art/town/tree_old_1..6.gltf`, `tree_bloom_1..2.gltf`. `add_trees` escolhe `tree_old_{hash(pos) % 6 + 1}`, yaw aleatório por seed.

**`tree_old` (tipuana/sibipiruna/figueira velha, copa em guarda-chuva):**
| Parte | Valor (variar por seed) |
|---|---|
| Altura total | 11–15 m |
| Tronco até a 1ª forquilha | 2,6–3,8 m, 10 lados, leve curva (desvio 0,3–0,6 m) e torção |
| Raio do tronco a 1,3 m | 0,55–0,85 m (diâmetro 1,1–1,7); afina 20% até a forquilha |
| Base | alarga ×1,8 nos últimos 0,8 m + **5–7 raízes tabulares**: aletas triangulares de 1,2–2,0 m de comprimento, 0,5–0,9 m de altura no tronco, 0,18 m de espessura, ângulos irregulares |
| Galhos primários | 3–5, saindo a 35–55° da vertical, 5–7 m, raio 0,28 → 0,12, 6 lados, 1 dobra no meio |
| Galhos secundários | 2 por primário, 2,5–4 m, raio 0,12 → 0,05 (ficam visíveis por baixo da copa: é isso que dá "árvore velha") |
| Copa | 9–14 tufos = icosfera subdiv 2 achatada (escala z 0,55–0,7), raio 2,2–3,6 m, um na ponta de cada galho + 3–4 no topo; ruído de vértice ±0,25 m |
| Diâmetro da copa | **12–18 m**; base da copa a 4,5–6 m do chão (jogador anda por baixo e vê os galhos) |
| Cor (vértice) | por normal.z e altura: baixo/dentro #245A3A → meio #3F8A50 → topo ao sol #7FC46A; tronco #8B5A3C escurecido 25%, raízes com musgo #3F8A50 a 30% na face de cima |
| Orçamento | ≤ 2 500 triângulos, 2 materiais (casca, folha), contorno inverted hull igual às casas |
| Colisor | `KIT_COLLIDERS["tree_old"] = ("cylinder", 0.75, 4.0)`; `tree_bloom`: 0,3 |

Variação entre os 6: nº de galhos, lado da inclinação, copa mais larga (1, 4), mais alta (2), assimétrica (3, 6), com cipós pendentes (5: 6–8 cilindros finos de 1,5–3 m pendurados dos galhos).

**`tree_bloom`**: tronco 0,22 m de raio, forquilha a 2 m, copa 6–7 m em 5 tufos, cor florida.

**Palmeira-imperial** (`build_palm`, hoje tronco 7,2 m × escala ~0,95): parametrizar `trunk_height` e exportar `palm_a` (9,0 m), `palm_b` (11,5 m), `palm_c` (14,0 m). Tronco raio 0,34 na base (bojo a 1/3 da altura: +0,05), anéis a cada 0,6 m; palmito verde 1,3 m; **18 folhas** de 3,6–4,2 m em 3 camadas (as de baixo caídas 20° abaixo da horizontal); folíolos com corte serrilhado como hoje. Distribuição: 50% b, 30% c, 20% a; escala ±6%; nunca duas iguais vizinhas na mesma fileira. Colisor r 0,36.

---

## C. Casas: catálogo e regras de quadra

### C.0 Por que as casas se atravessam hoje (causa medida)
- Os telhados do kit têm beiral lateral de ~1,1 m: `ROOF_BY_FOOTPRINT` dá meia-largura 4,12 para casa de 6 m e 4,98 para 8 m. `house_row` encosta os lotes com folga ~0 → cada telhado entra ~1 m no vizinho.
- AABB das malhas exportadas (lido dos acessores do glTF): `house_shop_narrow_*` x ∈ [−4,12, 4,12] (lote 6); `house_plaster_wide` x ∈ [−4,3, 8,98] (lote 8, descentrado); `house_cottage` x ∈ [−3,3, 7,12] (lote 6, descentrado); `house_shop` profundidade até −10,85 com `HOUSE_ROW_DEPTH = 10`.
- Barraca/placa/props de loja são postos por cima sem checar o vizinho.

### C.1 Regras de lote (valem para tudo que entra numa fileira)
1. **Lote**: largura múltipla de 2 m em {6, 8, 10, 12, 14, 16}; profundidade máx. 12 m. `HOUSE_ROW_DEPTH = 12.5` (recorte de esquina).
2. **Corpo** = largura do lote − 0,30 m (0,15 de cada lado). **Nenhuma** geometria passa de `lote/2 − 0,02` em x (telhado, beiral, chaminé, sacada lateral, hera). Fileira = parede-meia: cumeeira **paralela à rua** (beiral só na frente e no fundo) ou empena para a rua com beiral lateral ≤ 0,13 m; empenas laterais cegas com platibanda/corta-fogo 0,3 m acima do telhado quando o vizinho for mais baixo.
3. Para a frente pode avançar até 1,2 m sobre a calçada (beiral, sacada, andar em balanço, placa); calçada tem 3 m.
4. **Preencher o comprimento exato da fileira** (todas as fileiras atuais têm comprimento par: 90, 54, 24, 14...):
```python
def lot_widths(length, generator, widths=(6, 8, 10, 12)):
    alley = length % 2                      # sobra não-par vira beco (ver item 5)
    remaining, lots = length - alley, []
    while remaining > 0:
        options = [w for w in widths if remaining - w == 0 or remaining - w >= min(widths)]
        lots.append(generator.choice(options)); remaining -= lots[-1]
    return lots, alley
```
   Lotes fixos (lojas da seção D) entram primeiro; os trechos entre eles são preenchidos por `lot_widths`.
5. **Beco**: se sobrar `alley > 0`, vira passagem de 1–2 m entre dois lotes no terço central da fileira, fechada por muro de 2,2 m com portão de madeira (colisor). Beco só quando houver sobra.
6. **Esquina**: o lote da ponta de cada fileira principal usa arquétipo de esquina (duas fachadas); a fileira perpendicular começa 12,5 m depois.
7. **Vizinhos nunca repetem**: mesmo arquétipo proibido a menos de 3 lotes; mesma cor de reboco proibida em lotes adjacentes; alternar altura (não pôr 3 casas seguidas com a mesma altura de cumeeira ±0,5 m).
8. **Sidecar + teste**: o gerador grava `art/town/houses/<nome>.json` com `{"aabb_min": [...], "aabb_max": [...], "lot_width": w, "doors": [...]}`. `build_hub_scene.py` lê e dá `assert` em: AABB ⊂ lote; nenhum par de AABBs de prédios colocados se sobrepõe (rotações são múltiplos de 90°, então é teste de retângulos). Acrescentar teste GUT equivalente sobre `hub.tscn`.

### C.2 Como gerar (para ficarem realmente diferentes)
Novo `tools_src/build_town_houses.py`: casca procedural em bmesh (helpers de `build_cathedral.py`: `make_span`, `make_profile_prism`, `carve`, `map_uvs_per_face`) com as texturas do kit (reboco, pedra, tijolo, telha, madeira em `art/town/textures`), e peças do Medieval Village MegaKit só como **enxertos** (portas, janelas, venezianas, sacadas, chaminés, heras). Um construtor por arquétipo num dicionário `ARCHETYPES = {"sobrado": build_sobrado, ...}`; cada um recebe `(largura, profundidade, seed)`; seed escolhe cor, ritmo de janelas, espelhamento, detalhes. Exportar 3 seeds por arquétipo e por largura usada (~40 modelos, instanciados). Cor por vértice multiplicando a textura (já é o esquema de `build_shop_houses.py`).

Paleta de reboco (além da pedra #E9DCC6/#B9AA92, madeira #8B5A3C, telha #B65A40 da bíblia): cal #F4EFE6, creme #F2E6CF, ocre #E3B76A, rosa-terra #D99A84, azul-cinza #9FB6C9, verde-sálvia #A9C19A, vermelho-óxido #B5533F (só madeira/portas). Telhados: terracota #B65A40 (padrão), telha velha #8A4A3A, ardósia #5E6E8C, cobre-verde #5FA08A (só cúpulas/detalhes). Portas/venezianas: azul-colonial #3E6A9A, verde-garrafa #2F6B4F, vinho #7A2F3A, amarelo-queimado #D9A441.

### C.3 Catálogo (12 arquétipos)
| # | Arquétipo (inspiração) | Lote L × P (m) | Pav. | Telhado | Fachada / aberturas | Materiais e cor | Detalhe que identifica |
|---|---|---|---|---|---|---|---|
| 1 | **Sobrado colonial** (luso-brasileiro) | 8–12 × 10 | 2 | 4 águas baixo (25°), cumeeira paralela, beiral frontal com cimalha e telha capa-canal | Térreo: 3–5 portas-janela em arco abatido; 1º: mesmas prumadas com sacada corrida de ferro | Cal branca, cunhais e molduras em cor (azul, amarelo ou verde), telha terracota | Sacada corrida de ferro, molduras coloridas, pináculos de louça nos cantos do telhado |
| 2 | **Casa térrea de porta e janela** (colonial simples) | 6–8 × 9 | 1 (+ sótão) | 2 águas 30°, cumeeira paralela, platibanda baixa com cornija | Porta + 2 janelas guilhotina com venezianas | Reboco colorido (ocre, rosa, sálvia), barrado de pedra 0,8 m | Platibanda ondulada com pinha no centro, banco de pedra ao lado da porta |
| 3 | **Fachwerk** (enxaimel alemão) | 6–8 × 10 | 3 | Empena para a rua, 55°, beiral lateral 0,12, meia-água cortada no topo (Krüppelwalm) | Térreo pedra; andares em balanço 0,35 m cada; janelas em faixa de 3 | Madeira escura em X e K sobre reboco creme, telha velha | Cruzes-de-santo-andré, floreiras com flores vermelhas, viga entalhada na empena |
| 4 | **Tudor** | 10–12 × 10 | 2 | Cumeeira paralela 50° + **empena cruzada** assimétrica na frente; chaminé alta de tijolo com 2 canos | Bay window de 2 andares, janelas de losangos | Tijolo #A85A45 no térreo, madeira listrada vertical próxima em cima, ardósia | Chaminé torcida, porta em arco tudor, empena cruzada |
| 5 | **Casa de canal holandesa** | 6 × 12 | 3 + sótão | **Empena escalonada** (5–6 degraus) ou em sino, telhado 50° escondido atrás | 3 janelas altas por andar, diminuindo para cima; porta deslocada à esquerda | Tijolo vermelho-escuro com faixas e chaves de pedra clara | Degraus da empena, viga com gancho de içar no topo, óculo no sótão |
| 6 | **Chalé alpino** | 10–12 × 10 | 2 | 2 águas **baixo (22°)** com beiral frontal de 1,2 m sobre mãos-francesas; pedras sobre o telhado | Térreo pedra caiada; 1º todo em tábua horizontal; varanda de madeira na largura toda | Madeira mel #B07A4A, pedra clara, telhas de madeira cinza | Varanda com recortes de coração, floreiras, sino pequeno na empena |
| 7 | **Casa mediterrânea** | 8–10 × 10 | 2 | Quase plano (15°) de telha canal, cumeeira paralela; **terraço** em metade da largura com pérgola | Poucas janelas pequenas com grade, arco de entrada, escada externa lateral dentro do lote | Estuque branco/ocre áspero, telha terracota clara, portas azuis | Pérgola com trepadeira, vasos de barro, chaminé caiada cônica |
| 8 | **Art-déco comercial** (eco da catedral e do calçadão) | 8–10 × 10 | 2 | Plano atrás de **platibanda escalonada** | Vitrine larga no térreo com marquise reta; 1º com 3 janelas verticais entre aletas | Reboco liso creme/rosa com frisos verticais brancos, base de granito cinza | Aletas verticais e degraus no topo, letreiro em relevo, marquise |
| 9 | **Chalé de pedra** (Cotswold) | 8 × 9 | 1,5 | 2 águas 50° de ardósia, 2 **lucarnas** de empena | Porta central com alpendre de pedra, janelas com mainel de pedra | Pedra dourada #D9C08A irregular, ardósia | Lucarnas, roseira trepando, muro baixo com jardim de 1 m na frente (dentro do lote) |
| 10 | **Palacete italianizante** | 10–12 × 10 | 2–3 | 4 águas baixo com **beiral largo sobre cachorros** (só frente/fundo) | Janelas em arco pleno com frontões alternados, cunhais rusticados, piano nobile mais alto (3,8 m) | Estuque ocre ou rosa-terra, pedra clara nas molduras | Loggia de 3 arcos no último andar, cornija forte, balaústres |
| 11 | **Casa-torre normanda** (esquina) | 8 × 8 (esquina) | 4 | Pavilhão íngreme 60° de ardósia com grimpa | Seteiras embaixo, janela geminada em cima, torrinha de escada redonda num canto (dentro do lote) | Pedra cinza-quente, cunhais claros | Torrinha com telhado cônico, mata-cães decorativos |
| 12 | **Casa de mercador hanseática** (tijolo, arcada) | 8–10 × 12 | 3 | Empena para a rua com volutas barrocas; telhado 50° | **Arcada** de 2–3 arcos no térreo (galeria coberta de 2 m de fundo, andável) | Tijolo claro #C98A6A com pedra, telha terracota | Arcada com lampião, relógio de sol na empena |

Extras baratos para mais variedade sem novo construtor: (13) **casa geminada estreita** = #2 com 2 pavimentos; (14) **armazém** = #12 sem arcada, com portão de carroça.

Distribuição: fachadas de praça/avenida (`SHOP_FRONTAGES`) usam todos; ruas de trás priorizam 2, 3, 6, 7, 9. Esquinas: 11, 8 (versão de canto chanfrado) ou 1 (duas fachadas). Com 12 arquétipos × cor × espelho × largura e a regra de "não repetir em 3 lotes", nenhuma vista da praça mostra duas casas iguais.

Remover `build_shop_houses.py` do pipeline e as barracas/quintais de `add_shops` (as lojas agora são prédios, seção D). `build_shops.py` continua só para as **placas** e para os props reaproveitados dentro das lojas.

---

## D. Lojas de RPG: prédios próprios e entráveis

### D.0 Regras comuns
- Gerador: `build_town_houses.py`, construtores próprios em `SHOP_BUILDINGS = {"smith": ..., ...}`; saída `art/town/shops/shop_<tipo>.gltf` + sidecar.
- **Térreo é um salão real**: paredes com espessura 0,3 m e faces internas, forro a **3,6 m** (câmera: `SpringArm3D` de 4,2 m com colisão), salão com fundo ≥ 7 m. Andares de cima são só fachada (forro fechado).
- **Porta**: vão de **1,6 × 2,5 m**, sem folha ou com folhas duplas abertas fixas a 100° para dentro. **Sem degrau**: piso interno em y = 0,00 (nível da calçada), soleira de pedra de 1,6 × 0,3 m nivelada. Nada de plinto sob o prédio.
- **Colisão**: nada de caixa única. Paredes como caixas `*-colonly` separadas (4 lados, a da frente partida em dois pedaços + verga acima de 2,5 m), balcão e móveis grandes com caixa própria, forro com caixa (para a câmera não atravessar).
- **Vitrines**: vãos reais com vidro (alpha 0,25, sem colisão visual extra), dá para ver o interior da praça.
- **Luz**: 2 `OmniLight3D` quentes (#FFD9A0, energia 1,2–1,6, alcance 7, sem sombra, `distance_fade` 45 m) por loja + emissivos (brasa, cristais, lampiões). Janela dos fundos alta para luz fria de contraluz.
- **Lojista**: NPC parado atrás do balcão (`stand()`), virado para a porta. Grupo do nó `shop_<tipo>` mantido para a interação futura.
- **Placa**: a placa pendurada de `build_shops.py` (`shop_<tipo>_sign.gltf`) em braço de ferro a 3,2 m, perpendicular à fachada, ao lado da porta.
- Navmesh: rebake; vão de 1,6 m passa com o raio do agente.
- Props: Quaternius Fantasy Props MegaKit em `tools/vendor/props` (Anvil, Anvil_Log, Workbench, Workbench_Drawers, WeaponStand, Whetstone, Dummy, Shield_Wooden, Sword_Bronze, Axe_Bronze, Cauldron, Bookcase_2, BookStand, Book_Stack, Potion_1/2/4, SmallBottles, Shelf_*, Cabinet, Chest_Wood, Table_Large, Chair_1, Stool, Mug, Barrel, Barrel_Holder, Bed_Twin1/2, Nightstand_Shelf, Chandelier, Lantern_Wall, CandleStick_*, Banner_1/2, Scroll_1/2, Coin_Pile, Peg_Rack, Cage_Small). Copiar os que faltam via `copy_kit_models.py`.

### D.1 Onde ficam (lotes fixos)
Fileira oeste da GV — quadra 4, lado E, fachada em x = −75, olhando para a praça (z de −45 a 45, 90 m):
| z início..fim | Lote | Prédio |
|---|---|---|
| −45..−37 | 8 | residência (esquina, arquétipo 11 ou 1) |
| −37..−27 | 10 | **Armeiro** |
| −27..−15 | 12 | **Ferreiro** (de frente para o coreto/spawn) |
| −15..−7 | 8 | residência |
| −7..7 | 14 | **Guilda dos Aventureiros** (no eixo da esplanada: do chafariz se vê a guilda de um lado e a catedral do outro) |
| 7..13 | 6 | residência |
| 13..25 | 12 | **Taverna** |
| 25..37 | 12 | **Estalagem** |
| 37..45 | 8 | residência (esquina) |

Fileira sul da GV — quadra 7, lado N, fachada em z = 61 (x de −61 a −7, 54 m): res 6 (−61..−55), **Itens Mágicos** 10 (−55..−45), res 8, res 6, **Alquimista** 10 (−31..−21), res 8, res 6.

Fileira norte da avenida — quadra 1, lado S, fachada em z = −69: **Padaria** 8 (−49..−41), **Alfaiate** 8 (−33..−25), **Joalheiro** 6 (−19..−13), resto residências. Quadras 2 S, 5 W, 8 N: residências + 1 **Livraria/Cartógrafo** (quadra 5, lote central) se sobrar tempo.

### D.2 Prédios (frente = +Z local; "esq./dir." vistos de fora, de frente)
| Loja | Exterior | Interior (L × P úteis, porta, balcão, props, luz) |
|---|---|---|
| **Ferreiro** (lote 12 × 12) | Pedra escura no térreo, 1 pavimento + sótão baixo; metade direita é **forja aberta**: alpendre de 5 × 4 m sobre 2 pilares de pedra, telhado de meia-água de ardósia. **Chaminé de pedra larga (1,6 × 1,6, 9 m)** com fumaça (partícula macia). Sem vitrine: armas penduradas em grade de ferro na fachada. Placa: bigorna. | Salão 6,5 × 8 à esquerda, porta no centro do salão. Balcão em L de madeira grossa a 4,5 m da porta. Parede do fundo: `WeaponStand` ×2, espadas/machados em `Peg_Rack`. Alpendre (aberto para a rua e ligado ao salão por vão de 1,6 m): fornalha de tijolo com **brasa emissiva** (#FF7A2A, energia 2,5) + fole, `Anvil` sobre `Anvil_Log`, tina d'água (cilindro com `M_Water`), `Whetstone`, `Workbench`, barras de ferro, carvão. Luz: omni laranja na fornalha (tremulando por script simples ou fixa), 1 omni quente no salão. |
| **Armeiro** (10 × 10) | Arquétipo 12 (tijolo com empena de volutas) sem arcada; **2 vitrines grandes** em arco com armaduras em manequim; escudos pintados na fachada entre as janelas do 1º andar. Placa: escudo. | Salão 9 × 8, porta central. Balcão reto ao fundo (3 m) com `Chest_Wood` atrás. 4 `Dummy` com peitoral/elmo (2 nas vitrines, 2 no centro sobre estrados de 0,2 m com rampa chanfrada — ou sem estrado). Parede esq.: fileira de `Shield_Wooden` em 3 cores; parede dir.: prateleira de elmos e manoplas (caixas/esferas simples), `Workbench_Drawers`. Lustre `Chandelier` no centro. |
| **Itens Mágicos** (10 × 10) | Arquétipo 3 (enxaimel) com reboco azul-cinza e madeira roxa-escura #4A3A5E; **torrinha de canto** com telhado cônico cobre-verde e cristal emissivo na ponta; vitrine de losangos com brilho azul; estrelas pintadas no dintel. Placa: estrela. | Salão 9 × 8, porta à esquerda. Balcão em curva ao fundo-direita com orbe emissivo (#8FD8FF). `Bookcase_2` ×4 nas paredes, `BookStand` com livro aberto no centro sobre tapete redondo, mesa de cristais (prismas emissivos ciano/rosa, energia 1,5), `Scroll` em nichos, `Cage_Small` pendurada, cajados em suporte. Luz: 1 omni azul-fria (#A9C8F0) + 1 quente baixa; partículas lentas de poeira brilhante (16, sprite redondo). |
| **Alquimista** (10 × 10) | Arquétipo 7 (mediterrânea, estuque sálvia) com **alambique de cobre** saindo por cano na lateral frontal e chaminé fina torta soltando fumaça verde-clara; canteiro de ervas em floreiras na janela; vitrine com frascos coloridos. Placa: frasco. | Salão 9 × 7,5, porta central. Balcão reto à direita com balança. Fundo: bancada de laboratório (`Workbench`) com alambique (esferas + tubos de cobre), `Cauldron` sobre fogo emissivo verde (#7FE08A) no canto esq. fundo. Paredes: `Shelf_Small_Bottles`, `SmallBottles_1`, `Potion_1/2/4` em 4 prateleiras; ervas secas penduradas do forro (cones invertidos verdes/lilás); `Barrel` de ingredientes. |
| **Taverna** (12 × 12) | Arquétipo 4 (Tudor) com **terraço coberto** na frente (2 m dentro do lote: 2 mesas, barris), janelas de fundo de garrafa âmbar emissivas, barril-letreiro sobre a porta dupla. Chaminé larga lateral. Placa: caneca. | Salão 11 × 9, porta dupla central (2,0 m). **Bar** em L no fundo-direita (4 + 2 m) com `Barrel_Holder` ×3 atrás e prateleira de canecas. **Lareira** de pedra na parede esquerda (fogo emissivo + omni laranja). 4 `Table_Large` com `Stool`/`Chair_1`, `Mug`/`Table_Plate` nas mesas. Estrado baixo do bardo no fundo-esq. (0,15 m com chanfro). Escada para o andar de cima só cenográfica (primeiros 6 degraus + parede). `Chandelier` ×2. 2–3 NPCs sentados (`Sitting_Idle`). |
| **Estalagem** (12 × 12) | Arquétipo 1 (sobrado colonial, 3 pavimentos aqui) com sacada corrida, lampiões dos dois lados da porta, **portão de carroça** em arco à direita (passagem cenográfica de 3 m de fundo com `Prop_Wagon`). Placa: cama. | Recepção 7 × 8 à esquerda do portão, porta central da recepção. Balcão de recepção de frente para a porta com quadro de chaves (`Key_Gold` em `Peg_Rack`) e livro de hóspedes. À esquerda: canto de estar (lareira pequena, 2 `Chair_1`, tapete). Fundo: vão de 1,6 m para **um quarto** 4 × 4 visitável com `Bed_Twin1`, `Nightstand_Shelf`, `Chest_Wood`, janela. Escada cenográfica. |
| **Guilda dos Aventureiros** (14 × 12) | O maior e mais alto da fileira (3 pavimentos + torreão central com bandeira). Pedra clara + enxaimel no topo, simétrico: **portal em arco de 2,4 m** com escudo da guilda (espadas cruzadas) acima, 2 `Banner_1/2` longos ao lado, 2 braseiros na calçada, janelas altas com mainel. Placa: espadas cruzadas (entalhada, não pendurada). | Salão 13 × 10, pé-direito **duplo (6,5 m)** com vigas aparentes e mezanino cenográfico no fundo. Porta central. **Balcão de recepção** longo (5 m) no fundo com 2 atendentes. Parede direita: **quadro de missões** (painel de madeira 3 × 2 m com pergaminhos `Scroll`/quads) — ponto de interação futuro. Esquerda: 2 mesas de grupo, mapa grande na parede, troféus (cabeças = formas simples; escudos). Centro: tapete com brasão. `Chandelier` ×2 grandes, lareira no fundo-esq. |
| **Padaria** (8 × 9) *(extra)* | Arquétipo 2, reboco ocre; **forno de pedra saliente** com chaminé na lateral frontal, vitrine com pães, toldo listrado (único toldo que sobra). Placa: pão. | Salão 7 × 6, balcão-vitrine de frente para a porta, prateleiras inclinadas de pães atrás, boca do forno emissiva ao fundo, sacos de farinha (`Bag`). |
| **Alfaiate** (8 × 9) *(extra)* | Arquétipo 5 (holandesa), vitrine com 2 manequins de vestido. Placa: carretel. | Salão 7 × 6, balcão à direita, rolos de tecido em nichos (cilindros coloridos), `Dummy` ×3 com roupas, espelho alto. |
| **Joalheiro** (6 × 9) *(extra)* | Arquétipo 8 (art-déco) estreito, vitrine pequena gradeada com gemas emissivas. Placa: gema. | Salão 5 × 6, balcão-vitrine em U, `Chest_Wood`, `Coin_Pile`, gemas (octaedros emissivos fracos), lupa. |

Se o tempo apertar, os 3 extras ficam só com fachada temática e porta fechada.

---

## E. Presbitério (altar-mor, crucifixo, altares laterais, vitrais com pombas)

Referências: `cathedral_interior_1..3.png` (abside com lancetas altas e estreitas dos lados da imagem central, faixa ocre, altar branco com arcadinhas). Coordenadas com as constantes novas da seção G: `NAVE_HALF = APSE_RADIUS = 7.0`, `BODY_LENGTH = 40`, `CHANCEL_FRONT = 33.0`, `F = BASE + CHANCEL_HEIGHT` (piso do presbitério), centro da abside `A = (0, BODY_LENGTH)`. Se a seção G for adiada, multiplicar as medidas em planta por 0,64 (raio 4,5) e manter as alturas ×0,8.

### E.1 Piso e degraus
- Presbitério: `CHANCEL_HEIGHT = 0.9` em 6 degraus de 0,15 × 0,40 na largura toda da nave central (x ±5,5), com **rampa lateral** `-colonly` como hoje (`make_stair_ramp`).
- **Supedâneo** do altar: plataforma de 4,4 × 3,0 m centrada em y = BODY_LENGTH − 0,5, 2 degraus de 0,15 (z até F + 0,30), mármore branco com filete dourado no espelho.
- Piso do presbitério: mármore claro com tapete vermelho #9A2B2B (quad 2,2 m de largura) do último degrau até o altar; faixa de mármore verde-escuro contornando a abside.
- **Mesa de comunhão**: balaustrada (`make_balustrade`) em y = CHANCEL_FRONT + 0,3, de x = −5,5 a −1,3 e de 1,3 a 5,5 (vão central de 2,6 m).

### E.2 Altar-mor (sobre o supedâneo, centro em y = BODY_LENGTH − 0,5)
- **Mensa**: tampo 3,2 × 1,1 × 0,12 m em mármore, topo a F + 0,30 + 1,00; aba de 0,06.
- **Frontal**: em vez de bloco liso, **arcada de 5 arquinhos** (como no altar real): 6 colunetas de r 0,06 com base e capitel dourados, arcos plenos (`round_arch_profile(0.5, 0.55)`), painel de fundo recuado 0,15 m em mármore rosado #E2B9A8; no arco central, medalhão dourado com cruz grega/cordeiro (disco r 0,2 + cruz em relevo).
- Toalha branca: caixa de 3,3 × 1,16 × 0,02 no tampo, caindo 0,25 m nas pontas laterais com barra de renda dourada (faixa de 0,04).
- Sobre a mesa: 6 castiçais altos (3 de cada lado; base cônica, nó, vela de 0,5 m, chama emissiva), crucifixo de mesa pequeno no centro, missal em estante (`BookStand` simplificado).
- Atrás do altar, encostado no retábulo: **sacrário** — caixa 0,6 × 0,5 × 0,8 dourada com porta em arco, cúpula pequena e cruz; lamparina vermelha emissiva pendurada à direita (esfera r 0,07 #FF3B2B em corrente).

### E.3 Retábulo com o crucifixo (substitui `reredos_steps`, os 3 quadros e `ReredosCross`)
Plano do retábulo em y_r = BODY_LENGTH + APSE_RADIUS − 1,3, profundidade 0,7.
- **Predela**: base 6,0 × 0,7 × 1,6 m (z de F a F + 1,6), mármore, com 3 almofadas douradas.
- **Corpo**: edícula central 3,6 m de largura, de F + 1,6 a F + 9,2: duas **colunas caneladas** (`make_fluted_shaft`, r 0,22, 5,2 m) com capitéis dourados (`make_acanthus_leaf`, reaproveitar o capitel da nave em escala 0,5), entablamento com friso dourado, **frontão em arco** com raios dourados; fundo do nicho em **azul profundo #1F3F7A** com estrelas douradas pequenas (painel emissivo fraco 0,2) para a figura clara destacar.
- **Alas laterais** (1,2 m cada, até F + 5,5): nichos em arco com 2 figuras em pé de 1,5 m (`build_saint_figure` escala 0,85: Maria à esquerda sem cajado e com véu = `make_draped_cone` extra sobre a cabeça; João à direita), em mármore.
- **Crucifixo** (peça central, o pedido nº 1 do usuário):
  - Cruz de **madeira escura** #4A2F22: haste 5,2 × 0,30 × 0,22 m, travessa 3,0 × 0,26 × 0,22 a 3,9 m da base; pontas com remate trilobado dourado; base da cruz em F + 2,2 (pé apoiado num pequeno monte de pedra atrás do sacrário); titulus "INRI" = plaquinha 0,5 × 0,18 clara no topo. A cruz fica 0,25 m à frente do fundo azul.
  - **Corpo de Cristo** a partir do mesmo CC0 dos santos: generalizar `build_robed_figure` com parâmetro `tunic: bool` (sem a túnica cônica aqui), partes `("Head", "Hair_Beard", "Eyebrows", "Male_Peasant_Arms", "Male_Peasant_Body", "Male_Peasant_Feet")` + cabelo comprido (trocar `Hair_Buzzed` por um cabelo longo dos outfits se existir no .gltf; senão, modelar calota + 2 mechas caindo até o ombro com `make_draped_cone` r 0,13). Tudo num material só: **marfim/madeira clara policromada** #E8D2B0 (rugosidade 0,6), para a roupa de camponês da malha ler como talha, não como roupa.
  - Pose (`CRUCIFIX_POSE`, mesmo formato de `STATUE_POSE`): `upperarm_l` Y +105°, `upperarm_r` Y −105° (braços abertos ~15° acima da horizontal, mãos nos braços da cruz), `lowerarm_l/r` X −8°, `Head` X +22° e Z +14° (cabeça caída para o ombro direito), `thigh_l/r` X −12°, `calf_l/r` X +24° (joelhos levemente dobrados), `foot_l` sobre `foot_r` (deslocar 0,04 em y e girar Z 10°). Ajustar eixos conforme os nomes reais dos ossos do esqueleto UBC (conferir no .gltf).
  - Acréscimos: **perizônio** = `make_draped_cone("Loincloth", 0.78, 1.08, 0.24, 0.19, 9, 0.03, pano)` em branco-linho #EFE8DA com ponta pendente ao lado direito (cunha de 0,25 m); **coroa de espinhos** = toro r 0,115 / 0,018 com 10 espinhos (cones de 0,03) em #5A3A28; **auréola** = disco dourado r 0,22 com cruz vazada (3 raios), atrás da cabeça; cravos = 3 cilindros r 0,015 escuros; suppedaneum (apoio dos pés) = cunha de madeira.
  - Escala: figura × 1,6 (≈2,9 m); centro do peito a F + 6,3. Deve ser legível do meio da nave.
  - Plano B (se a pose do rig der problema): corpo de formas simples no mesmo material — tronco = cilindro afunilado 12 lados (r 0,2 → 0,15, 0,62 m) com leve S, cabeça = esfera 0,115 inclinada, braços = 2 cilindros de 2 segmentos cada (r 0,05), pernas = 2 de 2 segmentos (r 0,075 → 0,05) com joelhos dobrados, perizônio/coroa/auréola como acima. Mantém a leitura de crucifixo entalhado estilizado.
- **Luz**: `AltarLight` (spot) apontado para o crucifixo: posição (0, y_r − 6, F + 9), ângulo 28°, energia 4, cor #FFE9C4; mais 2 omnis fracos dourados atrás das colunas (contraluz no fundo azul).

### E.4 Abside = vitrais de verdade com pombas da paz
- Substituir as 3 frestas de 0,45 m por **6 lancetas altas** + **óculo** central:
  - Ângulos (0° = eixo, atrás do crucifixo): **±27°, ±52°, ±76°**. Bay central (0°) é cego, é o fundo do retábulo.
  - Cada lanceta: vão de **1,5 m de largura × 9,0 m de altura**, peitoril a F + 3,2, topo em arco pleno (`round_arch_profile(1.5, 8.25)`); moldura interna chanfrada creme com filete dourado; 2 barras horizontais de ferro (caixas de 0,04) a 1/3 e 2/3; parapeito de mármore inclinado.
  - **Óculo** redondo Ø 2,4 m no bay central, centro a F + 11,3 (acima do frontão do retábulo): **pomba branca descendo, de asas abertas, com raios dourados** em 12 gomos (Espírito Santo). É o ponto mais brilhante da igreja.
  - Entre as lancetas: pilastras finas (0,35 × 0,2) subindo até uma cornija a F + 12,6; acima, **semicúpula** pintada azul-celeste #7FA8D8 com nervuras douradas e estrelas (hoje é um tampo liso `ApseRoof`: fazer meia-esfera interna de raio APSE_RADIUS, 12 gomos).
  - Faixa ocre #D9A441 com motivo de arquinhos (como na foto) a F + 2,2 … F + 3,0 em toda a abside; abaixo, lambri de mármore cinza.
- **Textura do vitral** `make_dove_glass_image()` (256 × 1024, mesmo método Voronoi com linha de chumbo de `make_figure_glass_image`, ~900 células), coordenadas normalizadas u ∈ [−0,5, 0,5], v ∈ [0, 1] (0 = base):
  - Fundo: azul cobalto #1E3FA8 na base → azul-céu #6FB3F0 no topo (por v), com 15% das células em turquesa.
  - **Pomba** (branco #F6F4EA, centro em (0, 0,72)): corpo = elipse semi-eixos (0,11, 0,05) girada 30°; cabeça = círculo r 0,04 em (0,10, 0,775); bico = célula dourada em (0,145, 0,785); asa de cima = elipse (0,17, 0,06) girada 65° em (−0,03, 0,82); asa de baixo = elipse (0,15, 0,055) girada −10° em (−0,10, 0,70); cauda = leque triangular de (−0,10, 0,68) a (−0,19, 0,62)/(−0,15, 0,60). Células dentro da máscara ficam brancas com sombra perolada (10% lilás claro).
  - **Ramo de oliveira** no bico: 5 folhas verdes #3F8A50 (elipses pequenas) ao longo de um arco a partir de (0,15, 0,78).
  - **Raios**: 9 cunhas douradas #F2C544 / âmbar #E8962E saindo do centro da pomba para baixo e para os lados (ângulo entre −160° e −20°), só até v = 0,45, alternando com o azul.
  - Terço inferior (v < 0,30): lírios brancos e folhagem verde sobre fundo vermelho-rubi #A8242C; medalhão circular r 0,14 em (0, 0,14) com cruz dourada.
  - Borda (|u| > 0,42 ou v < 0,03 ou v > 0,97): losangos alternados rubi/ouro, como hoje.
  - Lancetas alternam `u` espelhado (pombas voando para o centro) e 3 variantes de matiz dos raios; a de ±27° tem a pomba mais alta (v 0,78), ±76° mais baixa (v 0,66) → composição em arco apontando para o óculo.
  - Óculo: textura 512 × 512 própria (pomba de frente, simétrica, asas abertas para os lados, cabeça para baixo; raios em 360°).
- Material: `glass` emissivo (energia 1,8 nas lancetas, 2,4 no óculo), sem sombra. Para o chão ganhar cor: 3 `SpotLight3D` fracos (azul #7FB0FF, âmbar #FFC766, azul) vindo das lancetas ±27° e do óculo para o piso do presbitério (energia 1,2, ângulo 30°, sem sombra).
- Exterior da abside: mesmas 6 lancetas com moldura e contraforte fino entre elas.

### E.5 Altares laterais (`build_side_altar`, um no fim de cada nave lateral)
- Degrau duplo 3,4 × 2,0 m (2 × 0,15); mesa 2,2 × 0,8 × 1,0 com frontal de **3 arquinhos** (mesma linguagem do altar-mor) e toalha.
- **Retábulo-edícula** 2,6 m de largura × 5,5 m: 2 colunetas caneladas (r 0,12, 2,6 m), frontão triangular com cruz, **nicho em arco de 1,4 × 2,6 m e 0,5 m de profundidade com estátua em vulto** (não pintura): esquerda = Nossa Senhora (figura com véu e manto azul-claro #9FC1E8 em material próprio, mãos postas), direita = São José (`build_saint_figure` com cajado florido, manto marrom #8B5A3C). Escala 1,0 (1,75 m). Fundo do nicho em concha (meia-cúpula canelada dourada).
- 4 castiçais + 2 vasos de flores (`Flower_3/4_Group` em escala 0,35) por altar; **estante de velas votivas** ao lado (grade de ferro 1,0 × 0,4 com 12 velinhas emissivas vermelhas/âmbar); genuflexório de madeira na frente (com colisor).
- Vitral pequeno em arco acima de cada um (lado de fora da parede de fundo), com monograma.
- Luz: 1 omni quente fraco (energia 0,8, alcance 4) por altar.

---

## F. Prioridade e cortes

Ordem (do que mais dói para o usuário / menor custo primeiro):
1. **Casas sem interseção** (C.0, C.1 itens 1–3 e 8): sidecar de AABB + assert + beiral lateral ≤ 0,13 m. Sem isso nada mais convence.
2. **Layout da GV e SJ** (A.4) + **sebes** (H) + **árvores velhas e palmeiras altas** (B, A.5). Um gerador novo (`build_trees.py`) e troca de constantes; maior ganho visual por hora.
3. **Lojas entráveis**: primeiro Ferreiro, Guilda, Taverna, Itens Mágicos; depois Armeiro, Alquimista, Estalagem; por último os 3 extras.
4. **Presbitério**: crucifixo + 6 lancetas de pomba + óculo; depois altar-mor detalhado; depois altares laterais.
5. **Catálogo de casas**: implementar na ordem 1, 3, 8, 5, 2, 7 (seis arquétipos já acabam com "tudo igual"), depois 4, 6, 9, 10, 12, 11.
6. **Catedral maior + bancos em 6 blocos** (G).
7. **Água do chafariz** (I).

Cortes se faltar tempo (nesta ordem): cipós/variantes 5–6 das árvores → topiaria em bola das sebes → interiores dos 3 extras → quarto da estalagem e mezanino da guilda → alas com Maria/João do retábulo (deixar só o crucifixo) → arquétipos 9–12 → névoa e anéis de espuma do chafariz (manter fitas + partícula redonda) → coro/órgão e via-sacra da catedral → escalar a catedral (manter tamanho atual e só refazer bancos/presbitério com fator 0,64 em planta). **Não cortar**: assert de sobreposição, esplanada + remoção do anel/X, sebe em todo canteiro, crucifixo com corpo, lancetas com pomba, porta de 1,6 m sem degrau.

---

## G. Catedral maior, bancos em 3 + 3, melhorias

### G.1 Dimensões novas (real ≈ 29 × 53 m; hoje 20 × 38,5; novo **26 × 47,6** ≈ 0,9 do real)
| Constante (`build_cathedral.py`) | Hoje | Novo |
|---|---|---|
| `HALF_WIDTH` | 10,0 | **13,0** |
| `NAVE_HALF` (eixo das colunas) | 4,5 | **7,0** |
| `APSE_RADIUS` | 4,5 | **7,0** |
| `BODY_LENGTH` | 34,0 | **40,0** |
| `NARTHEX_DEPTH` | 5,0 | 5,0 |
| `PIER_Y` | 10,4…26,6 (4) | **[10,6, 16,2, 21,8, 27,4, 33,0]** (vão 5,6 m; o último é o arco triunfal) |
| `BAY_CENTERS` | 5 | **[7,8, 13,4, 19,0, 24,6, 30,2]** + tramo do presbitério 36,5 |
| `ARCH_WIDTH` / `ARCH_SPRING` | 4,4 / 6,0 | **4,6 / 7,6** |
| `ARCADE_TOP` | 9,0 | **11,2** |
| `AISLE_TOP` | 11,4 | **13,5** |
| `NAVE_CEILING` / `NAVE_WALL_TOP` | 14,0 / 15,5 | **17,5 / 19,5** |
| `TOWER_BASE_TOP` | 17,0 | **22,0**; toda a parte alta da torre × 1,3 (ponta da cruz ≈ 46–48 m: as torres têm de passar bem acima das copas de 15 m) |
| `TOWER_OUTER`, `CENTER_HALF` | 7,0 / 2,8 | **9,1 / 3,6** |
| `PORTAL_WIDTH` / `PORTAL_SPRING` | 4,0 / 4,0 | **4,6 / 4,8** |
| `CHANCEL_FRONT` | 29,0 | **33,0** |
| `AISLE_WINDOW` | (1,5, 6,6) | **(1,7, 7,6)** |
| `CHANDELIER_Y` | 3 | **[8, 14, 20, 26]** |
| `PEW_ROWS` | (8, 26) | **(8,0, 31,0)** |
| `STATUE_SPOTS` | (∓9,6, −2) | **(∓12,2, −2,4)**, `STATUE_SCALE` 1,45, pedestal 2,8 |
| Em `build_hub_scene.py` | `CATHEDRAL_FACADE_X = 18` | **13** (fundo da abside em x ≈ 60,6; praça vai até 64); `add_cathedral_lights`: naves em +8, +15, +22, +29; `Priest`/`worshipper_route` reposicionados |

### G.2 Bancos: 3 blocos à esquerda + 3 à direita
Interpretação adotada de "3 fileiras à esquerda e 3 à direita": **três blocos paralelos de bancos de cada lado do corredor central** (seis colunas de bancos no total, como na foto do interior: dois blocos na nave central de cada lado + um bloco em cada nave lateral), com corredores entre eles. Seção transversal por lado (x a partir do eixo; espelhar):
| Faixa | x (m) | Largura |
|---|---|---|
| Corredor central (meio) | 0 – 1,3 | 2,6 total, com passadeira vermelha |
| **Bloco A** (nave, interno) | 1,3 – 3,6 | banco de 2,3 m |
| Corredor | 3,6 – 4,6 | 1,0 |
| **Bloco B** (nave, externo) | 4,6 – 6,3 | banco de 1,7 m |
| Coluna (eixo 7,0, r ≈ 0,6) + passagem | 6,3 – 8,8 | 1,2 livre depois da coluna |
| **Bloco C** (nave lateral) | 8,8 – 11,2 | banco de 2,4 m |
| Corredor da parede | 11,2 – 12,4 | 1,2 (acesso aos altares laterais e à via-sacra) |
- Fileiras de y = 8,0 a 31,0, passo 1,15 m → 21 fileiras × 6 blocos = 126 bancos (instanciar/mesclar por material). Interromper os blocos em y ≈ 19 (uma fileira a menos = corredor transversal de 1,6 m ligando as portas laterais).
- Banco: assento a 0,45, encosto a 0,95, laterais recortadas com voluta, genuflexório rebatido atrás, madeira castanha #7A4E34 com topo do encosto mais claro. Colisor: uma caixa por **bloco contínuo** entre corredores (altura 0,95), não por banco.

### G.3 Melhorias de interior
- **Arco triunfal** em y = 33,0 separando nave e presbitério: arco pleno de aduelas vermelho/branco maiores, inscrição dourada em faixa, e sobre cada pé-direito uma **estátua em mísula com dossel** (visível em `cathedral_interior_3.png`).
- **Faixa ocre** contínua a 4,2–5,0 m nas paredes laterais com motivo de arquinhos e cordeiro (textura gerada 512 × 128), lambri de mármore cinza até 1,6 m, paredes creme acima.
- **Duas fiadas de vitrais** por tramo, como na foto: lanceta alta em cima (`AISLE_WINDOW`) e janela menor (1,4 × 2,2) embaixo da faixa ocre.
- **Via-sacra**: 14 oratórios pequenos de madeira com frontão (0,5 × 0,8) entre as janelas, a 2,4 m.
- **Teto**: caixotões brancos fundos entre vigas (como na foto), florão dourado no centro de cada caixotão, cornija com dentículos.
- **Coro alto** sobre o nártex: laje a 5,5 m com balaustrada, órgão de tubos (15 cilindros dourados escalonados) e rosácea/trifório da fachada iluminando por trás.
- Nártex: 2 pias de água benta em concha, guarda-vento de madeira com vidro, quadro de avisos.
- Mobiliário: **ambão/púlpito** de mármore à esquerda do presbitério (3 degraus, águia dourada), **cadeira presidencial** + 2 bancos à direita, **pia batismal** octogonal no início da nave lateral esquerda, **confessionário** de madeira (2 × 1,2 × 2,6) na nave lateral direita, credência.
- Piso: granito polido em xadrez creme/cinza na diagonal nas naves, faixa escura no perímetro, passadeira vermelha no corredor central; `roughness` 0,25 para refletir os vitrais.
- Luz: lustres maiores (2 aros, 12 globos), arandelas como hoje; reduzir o ambiente azulado dentro (um `ReflectionProbe` interior com ambiente próprio quente #FFF1DC, energia 0,5) para o creme não esverdear.
- **Portas laterais** no tramo de y ≈ 19 (uma por lado, 1,8 m, com rampa externa em vez de escada).

### G.4 Melhorias de exterior (referência `cathedral_facade_1.png`, `praca_sao_jose_forecourt_1.png`)
- Cor: panos de parede **rosa-salmão #E8B9A6** entre aletas e molduras **brancas #F4EFE6** (hoje é tudo creme); embasamento de granito cinza de 1,2 m.
- Torres: aletas verticais contínuas da base ao topo, 3 recuos escalonados no coroamento, venezianas de sineira, relógio, cruz fina de ferro; sinos visíveis (2 por torre).
- Corpo central: empena escalonada mais alta entre as torres, **trifório de 3 lancetas altas com vitral** sobre o portal (visto de dentro ilumina o coro), balcão com balaustrada entre as torres (existe na foto).
- **Portal** mais fundo: 3 arquivoltas em degrau, tímpano com relevo (pomba/cruz), portas duplas de madeira almofadada 4,6 × 5,0 abertas, 2 lampiões de ferro.
- Laterais: contraforte-pilastra branco por tramo, lanceta alta + janela baixa entre eles, platibanda com balaustrada sobre as naves laterais, cantos frontais arredondados (já existem; manter).
- Telhado: duas águas de **telha terracota** sobre a nave (como na aérea), cumeeira com cruz no encontro da abside; abside com contrafortes, 6 lancetas e meia-cúpula de cobre-verde #5FA08A.
- Escadaria: 7 degraus na largura do corpo central + torres (≈ 18 m), com 2 plintos laterais para os santos e **rampa lateral** real de cada lado (não só colisor); corrimão de ferro central.
- Adro: piso de pedra com rosa-dos-ventos/estrela incrustada na frente do portal, 4 vasos grandes, 2 postes de 3 globos.

---

## H. Sebes em volta de todo canteiro

- **Todo** canteiro (GV, SJ, canteiro central, rotatória, anel do Marco) recebe sebe baixa aparada no perímetro inteiro, não só no lado da rua.
- **Seção**: começa a 0,30 m da borda externa do meio-fio (meio-fio 0,22 + 0,08 de terra), **largura 0,55 m**, **altura 0,50 m acima da grama da borda** (topo ≈ 0,62 m absoluto; altura do joelho). Topo levemente abaulado: chanfro de 0,08 m nas duas arestas + a ondulação de ±0,03 que já existe (reduzir de 0,05). Cor: verde-escuro #245A3A nas laterais, #3F8A50 no topo.
- Em `build_ground.py`: `HEDGE_BAND = (0.30, 0.85)`, `HEDGE_HEIGHT = 0.50`; em `build_beds` trocar o filtro "lado da rua" (campo de índice 3) por um campo novo `gap` (ver abaixo): `hedge_polygons = clip_region(triangles, [(2, 0.30, True), (2, 0.85, False), (gap, 0.0, True)])`. Para o chanfro: gerar a sebe em duas faixas (0,30–0,38 e 0,77–0,85 com topo 0,42; miolo 0,38–0,77 com topo 0,50) ou interpolar a altura pelo campo.
- **Onde os caminhos cruzam**: caminho não é canteiro, então a sebe naturalmente acompanha a borda de cada canteiro e **nunca atravessa um caminho**; nas bocas dos caminhos a sebe dobra junto com o meio-fio (o campo de distância já arredonda a quina convexa com raio ≈ 0,3–0,85 m).
- **Vãos de acesso ao gramado**: 1,6 m de largura. Regra determinística (seed 53) em `build_hub_scene.py` → `hedge_gaps()`: candidatos = pontos de grade de 1 m com `0,30 < bed_field < 0,85`; escolha gulosa com distância mínima de **22 m** entre vãos e ≥ 4 m de qualquer quina (ponto onde o gradiente do campo muda > 40° em 1 m); garantir ≥ 1 vão por canteiro e 1 vão atrás de cada banco que encosta em canteiro. Campo `gap(p) = min(dist(p, centro_i)) − 0,8`.
- **Remates**: nas duas pontas de cada vão, **bola de topiaria Ø 0,7 m** (icosfera) sobre a sebe; nas pontas agudas dos canteiros (cunhas com ângulo < 60°, ou onde o canteiro tem menos de 2,4 m de largura), a sebe preenche a ponta inteira e termina em bola Ø 0,9 m. Em volta de tronco/poste/palmeira dentro da faixa: recorte circular de 0,6 m de raio.
- Canteiros estreitos (canteiro central da avenida): mesma seção; se o canteiro tiver < 2,2 m de largura útil, sebe só nas duas laterais longas.
- Colisão: manter `Hedge*-colonly` (sebe bloqueia; entra-se pelos vãos ou pulando). Altura do colisor = topo da sebe. Refazer navmesh.
- Flores: faixa de 0,4 m de flores baixas (as `Flower_*_Group` em escala 0,5) por dentro da sebe só nos canteiros que tocam o largo do chafariz e o adro.

---

## I. Água do chafariz (fluida, sem quadradinhos)

Problema atual (`features/hub/props/fountain_large.tscn`): tudo é `GPUParticles3D` com `QuadMesh` de 0,06 × 0,16 sem textura → quadrados tremendo. Solução: **malhas contínuas com shader de UV rolando** para todo fluxo de água; partículas só para respingo e névoa, com sprite redondo macio.

### I.1 Malhas (geradas em `build_plaza_props.py`, material `M_WaterStream`, trocadas via `_subresources` como o `M_Water`)
1. **Jatos em arco (8)**: fita-tubo ao longo da parábola do jato atual (v₀ = 5,75 m/s, elevação 63,4° → alcance ≈ 2,7 m, ápice ≈ 1,35 m acima do bico). `p(t) = p0 + v0·t + ½·g·t²`, 28 segmentos × 6 lados, raio 0,03 no bico → 0,075 no fim (o jato abre). UV: `u` em volta, `v` = comprimento de arco em metros / 0,6. Cor de vértice R = progresso 0→1 (para o shader desmanchar a ponta). Os bicos saem das 4 aguadeiras + 4 bicos na borda do tambor, caindo dentro do tanque.
2. **Bicas dos gomos**: cada bacia tem gomos (8 / 10 / 12). Em cada vale de gomo, uma **fita** de 0,16 / 0,20 / 0,26 m de largura caindo em parábola curta (velocidade horizontal 0,55 m/s) da borda da bacia até a superfície de baixo (quedas ≈ 0,64 m, 1,09 m e 2,7 m até o tanque). Fita com 2 quads de largura × 14 de comprimento, arqueada (centro 0,02 m à frente), afinando 25% e depois abrindo 40% no fim.
3. **Véu contínuo** bem fraco em cada bacia: saia cilíndrica do lábio até a superfície de baixo, 48 segmentos, alpha máx. 0,18 (dá a "lâmina" entre as bicas).
4. **Cogumelo do topo**: tubo vertical de 0,35 m (r 0,035) + cúpula em guarda-chuva (meia-esfera r 0,32 achatada 0,6, UV rolando para fora/baixo) como no chafariz real.
5. **Discos de impacto**: quad horizontal de 0,9 m (1,4 m sob as bicas grandes) 5 mm acima da água em cada ponto de queda (8 jatos + 12 bicas de baixo + 1 anel sob cada bacia). Material `M_WaterFoam`.
6. **Superfícies** (tanque e 3 bacias): discos com 24 anéis × 48 setores (hoje é tampa de cilindro sem subdivisão), para o deslocamento de vértice funcionar.

### I.2 Shader das fitas/jatos (`art/shaders/water_stream.gdshader`)
```glsl
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, unshaded;
uniform sampler2D streak_noise : repeat_enable;   // NoiseTexture2D 256, seamless, esticado em v
uniform float flow_speed = 3.2;                    // tiles/s (jato: 5.5; véu: 1.6)
uniform vec3 water_tint : source_color = vec3(0.74, 0.90, 1.0);
uniform float opacity = 0.75;                      // véu: 0.18
void vertex() {
    float along = COLOR.r;                         // 0 no bico, 1 no fim
    VERTEX += NORMAL * sin(UV.y * 16.0 - TIME * 8.0) * 0.006 * (0.3 + along);
    VERTEX.xz += vec2(sin(TIME * 1.7 + UV.y * 2.0), cos(TIME * 1.3)) * 0.012 * along * along;
}
void fragment() {
    vec2 flow_uv = vec2(UV.x * 2.0, UV.y - TIME * flow_speed);
    float streak = texture(streak_noise, flow_uv).r * 0.6 + texture(streak_noise, flow_uv * vec2(3.0, 0.5) + 0.37).r * 0.4;
    float rim = pow(1.0 - abs(dot(normalize(NORMAL), normalize(VIEW))), 2.0);
    float breakup = smoothstep(0.55, 1.0, COLOR.r);                 // a ponta se desfaz em gotas
    float body = smoothstep(breakup * 0.75, breakup * 0.75 + 0.25, streak);
    ALBEDO = mix(water_tint, vec3(1.0), smoothstep(0.55, 0.85, streak) + rim * 0.5);
    ALPHA = opacity * body * (0.55 + 0.45 * streak) * smoothstep(0.0, 0.04, COLOR.r);
}
```
Ruído: `FastNoiseLite` celular/simplex freq 0,03, textura 256 × 256 seamless. Sem sombra projetada (`cast_shadow = off`).

### I.3 Espuma/anéis de impacto (`water_foam.gdshader`, unshaded, blend_mix)
`r = length(UV − 0.5) × 2`; `rings = smoothstep(0.75, 1.0, sin((r × 3.0 − TIME × 1.4) × 6.283) × 0.5 + 0.5)`; `core = 1 − smoothstep(0.0, 0.3, r + (ruído − 0.5) × 0.15)`; `ALPHA = (core × 0.85 + rings × 0.45) × (1 − smoothstep(0.6, 1.0, r))`; cor branca levemente azulada #F2FAFF. Fase aleatória por instância (`INSTANCE_CUSTOM` ou offset por cor de vértice).

### I.4 Superfície (`art/shaders/water.gdshader`, já tem 2 normais rolando: acrescentar)
- Rolagem das normais: (0,03, 0,02) e (−0,02, 0,035) UV/s, escalas 0,35 e 0,8 por metro; força da normal 0,35.
- **Fresnel**: `mix(raso, fundo, ...)` raso #7FD6E0, fundo #2F7FB5; reflexo do céu #D7EEF5 por `pow(1 − NdotV, 4)` × 0,6.
- **Espuma de borda** por profundidade (`hint_depth_texture`): faixa branca onde a diferença de profundidade < 0,12 m, borda quebrada por ruído, pulsando 8%.
- **Ondas radiais** saindo do centro (onde caem as bicas): `sin(dist × 7,0 − TIME × 3,0) × exp(−dist × 0,35)` somado à normal (peso 0,25) e ao deslocamento de vértice (amplitude **0,012 m**; + ruído 0,008 m).
- **Refração leve**: `hint_screen_texture` deslocada por `normal.xz × 0,015`.
- **Brilhos toon**: `step(0,985, dot(reflexo, sol) + ruído × 0,02)` → pontos brancos cintilantes (energia 1,5, entram no glow).
- `roughness 0,08`, `specular 0,6`, alpha 0,82.

### I.5 Partículas (só respingo e névoa)
Textura `T_SoftDrop.png` 64 × 64: gradiente radial branco, alpha `(1 − r)^2` (gerar no script). Material: `StandardMaterial3D` unshaded, alpha, billboard de partícula, `vertex_color_use_as_albedo`, sem `cull`. **Apagar** os emissores `UpperOverflow/MiddleOverflow/LowerOverflow/Jet*` atuais.
| Emissor | Onde | amount | lifetime | Velocidade / forma | Tamanho | Alpha |
|---|---|---|---|---|---|---|
| Respingo de impacto (1 por jato e por bica grande) | ponto de queda | 14 | 0,45 s | para cima 1,2–2,0 m/s, spread 55°, gravidade −9,8 | 0,05 → 0,13 m (curva crescente) | 0,7 → 0 (curva) |
| Gotas da ponta do jato | últimos 30% do arco (caixa pequena) | 10 | 0,35 s | herda a direção do jato (2–3 m/s), spread 12° | 0,04–0,07 | 0,8 → 0 |
| Respingo em anel sob cada bacia | anel no raio da bacia | 60 / 80 / 120 | 0,4 s | radial 0,3–0,6 + cima 0,8–1,4 | 0,04 → 0,10 | 0,6 → 0 |
| Névoa | centro, altura 1,5–4 m (esfera r 1,8) | 24 | 2,6 s | sobe 0,25–0,4 m/s, sem gravidade, turbulência 0,3 | 0,7 → 1,3 m | 0,0 → 0,08 → 0 |
| Cintilação | superfície do tanque (disco r 5) | 20 | 0,6 s | parada | 0,03–0,05 | pisca 1 → 0 |
`fixed_fps = 0` (ou 60) e `interpolate = true` para não "tremer"; `visibility_aabb` cobrindo o tanque todo.

### I.6 Custo e validação
< 4 000 triângulos de água, 3 materiais (stream, foam, surface), ~350 partículas no total (hoje: ~1 000+). Validar com print a 1,6 m de altura a 6 m do tanque e recorte 3× das bicas: nenhuma aresta de quad visível, fluxo contínuo do lábio até a superfície, espuma onde a água encosta. Aplicar a mesma receita (1 bacia, 1 cogumelo, véu) em `fountain_small.tscn`.

---

## J. Árvores só em canteiro, passeios livres (correção de bug)

Causa do bug atual: em `add_trees`, as listas `sao_jose` e `sao_jose_extra` não passam por `on_lawn()`. `sao_jose_extra` põe troncos em z = ±30, em cima dos passeios de z = ±31; os de dz = 21 caem na beira do passeio em volta da catedral. Só as palmeiras são filtradas hoje.

Regra única, aplicada num só lugar (`can_plant()` em `build_hub_scene.py`, usada por árvores, palmeiras, arbustos, flores e tufos):
```python
TRUNK_RADIUS = {"tree_old": 0.75, "tree_bloom": 0.3, "palm": 0.36, "bush": 0.5}
PLANT_CLEARANCE = 1.2          # do meio-fio do canteiro até a casca
ROOT_CLEARANCE = {"tree_old": 2.4}   # raízes tabulares chegam a 2,0 m do eixo

def can_plant(point, kind):
    return bed_field(point) >= ROOT_CLEARANCE.get(kind, PLANT_CLEARANCE + TRUNK_RADIUS[kind])
```
- `bed_field` já é a distância assinada até a borda do canteiro (positivo = dentro). Isso garante de uma vez: tronco dentro do gramado, ≥ 1,2 m do meio-fio, fora de qualquer caminho/largo/adro e por dentro da sebe (faixa 0,30–0,85).
- Candidato reprovado é **descartado**, nunca empurrado para o lado (evita amontoar na borda). As listas de A.5 foram escolhidas para passar; a amostragem Poisson da SJ rejeita antes de aceitar.
- A copa pode e deve avançar sobre os caminhos (é a sombra do bosque); só o tronco é restrito. Base da copa ≥ 4,5 m: nada bate na cabeça nem na câmera.
- `assert` no fim de `add_trees`: nenhum item plantado com `bed_field < 1.2`. Teste GUT: nenhum colisor de tronco sobre piso (ponto do tronco com `ground_height == 0`).
- O inverso para postes e bancos: `bed_field(p) <= -0.4` (ficam no piso, nunca no gramado).
- Canteiro central da avenida (~3 m úteis): `tree_old` não passa na regra; usar `tree_bloom` ali.

**Sebes (confirmação da seção H):** hoje `HEDGE_HEIGHT = 0.8` somado ao canteiro já elevado (`bed_height`, 0,12–0,38) dá caixas de ~1,1 m (cintura), e só em parte do perímetro. Fica: **0,50 m de altura, 0,55 m de largura, contínua em todo o perímetro de todo canteiro**, topo chanfrado, interrompida só nos vãos de 1,6 m. Topo fixo em `LAWN_EDGE_HEIGHT + 0.50` (≈ 0,62 m do piso), sem somar o abaulado do canteiro.

---

## K. Fonte pequena da avenida → rotatória de verdade

Problema: `ROUNDABOUT = (0, -57)` com `ROUNDABOUT_RADIUS = 9.0` ocupa a largura inteira da avenida (z de −66 a −48 = 18 m): não sobra pista em volta, a fonte fica entalada no canteiro central.

Decisão: **manter a fonte e fazer a rotatória real** (é o cruzamento da avenida com a Rua Brasil, o eixo que leva ao Marco e à catedral; a avenida real tem rotatórias pequenas no canteiro).

Geometria (centro C = (0, −57)):
| Elemento | Raio (m) |
|---|---|
| Fonte pequena (`fountain_small`), tanque | 0 – 1,6 |
| Anel de piso de pedra em volta da fonte (sem bancos) | 1,6 – 2,4 |
| Canteiro em anel: gramado + flores (seção L), sebe 0,5 m na borda externa, 4 `palm_a` a r 3,5 nas diagonais | **2,4 – 4,6** |
| Meio-fio da ilha (0,16 de altura) | 4,6 – **5,0** |
| **Pista em anel** (pedra de rua, rebaixada `STREET_DROP`), 5,5 m de largura | **5,0 – 10,5** |
| Meio-fio externo | círculo r 10,5 |
- Constantes: `ROUNDABOUT_ISLAND_RADIUS = 5.0`, `ROUNDABOUT_OUTER_RADIUS = 10.5`, `ROUNDABOUT_LAWN_RADII = (2.4, 4.6)`.
- Como 10,5 > 9 (meia-largura da avenida), **recortar em arco** as calçadas que entram no círculo: em `build_ground.py`, toda laje (quadras 1 e 2 ao norte, cantos das duas praças ao sul) perde a parte com `dist(p, C) < 10.5`; o meio-fio acompanha o arco. O recorte chega a |x| ≈ 5,4 em z = −66 e em z = −48: só come canto de calçada (fachadas começam em |x| = 7, z = −69; `LAWN_RECTS` começam 4 m para dentro das praças). O assert de AABB (C.1) confere que nenhuma casa de esquina entra no círculo de r 11.
- **Canteiro central da avenida** termina antes: `MEDIAN_BEDS` de |x| = 14,5 para fora, com **nariz arredondado** (semicírculo r 3) apontando para a rotatória; entre o nariz e o anel, pista livre.
- A Rua Brasil (x ±4) desemboca no anel ao sul e ao norte com a largura que tem. Sem ilhas divisoras.
- Incrustação de pedra clara no anel de pista a r 7,7 ± 0,15; 4 travessias em pedra clara (2,5 m) nos quatro braços, logo fora do círculo.
- Postes: os 6 atuais a r 7,5 cairiam no meio da pista → 8 postes a **r 11,3**, 2 em cada canto recortado; nenhum na ilha.
- Colisão: ilha com saia em rampa como os outros meios-fios; fonte mantém o colisor. `MedianWalker*` param em |x| = 16.
- A fonte pequena recebe a receita de água da seção I.

---

## L. Flores nos gramados

Referência: nas fotos reais os gramados têm manchas baixas de flor e folhagem junto aos caminhos e em volta do chafariz, não flores gigantes soltas. Hoje: `Flower_3/4_Group` em escala 1,3 viram tulipas de 1,5 m no meio da grama (`LawnEye.png`). **Remover** esses usos dos gramados (ficam só nos vasos do adro, escala 0,6).

### L.1 Modelo
Canteiro de flor = malha gerada em `build_ground.py` (`build_flower_beds`), não instâncias soltas:
- Base: mancha de forração #245A3A abaulada (+0,10 m no centro), contorno orgânico (raio × (1 + 0,12 · ruído)).
- Flores: tufos baixos de **0,22–0,38 m** = 2 quads cruzados de folha (#3F8A50) + 3–5 cabeças (discos de 6 lados/octaedros achatados, Ø 0,09–0,14) coloridas por vértice. **Densidade 9 tufos/m²**, posição e rotação com jitter; tudo mesclado numa malha por praça, 1 material, sem alpha. `visibility_range_end` 70 m.
- Cores (a bíblia não lista flores; usar esta faixa quente/pastel, que conversa com o telhado #B65A40 e o céu #5C8FD1): vermelho #D9483B, amarelo #F2C544, laranja #E8962E, branco #F4EFE6, rosa #E9A6C0, lilás #B79AD6. **Cada mancha: 1 cor dominante (80%) + branco ou amarelo (20%)**; nunca arco-íris na mesma mancha.
- Sem colisão. Toda mancha fica com `bed_field >= 1.0` (por dentro da sebe) e a ≥ 1,5 m de tronco.

### L.2 Onde
| Tipo | Forma | Onde | Cor |
|---|---|---|---|
| **Bordadura da esplanada** | faixa de 0,8 m (`bed_field` 1,0–1,8) nas bordas de canteiro que tocam a esplanada (|z| 4–6,5; x de −60 a −46 e de −22 a −8) | GV | trechos de 6 m alternando vermelho / amarelo |
| **Coroa do chafariz** | faixa de 1,0 m (`bed_field` 1,0–2,0) na borda dos canteiros voltada para o largo (dist. ao chafariz 11–13,5) | GV | vermelho com branco |
| **Meias-luas dos largos** | crescente de 0,9 m em volta de cada largo/rondel (dist. ao centro: raio + 1,0 a raio + 1,9), interrompido onde saem caminhos | 4 largos | oeste: rosa; leste: lilás |
| **Canteiros redondos** | disco r 1,8–2,4 no ponto de `bed_field` máximo de cada gramado com área > 250 m² | GV (≈ 8) | laranja com amarelo |
| **Anel do coreto** | faixa de 0,8 m (dist. ao coreto 5,6–6,4), aberta 60° na frente da escada | GV | branco com rosa |
| **Pé das palmeiras** | disco r 0,7 em 1 a cada 3 palmeiras | GV | amarelo |
| **Adro** | 2 faixas de 1,0 × 8 m nos canteiros dos lados do adro + os 4 vasos | SJ | branco e vermelho |
| **Clareiras do bosque** | 6 manchas r 1,5–2,5 onde a Poisson deixou vão ≥ 7 m; folhagem de sombra mais alta (0,4 m, #3F8A50/#7FC46A) com poucas flores, 4 tufos/m² | SJ | branco, lilás |
| **Rotatória e Marco** | anel de 0,9 m por dentro da sebe | K, A.4 | vermelho (rotatória), amarelo (Marco) |
| **Canteiro central da avenida** | manchas de 3 × 1 m a cada 16 m, entre as árvores | avenida | alterna rosa / laranja |
- Arbustos floridos (`Bush_Common_Flowers`): 8 em volta do largo do chafariz, **dentro** do canteiro (r 12,4, passando por `can_plant(p, "bush")`), e 2 por largo secundário.
- Tufos de capim: 60 por praça, escala 0,3–0,4, nunca em cima de mancha de flor.
- Total esperado ≈ 420 m² de flor (≈ 3 800 tufos, ~40 mil triângulos). Se pesar: 6 tufos/m² e cortar clareiras do bosque e pé das palmeiras.

### L.3 Encaixe na prioridade (seção F)
J faz parte do item 2 (pré-requisito do layout). K e L vêm logo depois do item 2, no mesmo `build_ground.py`: primeiro K, depois L (bordadura da esplanada, coroa do chafariz e meias-luas primeiro; o resto é corte fácil).
