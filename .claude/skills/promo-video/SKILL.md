---
name: promo-video
description: Use BEFORE planning, recording, editing or delivering ANY Ascendancy promo/marketing/trailer video. Lists every video already made (never repeat its story, look, music or technique), trailer best practices, the recording/edit pipeline, the review checklist and the delivery rules.
---

# Vídeos de divulgação

Regra do dono: **cada vídeo é novo em história, estilo, música E técnica.** Refazer um formato aprovado, só com o jogo atualizado, é rejeitado ("fez igual o outro, mas pior"). Um vídeo de marketing mostra **tudo que o jogo tem até agora**, não um ponto só.

## Antes de começar
1. Releia a tabela "Já feitos" e escolha conceito + técnica fora dela. Na dúvida, mande um ajudante Haiku pesquisar ideias de trailer e escolha uma que não repita.
2. Liste o que existe no jogo HOJE (todos os PRs abertos: interiores, fazenda, céu, animais, combate, mobs) e monte o vídeo cobrindo tudo. Para filmar o que ainda não está na main, grave numa worktree local com as branches mescladas (sem push).
3. Use todos os recursos da skill `creative-tools`: narração (Fish Audio), música gerada (Google Flow), modelos (Tripo) quando ajudarem.
4. Se o prazo só permitir repetir formato, avise ANTES e deixe o dono decidir.

## Já feitos (não repetir)
| Vídeo | Conceito | Técnica | Música |
|---|---|---|---|
| promo/tour (`promo_shots.gd`, `promo_director.gd`, `full_shots.gd`) | passeio pela cidade | câmeras de jogo em rota, cortes simples | pad ambiente + sinos (`compose_promo_music.py`) — estilo que o dono prefere |
| drone (`drone_reel.tscn`) | sobrevoo | câmera aérea contínua | — |
| épico | — | — | orquestral épico (`compose_epic_music.py`) — o dono NÃO gostou do estilo |
| trailer de marketing (`marketing_shots.gd`, `marketing_timeline.py`, `cut_marketing_trailer.py`) | lenda da mula em cold open, cidade, noite, luta | clipes 60 fps + edição ffmpeg no beat, cartelas Cinzel, grade por ato, letterbox, câmera lenta | `compose_marketing_music.py` |
| "Uma noite em Ascendancy" v1/v2 (`night_take_director.gd`, `night_take_route.gd`) | heroína da praça à cripta e de volta, dia virando noite | plano-sequência sem corte; v2 com câmera em órbita, lanterna | `compose_night_take_music.py` |

Acrescente uma linha aqui a cada vídeo entregue.

## Boas práticas de trailer (pesquisa 2026-11-20)
- Jogo de verdade nos primeiros 2–3 s; nada de logo, fade ou lenda narrada abrindo. Logo/título só no fim (≤ 3 s).
- Gênero claro cedo (exploração, combate). Promessas concretas, não "mundo profundo".
- 60–90 s para o trailer principal da Steam; parar quando acabar material novo.
- Muita gente assiste sem som: a imagem conta sozinha; narração e texto não competem ao mesmo tempo.
- Steam: 1920x1080, 30/60 fps, H.264/AAC. Os 6 primeiros segundos viram o microtrailer.
- Fontes: derek-lieu.com (estrutura Gênero → Gancho → Conteúdo), partner.steamgames.com/doc/store/trailer, howtomarketagame.com.

## Pipeline
- Gravar: `bash tools_src/record.sh <cena.tscn> <saida.avi>` (roda checagem headless antes e falha em qualquer ERROR; janela fora da tela, sem som). Movie writer em fps fixo: o tempo do jogo segue o vídeo.
- Diretor em `tests/promo/<nome>_director.gd` + roteiro em `<nome>_route.gd`/tabela; luz do dia por `hub.set_time_of_day(t)`; esconder UI e avisos do jogo (ex.: `$Prompt` do `SecretPassage`).
- Céu final: se a branch do céu ainda não entrou, gravar com `git show <commit>:art/shaders/sky.gdshader > art/shaders/sky.gdshader` sem commitar.
- Música/narração: gerar antes e cortar o vídeo nos tempos dela, ou retimar as deixas (`CUES`) pelas durações medidas (`NAME legs=`).
- Montagem: ffmpeg (`xstack` para quadros lado a lado, `fade`, `afade`, `-movflags +faststart`).

## Conferência (obrigatória antes de entregar)
- Extrair quadros a cada 1–3 s (e a cada 0,2 s nas curvas e passagens estreitas), montar folha e olhar: câmera dentro de parede/laje, heroína tapada, morador na frente da lente, aviso de UI, objeto flutuando.
- Corrigir e regravar; contar ao dono o que sobrou de defeito.

## Entrega
- Um arquivo `.mp4` em `C:\Users\mateu\Downloads\jogo\`, 1080p, < 98 MB (alvo ~85–90 MB, `-b:v` ~8–9 Mbps, preset slow), nome descritivo.
- Apagar o .avi bruto e as pastas de conferência depois.
- Commitar só os scripts do vídeo (diretor, roteiro, música) na branch do vídeo; nunca o shader do céu emprestado.
