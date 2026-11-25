# Portable runtime installed under .runtime; no Windows service or global settings.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $projectRoot '.runtime/ollama'
$executable = Join-Path $runtime 'ollama.exe'
if (-not (Test-Path -LiteralPath $executable)) {
    throw 'Runtime ausente. Consulte docs/operations.md para a distribuição oficial verificada.'
}
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_MODELS = Join-Path $runtime 'models'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
& $executable serve
exit $LASTEXITCODE
