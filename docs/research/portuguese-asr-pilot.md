# Transcrição em português nos três vídeos do piloto

Em 26 de novembro de 2026, o Whisper `small` multilíngue recuperou a sequência de capacidades de memória que o criador escreveu na descrição, o nome do utensílio no vídeo de legumes e termos técnicos que saíram deformados no `tiny`. Recomendo o `small` para a próxima avaliação local. Em 201,87 s de áudio, o tempo total de processamento subiu de 13,65 s para 64,46 s, cerca de 4,7 vezes. Um erro numérico relevante persistiu. [Avaliação anterior e origem da amostra](../real-tiktok-evaluation.md)

## Resultados observados

| Vídeo do Manual do Mundo | Áudio | `tiny` | `small` | O que mudou |
| --- | ---: | ---: | ---: | --- |
| [Descascador](https://www.tiktok.com/@manualdomundo/video/6912907102075784453) | 14,91 s | 1,45 s | 5,27 s | Aos 11,84 s, o `tiny` produziu “legulho”. O `small` produziu “legumes”, termo presente na descrição do criador. Ambos geraram três segmentos. |
| [Microscopia](https://www.tiktok.com/@manualdomundo/video/6971120192600476934) | 57,21 s | 3,65 s | 19,34 s | Entre 32 e 50 s, o `small` recuperou as grafias “cloroplasto”, “fotossíntese” e “clorofila”. O `tiny` segmentou ou deformou os três termos. O `small` também registrou “micro-órganos”. |
| [Memória e números binários](https://www.tiktok.com/@manualdomundo/video/6985162794849127685) | 129,75 s | 8,55 s | 39,85 s | Na abertura, o `small` recuperou 16, 32, 64 e 128, na ordem da descrição. O `tiny` fundiu 16 e 32. Aos 27–36 s, “organismos” passou a “algarismos”. Aos 86,96 s, o `small` ainda produziu a contagem incoerente “0 a 9, 199”. |

A comparação usa três gravações do mesmo criador e uma execução por par de modelo e vídeo, em um AMD Ryzen 5 5600G. A cronometragem inclui carregar o modelo em cada vídeo, decodificar, aplicar o detector de voz e consumir todos os segmentos. Cache de disco e carga da máquina podem variar. As descrições públicas permitem conferir alguns termos. Uma transcrição humana alinhada seria necessária para calcular taxa de erro de palavras (WER) e medir a precisão dos timestamps. [Fontes dos três vídeos](../real-tiktok-evaluation.md#fontes-e-execução)

## Pesos e reprodução

As duas variantes são multilíngues. A Systran distribui o `small` convertido para CTranslate2 em FP16 sob licença MIT. A execução local solicitou INT8 na CPU. A coluna SHA-256 contém o hash calculado sobre `model.bin` e conferido com o atributo `lfs.sha256` da API na revisão indicada. [Ficha oficial do modelo](https://huggingface.co/Systran/faster-whisper-small/blob/536b0662742c02347bc0e980a01041f333bce120/README.md)

| Variante | Revisão do repositório Systran | Bytes de `model.bin` | SHA-256 de `model.bin` |
| --- | --- | ---: | --- |
| [`tiny`](https://huggingface.co/api/models/Systran/faster-whisper-tiny/revision/d90ca5fe260221311c53c58e660288d3deb8d356?blobs=true) | `d90ca5fe260221311c53c58e660288d3deb8d356` | 75.538.270 | `dcb76c6586fc06cbdac6dd21f14cfd129cc4cdd9dce19bf4ffa62e59cbe6e6d1` |
| [`small`](https://huggingface.co/api/models/Systran/faster-whisper-small/revision/536b0662742c02347bc0e980a01041f333bce120?blobs=true) | `536b0662742c02347bc0e980a01041f333bce120` | 483.546.902 | `3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671` |

Para preparar cada diretório `.runtime/models/faster-whisper-<variante>`, obtenha `model.bin`, `tokenizer.json`, `config.json`, `vocabulary.txt` e `README.md` em `https://huggingface.co/Systran/faster-whisper-<variante>/resolve/<revisão>/<arquivo>`. Confira o SHA-256 antes de carregar os pesos. Os manifestos locais em cada diretório registram os hashes dos cinco arquivos.

O ensaio usou Python 3.12.2, `faster-whisper==1.2.1`, `ctranslate2==4.9.1` e `av==18.1.0`. Para repetir da raiz do projeto, execute o trecho a seguir com o Python do ambiente de mídia. O idioma `pt` é informado ao modelo. O detector de voz está habilitado. Os demais parâmetros de decodificação usam os padrões da versão indicada. [Adaptador do Pulso](../../backend/pulso/adapters/media_signals.py) · [Interface da versão ensaiada](https://github.com/SYSTRAN/faster-whisper/tree/v1.2.1)

O script do projeto prepara os diretórios com revisão fixa. Execute `python scripts/prepare-transcription.py --model small` ou `--model tiny`. O script confere o SHA-256 dos pesos antes de escrever o manifesto. A execução com `small` foi verificada localmente.

```python
from pathlib import Path
from time import perf_counter

from faster_whisper import WhisperModel

videos = ('6912907102075784453', '6971120192600476934', '6985162794849127685')
for size in ('tiny', 'small'):
    for video in videos:
        started = perf_counter()
        model = WhisperModel(f'.runtime/models/faster-whisper-{size}', device='cpu',
                             compute_type='int8', local_files_only=True)
        source = Path('.runtime/media/pilot-real') / f'{video}.mp4'
        segments, info = model.transcribe(str(source), language='pt', vad_filter=True)
        transcript = [(s.start, s.end, s.text.strip()) for s in segments]
        print(size, video, round(perf_counter() - started, 2), info.duration, transcript)
        del model
```

Os manifestos por vídeo em `.runtime/pilot/tiktok-real/` identificam os MP4 por SHA-256. As transcrições com seus intervalos e tempos de execução estão no arquivo local `.runtime/pilot/asr-comparison.json`. Tanto os MP4 quanto as transcrições integrais ficam fora do Git.
