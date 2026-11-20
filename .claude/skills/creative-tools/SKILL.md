---
name: creative-tools
description: Inventory of every external creative resource available to Ascendancy work (voice TTS, AI music, AI 3D models, AI images, browser helpers) with keys, endpoints, verdicts, licensing and how to drive each. Use when planning any video, audio, voice, music, model or art task, so no available resource is forgotten.
---

# Recursos criativos disponíveis

Antes de qualquer vídeo, voz, música, modelo ou arte: passe por esta lista e use o que ajudar. Chaves ficam em `.env` na raiz (fora do git via `.git/info/exclude`; nunca commitar, nunca imprimir o valor).

| Recurso | Uso | Como acessar | Situação |
|---|---|---|---|
| Fish Audio TTS | narração de trailer, falas de NPC | API `POST https://api.fish.audio/v1/tts`, header `model: s2.1-pro-free` (grátis), `Authorization: Bearer $FISH_AUDIO_API_KEY` | aprovado em inglês |
| Google Flow (música) | trilha de vídeo, música do jogo | navegador Opera logado na conta do dono, via ajudante Haiku | liberado pelo dono |
| Tripo 3D | estátuas, relicários, monstros, peças de destaque | Studio no navegador (créditos grátis da conta, ~55 por geração) via ajudante Haiku; API `api.tripo3d.ai/v2/openapi` com `$TRIPO_API_KEY` (saldo da API é separado, hoje zero) | a testar |
| Gemini / IA de imagem web | referências e concept art | navegador; apagar os chats criados na rodada depois | conforme memória |
| Blender 5.2 | modelagem procedural, limpeza de malha | `"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python tools_src/x.py` | padrão |
| ffmpeg / Python (numpy) | montagem de vídeo, música procedural, análise | linha de comando | padrão |

## Voz (Fish Audio)
- O jogo será em **inglês**: narração e NPCs em inglês. Sem `reference_id` + texto em português sai sotaque de Portugal e soa IA.
- Voz padrão em inglês (sem `reference_id`) foi aprovada ("MUITO BOA", fala do padeiro). Vozes da biblioteca: buscar por `GET https://api.fish.audio/model?language=en&title=...`.
- Não usar vozes que clonam ator ou personagem conhecido (repo público).
- Corpo JSON em UTF-8 (montar com Python; `curl -d` com acento quebra).
- Para disfarçar o tom de IA no jogo/vídeo: reverb do lugar, EQ, ambiente por baixo.

## Música (Google Flow)
- Instrumental, sem voz. Estilo preferido do dono: pad ambiente quente, arpejo de sinos/celesta, batida leve (o do `ascendancy_trailer.mp4`); NÃO orquestral épico.
- Baixar para `Downloads`, anotar o prompt e os termos de uso mostrados.

## Modelos (Tripo)
- Termos de uso: saída do plano grátis é pública e com direito autoral renunciado (sem crédito obrigatório); páginas de ajuda/preço se contradizem — vale o Termo. Plano pago = privado e comercial.
- Comunidade: quase só dragões/anime; checar origem (modelo feito de imagem de terceiros ou franquia = não usar), licença e preço de export (~5 créditos).
- Anime não combina com o guia de estilo (`style-bible`). Toda peça passa pelo Blender (malha, escala 1 u = 1 m, origem no chão) e entra em `CREDITS.md` (link, autor, data, prompt).

## Ajudantes
- No máximo 1 ajudante Opus/Sonnet ao mesmo tempo; ajudantes Haiku extras podem (baratos).
- Navegador (Opera, ferramentas `mcp__opera__*`) só por ajudante Haiku, numa aba própria, sem mexer nas abas do dono, sem comprar nem mudar conta. Screenshots do Opera só gravam dentro das pastas de trabalho (scratchpad), não em Downloads.
