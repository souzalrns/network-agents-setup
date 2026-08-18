#!/bin/bash
echo "🚀 Network Agents - Setup Completo"
echo "=================================="
echo ""
# Verifica Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado. Instale Node.js 18+"
    exit 1
fi
# Verifica pnpm
if ! command -v pnpm &> /dev/null; then
    echo "📦 Instalando pnpm..."
    npm install -g pnpm
fi
# Instala dependências
echo "📦 Instalando dependências..."
pnpm install
# Gera Prisma client
echo "🗄️ Gerando Prisma client..."
cd packages/memory
pnpm prisma:generate
cd ../..
# Cria .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando .env..."
    cp .env.example .env
    echo "⚠️ Edite .env com suas credenciais!"
fi
# Sobe Docker (opcional)
echo ""
echo "🐳 Deseja subir PostgreSQL e Redis com Docker Compose? (y/n)"
read -r start_docker
if [ "$start_docker" = "y" ]; then
    echo "🐳 Subindo Docker Compose..."
    docker-compose up -d postgres redis
    echo "⏳ Aguardando serviços..."
    sleep 10
fi
# Roda migrações
echo "🗄️ Rodando migrações..."
cd packages/memory
pnpm prisma:migrate --name init
cd ../..
# Build
echo "🔨 Compilando projeto..."
pnpm build
# Verifica integridade
echo "🔍 Verificando integridade..."
pnpm ts-node scripts/verify.ts
echo ""
echo "✅ Setup completo!"
echo ""
echo "🚀 Para iniciar: pnpm start"
echo "📝 Para desenvolvimento: pnpm dev"
