# Vessel_v2 - Documentação do Projeto

> Este ficheiro é a fonte de verdade do projeto. Atualizar após cada sessão.

## Stack Tecnológico
- **Backend**: FastAPI + SQLite (WAL mode) + Uvicorn
- **Frontend**: React 19 + Vite 8 + Tailwind CSS 4
- **Auth**: HTTP Basic (user: `vessel`, pass: `control2026`)
- **Python**: venv em `/home/kaus/Desktop/Kaus_Test/Vessel_v2/venv`

## Estrutura do Projeto
```
Vessel_v2/
├── backend/
│   ├── api_server.py    # API REST + Auth + Static files
│   ├── database.py      # Schema SQLite
│   └── ais_ingestor.py  # WebSocket AIS listener
├── frontend/
│   ├── src/            # Código fonte React
│   └── dist/           # Build estático
├── launcher.py        # Orquestrador de serviços
├── venv/             # Ambiente virtual
└── AGENTS.md         # Este ficheiro
```

## Base de Dados
- **Ficheiro**: `backend/vessels_v2.db`
- **Modo**: WAL (Write-Ahead Logging)
- **Tabelas**:
  - `vessels_master` - dados das embarcações
  - `positions_history` - histórico de posições
  - `occurrences` - ocorrências/ameaças

## Endpoints API
| Rota | Auth | Descrição |
|------|------|----------|
| `/api/` | ✅ | Status da API |
| `/api/vessels` | ✅ | Lista de embarcações |
| `/api/vessels/live` | ✅ | Posições em tempo real |
| `/` | ✅ | Frontend SPA |

## Histórico de Sessões

### Sessão 1 (18-04-2026) - Testes Iniciais
- [x] Verificação de packages instalados
- [x] Inicialização da base de dados
- [x] Startup do API server
- [x] Teste de autenticação Basic
- [x] Teste endpoints `/api/`, `/api/vessels`, `/api/vessels/live`
- [x] Teste frontend SPA (HTML + assets)
- **Resultado**: ✅ Tudo funcional

### Sessão 2 (18-04-2026) - Teste Backend
- [x] Teste completo da API (todos os endpoints)
- [x] Verificação de assets estáticos
- [x] Confirmado: servidor a correr na porta 8000
- **Resultado**: ✅ Todos os testes passaram

### Sessão 3 (18-04-2026) - Correção de Caminhos
- [x] Projeto movido de `/home/kaus/Desktop/Kaus_Test/sails/VesselControl/Vessel_v2` para `/home/kaus/Desktop/Kaus_Test/Vessel_v2`
- [x] Recriação do venv (venv tinha caminhos hardcoded com caminho antigo)
- [x] Teste de importação: `from backend.database import init_db` ✅
- **Resultado**: ✅ Venv recriado com sucesso

## Estado Atual
- Servidor em execução na porta 8000
- Base de dados vazia (sem dados AIS)
- Frontend compilado mas com template padrão Vite

## Preferências
- Credenciais: `vessel:control2026` (alterar para .env em produção)
- CORS aberto para desenvolvimento
- Usar launcher.py como ponto de entrada

## Próximos Passos
1. Desenvolver UI real do dashboard
2. Integrar dados AIS reais
3. Adicionar .env com credenciais reais
4. Implementar autenticação mais robusta
5. Adicionar mais endpoints según necessidade

## Ferramentas e Skills Disponíveis

### Localização
Skills расположены em: `/home/kaus/Desktop/Kaus_Test/.agent/skills/`

### Skills Relevantes para o Projeto

| Skill | Descrição | Uso no Projeto |
|-------|-----------|----------------|
| `@[skills/tailwind-patterns]` | Tailwind CSS v4 (CSS-first) | **UI do Dashboard** |
| `@[skills/nextjs-react-expert]` | React performance (57 regras) | **Frontend React** |
| `@[skills/frontend-design]` | Design thinking para web UI | **Design do Dashboard** |
| `@[skills/app-builder]` | Criar apps full-stack | **Estrutura do projeto** |
| `@[skills/api-patterns]` | REST/GraphQL/API design | **Endpoints API** |
| `@[skills/database-design]` | Schema, indexing, ORM | **Base de dados** |
| `@[skills/web-design-guidelines]` | UI/UX best practices | **Revisão de UI** |
| `@[skills/webapp-testing]` | E2E testing (Playwright) | **Testes** |
| `@[skills/python-patterns]` | Python async, type hints | **Backend** |
| `@[skills/bash-linux]` | Bash/Linux commands | **DevOps** |
| `@[skills/systematic-debugging]` | 4-phase debugging | **Bug fixing** |
| `@[skills/lint-and-validate]` | Linting e static analysis | **Quality control** |
| `@[skills/tdd-workflow]` | Test-Driven Development | **Testes** |

### Roadmap de Desenvolvimento

```
FASE 1: Setup Base (Concluído)
├── [x] Backend FastAPI + SQLite ✅
├── [x] Autenticação Basic ✅
└── [x] Frontend React/Vite/Tailwind ✅

FASE 2: UI Dashboard (Próximo)
├── [ ] Desenvolver Dashboard UI
│   ├── Usar: @[skills/tailwind-patterns]
│   ├── Usar: @[skills/frontend-design]
│   └── Usar: @[skills/nextjs-react-expert]
├── [ ] Integrar API com Frontend
│   ├── Usar: @[skills/api-patterns]
│   └── Usar: @[skills/webapp-testing]
└── [ ] Testes E2E
    └── Usar: @[skills/tdd-workflow]

FASE 3: Funcionalidades Avançadas
├── [ ] Integração AIS real
├── [ ] Mapas em tempo real
├── [ ] Sistema de alertas
└── [ ] Dashboard analytics

FASE 4: Produção
├── [ ] .env com credenciais
├── [ ] CORS restrito
├── [ ] Deploy
└── [ ] Monitoring
```

### Como Usar Skills
Para ativar uma skill, menciona no prompt:
- `"usa @[skills/tailwind-patterns] para a UI"`
- Ou a skill carrega automaticamente conforme o contexto

## Notas
- AIS ingestor descomentado no launcher (não está a correr)
- Frontend precisa de implementação real de dashboard marítimo
- Skills disponíveis em: `/home/kaus/Desktop/Kaus_Test/.agent/skills/`
- NOTA: O servidor por vezes continua em background após timeout - usar `pkill -f uvicorn` se necessário