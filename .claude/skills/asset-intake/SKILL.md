---
name: asset-intake
description: Regras para trazer qualquer modelo, textura, animação, shader ou addon de terceiros para o projeto (licença, pasta, crédito, pipeline Blender→Godot). Use antes de baixar ou importar asset.
---

# Entrada de assets

## Licença (repo é público)
- Aceito: CC0, CC-BY (crédito em CREDITS.md), MIT/BSD/Unlicense (código/shader), VRM com "Redistribution: Allow" e modificação permitida.
- Proibido no repo: Mixamo (proíbe redistribuir arquivos brutos), CC BY-NC, licenças de marketplace (CGTrader, Booth padrão), GPL dentro do código MIT, qualquer coisa de jogo/anime existente.
- Ler a página de licença real antes de baixar. Registrar em CREDITS.md: nome, autor, URL, licença, data.
- Downloads vão para pasta nova vazia no scratchpad; nunca executar scripts deles.

## Fontes aprovadas (ver docs/research/assets.md)
- Animações: Quaternius Universal Animation Library 1/2 (CC0), KayKit Character Animations (CC0).
- Ambiente: Quaternius Medieval Village MEGAKIT, Stylized Nature MegaKit (CC0), Kenney Fantasy Town Kit (CC0), Poly Haven texturas/HDRI (CC0), ambientCG (CC0).
- Shaders: eldskald/godot4-cel-shader (MIT), godot-vrm MToon (MIT).
- Peças de destaque (catedral, fonte, postes, bancos) são modeladas no Blender por nós, porque os kits livres são low-poly demais.

## Pipeline
1. Fonte editável: `art/src/*.blend` (gerados por `tools_src/*.py` quando procedural).
2. Blender em background: `"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python tools_src/x.py`.
3. Exportar glTF binário (.glb) para `art/models/`, escala 1 unidade = 1 m, Y para cima, origem no chão.
4. Personagens: VRM 1.0 → godot-vrm → MToon. Esqueleto mapeado para `SkeletonProfileHumanoid` (BoneMap) para retarget das animações CC0.
5. Normais suavizadas para o contorno (inverted hull) em peças com aresta dura.
6. Texturas: 2048 por personagem, 1024 por conjunto de prédios; albedo pintado, sem normal map no rosto.
