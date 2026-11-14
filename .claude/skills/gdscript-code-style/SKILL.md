---
name: gdscript-code-style
description: Carregar antes de escrever ou editar qualquer GDScript ou shader do jogo. Guia oficial de estilo GDScript + gdlint/gdformat + regras do projeto (sem laço dentro de laço, dispatch por Dictionary em vez de if/match, declarações primeiro, nomes completos, código espaçado).
---

# Estilo de código GDScript

Base: guia oficial de estilo do GDScript (https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html), checado por gdtoolkit. Regras extras do projeto adaptadas do archetypal-webservice. Valem para `core/ net/ world/ features/ data/ tests/`. Scripts geradores em `tools_src/` podem ser mais soltos, mas sem laço aninhado sem motivo.

## Linter e formatador (obrigatório depois de editar)
```
tools/pyenv/Scripts/python.exe -m gdtoolkit.formatter core net world features data tests
tools/pyenv/Scripts/python.exe -m gdtoolkit.linter core net world features data tests
```
Configuração em `gdlintrc` (raiz). Zero aviso antes de commit. Tipagem estática sempre (`var speed: float = 4.0`, `func walk_to(target: Vector3) -> void`). Ligar `debug/gdscript/warnings/untyped_declaration` como aviso.

## Nomes
- Arquivos e pastas snake_case; `class_name` e nós PascalCase; funções e variáveis snake_case; constantes e membros de enum UPPER_SNAKE_CASE.
- Sem abreviação: `player_controller`, não `pc`; `velocity`, não `vel`; `request`, não `req`. Contador de laço curto (`index`) só quando óbvio.
- Função diz o que faz, com verbo: `spawn_walking_npcs()`, `build_floor_layout(seed)`, `apply_hit_damage(hit)`. Nada de `process()`, `do_stuff()`, `handle()` genérico.
- Booleanos como pergunta: `is_grounded`, `has_boss_been_defeated`.

## Ordem no arquivo (gdlint `class-definitions-order`)
`@tool`, `class_name`, `extends`, docstring, `signal`, `enum`, `const`, variáveis estáticas, `@export`, variáveis públicas, privadas (`_`), `@onready`, depois `_init`, `_ready`, `_process`/`_physics_process`, métodos públicos, métodos privados.
Tipos de dados primeiro, lógica depois. Muitas constantes/enums compartilhados vão para arquivo próprio no mesmo módulo (`floor_constants.gd`).

## Dentro da função
- Declarar as variáveis no topo da função, antes da lógica.
- Separar cada etapa (carregar, indexar, montar, aplicar, retornar) com uma linha em branco. Nunca blocos grudados.
- Linha em branco antes de `if`/`for`/`match` e antes de `return` quando há código acima.
- Nunca passar chamada direto como argumento: nomear antes.

```gdscript
func spawn_walking_npcs(route_points: Array[Vector3]) -> void:
	var npc_count: int = route_points.size()
	var npc_scene: PackedScene = NPC_SCENE

	if npc_count == 0:
		return

	for route_point in route_points:
		var npc: WalkingNpc = npc_scene.instantiate()

		npc.position = route_point
		add_child(npc)
```

## Sem pilha de if: dispatch por Dictionary
Para mapear um discriminador (enum, ação, estado) para comportamento, usar `Dictionary` de `Callable` indexado pelo enum, não cadeia de `if/elif` nem `match` longo. `match` só quando os ramos têm formas realmente diferentes.

```gdscript
enum HitKind { SLASH, PIERCE, BLUNT }

var _hit_reactions: Dictionary[HitKind, Callable] = {
	HitKind.SLASH: _react_to_slash,
	HitKind.PIERCE: _react_to_pierce,
	HitKind.BLUNT: _react_to_blunt,
}


func react_to_hit(kind: HitKind) -> void:
	var reaction: Callable = _hit_reactions[kind]

	reaction.call()
```

Valores simples: Dictionary de dados (`const MOVE_SPEED_BY_STANCE := {Stance.WALK: 2.0, Stance.RUN: 5.5}`).

## Retorno antecipado, não else
Guard clauses no começo; caminho feliz no menor nível de indentação. `else` só em ramo binário simétrico. Valor simples: `var x := a if cond else b`.

## Enums, não strings soltas
Conjunto finito de valores (estado de NPC, tipo de dano, modo de rede) = `enum`. Nada de comparar string.

## Laços
- Proibido laço dentro de laço. Se precisa cruzar duas coleções, montar antes um índice (`Dictionary` por id/célula) e fazer um laço só com consulta O(1).
- Grade 2D (geração de mundo): percorrer um índice plano (`for cell_index in grid_size.x * grid_size.y`) e converter para coordenada com função nomeada (`cell_from_index`), ou iterar uma lista de células pronta.
- Várias passadas curtas e legíveis sobre o mesmo array são aceitáveis. Quando acumulam, uma função privada percorre uma vez e preenche um resultado com vários campos.
- Nada de busca (`find`, `has` em Array) dentro de laço: usar Dictionary.
- Hot path (`_process`, `_physics_process`): nada de alocar arrays/dicionários por frame, nada de percorrer a cena inteira.

## Encadeamento
Duas ou mais chamadas encadeadas: uma por linha, a partir da segunda, com indentação extra. Tween é o caso comum:
```gdscript
var tween: Tween = create_tween()

tween.tween_property(door, "rotation:y", PI / 2.0, 0.4) \
		.set_trans(Tween.TRANS_SINE) \
		.set_ease(Tween.EASE_OUT)
```

## Um script por responsabilidade
Um `class_name` por arquivo. Classe auxiliar vai para arquivo próprio ou vira método privado.

## Comentários
Código autoexplicativo por nome. Comentário só para o porquê não óbvio (limite de rede, decisão de design). Docstring `##` em classes e funções públicas de `core/` e `net/`.

## Shaders (.gdshader)
Mesmo espírito: uniforms com nome completo e `hint`, funções nomeadas por efeito (`toon_ramp`, `rim_light`), sem laço aninhado no fragment.
