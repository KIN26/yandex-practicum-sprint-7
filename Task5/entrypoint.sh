#!/bin/bash

/bin/ollama serve &
pid=$!

sleep 5

echo "🔴 Retrieve mistral model..."
ollama pull mistral:instruct
echo "🟢 Done!"

wait $pid
