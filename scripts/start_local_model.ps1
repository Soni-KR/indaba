$ErrorActionPreference = 'Stop'
$aegisRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $aegisRoot
& "$aegisRoot/runtime/llama/llama-server.exe" --model "$aegisRoot/models/Qwen3-8B-Q4_K_M.gguf" --host 127.0.0.1 --port 8091 --ctx-size 8192 --parallel 1 --gpu-layers 99 --alias Qwen3-8B-Q4_K_M --reasoning off --offline --no-webui
