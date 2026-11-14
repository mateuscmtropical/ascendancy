---
name: style-bible
description: Bíblia de estilo visual do jogo (paleta, luz, contorno, proporções, materiais, o que fazer e não fazer) e como validar visual com prints. Use em qualquer trabalho de arte, shader, cena ou iluminação.
---

# Bíblia de estilo

Alvo: fantasia anime cel-shaded, limpa, clara e fresca ("fresh, bright, clean, anime-like"). Clima de cidade medieval europeia luminosa com catedral gótica, praças de pedra, fontes e muito verde. Nada copiado de SAO, Genshin ou Monster Hunter.

## Paleta (hex)
- Céu: zênite #5C8FD1, horizonte #D7EEF5, sol #FFE2B0
- Pedra: luz #E9DCC6, meio #B9AA92, sombra fria #7C7E98
- Madeira #8B5A3C, telhado #B65A40
- Folhagem: #7FC46A, #3F8A50, #245A3A
- Pele: luz #F7D6C4, sombra #E2A7A3 (rosada, nunca cinza), sombra funda #A97A8F
- Contorno: base #2B2236 tingido ~35% com a cor do material

## Luz e pós
- Renderer Forward+. Sol único quente #FFE6C4, 35–45° de elevação, 2–3 cascatas, sombra até ~60 m.
- Preenchimento do céu frio #A9C8F0 ~30% do sol. Rim light nos personagens #BFE6FF, oposto ao sol.
- Tonemap Linear ou Filmic leve + LUT 3D. Glow com threshold ~1.0, Screen, intensidade baixa.
- Névoa de altura leve, Sun Scatter, aerial perspective 0.3–0.4.
- GI: LightmapGI assado na cidade; SSAO + SSIL meia resolução. Nada de SDFGI no mundo aberto.

## Contorno
Inverted hull (next_pass, cull_front, deslocamento pela normal). ~1.5 px em 1080p, escalado pela distância (0.8–2.5 px), some depois de ~40 m. Normais suavizadas em aresta dura.

## Personagens (aprovado pelo usuário em 2026-11-14)
- Base: Quaternius Universal Base Characters (CC0), homem e mulher, com o desenho original deles: corpo estilizado de proporção quase realista (~7.5 cabeças), rosto estilizado, cabelo em mechas. Referência: `C:\Users\mateu\Downloads\jogo\base_personagens_cc0.png`.
- Não trocar por cabeça anime. Manter o design; acrescentar roupa de aventureiro/armadura de fantasia, cabelos e acessórios no mesmo nível de detalhe.
- Sombreamento: suave com rampa leve (2–3 faixas com transição macia) + rim light; não cel duro. Mesmo esqueleto humanoide (retarget das animações CC0).
- NPCs: mesmas bases variando roupa, cabelo, tom de pele e cor.

## Materiais
- Máx. 3 faixas de rampa + specular toon. Albedo pintado à mão; sem roughness em pedra; sem normal map no rosto.

## Não fazer
ACES/AgX como padrão; SDFGI aberto; Freestyle em runtime; contorno preto puro; sombra cinza dessaturada; normal map fotorrealista em rosto; copiar asset ou mapa de jogo existente.

## Validação (obrigatória)
Depois de qualquer mudança visual: print na visão do jogador (olho 1.6 m) e recortes ampliados 2–3x das áreas mudadas (skill `godot-run`). Conferir paleta, contorno, sombras coloridas, sem serrilhado/z-fighting, sem objeto flutuando ou afundado. Comparar com prints anteriores.
