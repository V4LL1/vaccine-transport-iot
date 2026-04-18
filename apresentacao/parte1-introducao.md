# PARTE 1 — INTRODUÇÃO

---

## 1.1 Abertura — O Problema Real

Em fevereiro de 2021, o Brasil perdeu cerca de **R$ 1,5 bilhão em vacinas COVID** por falhas na cadeia de frio durante o transporte e armazenamento. Não foi por falta de vacina — foi por falta de rastreabilidade, monitoramento e controle.

Esse não é um caso isolado. A Organização Mundial da Saúde estima que **entre 25% e 50% das vacinas chegam inutilizadas ao destino final** em países em desenvolvimento, principalmente por quebras na cadeia fria que nunca são detectadas a tempo.

O problema central é simples: **como garantir, com evidência técnica e rastreável, que um produto farmacêutico saiu do fabricante e chegou ao destino com sua integridade preservada?**

Hoje, na maioria das operações logísticas farmacêuticas do Brasil, a resposta ainda é: um datalogger de temperatura descartável que é lido só quando o produto chega — se é que é lido. Não há alertas em tempo real, não há rastreamento de rota, não há auditoria de quem acessou a informação, e não há continuidade de dados em caso de falha de conexão.

É exatamente esse gap que este projeto propõe preencher.

---

## 1.2 O Que é o Projeto

O **PharmaTransport IoT** é um sistema de monitoramento seguro e rastreável para transporte de produtos farmacêuticos, desenvolvido como Trabalho de Conclusão de Curso de Engenharia da Computação.

O sistema é composto por três grandes dimensões que trabalham juntas:

### Hardware Físico
Um dispositivo embarcado construído sobre o **ESP32 DevKit V1** — um microcontrolador dual-core com WiFi integrado amplamente utilizado em aplicações industriais IoT. Esse dispositivo é instalado fisicamente na carga transportada e carrega consigo sensores de temperatura, umidade e GPS.

### Software Full-Stack
Uma aplicação completa com backend em Python Flask, banco de dados relacional MySQL, e um dashboard web acessível de qualquer navegador. O backend recebe os dados do dispositivo em tempo real, armazena com rastreabilidade completa, e expõe uma API REST consumida pelo frontend.

### Cibersegurança por Design
A segurança não foi adicionada depois — foi projetada junto com o sistema desde o início. Comunicação cifrada com TLS 1.2, autenticação multifator com TOTP, controle de acesso por perfil (RBAC), assinatura digital de payloads com HMAC-SHA256 e audit log completo de todas as ações.

### A Arquitetura em 4 Pilares

```
[ESP32 + Sensores]  →  [MQTT TLS 1.2]  →  [Flask + MySQL]  →  [Dashboard + Alertas]
    PERCEPÇÃO            CONECTIVIDADE         ANÁLISE               AÇÃO
```

Cada pilar tem uma responsabilidade clara e separada:
- **Percepção**: coletar dados do mundo físico com precisão e confiabilidade
- **Conectividade**: transmitir esses dados com segurança, mesmo em condições adversas de rede
- **Análise**: armazenar, processar e detectar violações
- **Ação**: apresentar as informações de forma clara e gerar alertas quando necessário

---

## 1.3 O Que o Sistema Faz — Funcionalidades Principais

Do ponto de vista operacional, o PharmaTransport IoT entrega as seguintes capacidades:

### Monitoramento Contínuo em Tempo Real
O dispositivo coleta temperatura, umidade e coordenadas GPS a cada **5 segundos** e transmite via MQTT para o servidor. O dashboard exibe essas informações com atualização automática, sem necessidade de recarregar a página.

### Rastreamento de Rota Completo
Cada leitura inclui latitude e longitude com precisão GPS. O dashboard renderiza a rota completa da viagem em um mapa interativo (Leaflet.js + OpenStreetMap), com marcadores de início, posição atual e pontos intermediários. É possível visualizar exatamente onde cada leitura foi coletada.

### Detecção Automática de Violações
Cada produto farmacêutico cadastrado tem uma faixa de temperatura segura definida (por exemplo, Spikevax da Moderna: -25°C a -15°C). O sistema detecta automaticamente qualquer leitura fora desse intervalo e exibe no painel de alarmes, com timestamp preciso, localização e quanto a temperatura desviou do limite.

### Continuidade Garantida — Buffer Offline
Se o dispositivo perder conexão WiFi ou o broker MQTT ficar indisponível, **nenhuma leitura é perdida**. O ESP32 grava os dados localmente no SPIFFS (sistema de arquivos interno) e, ao reconectar, envia automaticamente todo o histórico acumulado em ordem cronológica.

### Rastreabilidade de Lote
Cada viagem é associada a um lote específico de produto (com código de lote, data de validade e quantidade). Cada leitura de temperatura é vinculada a esse lote. No final de uma viagem, é possível gerar o histórico completo de condições de transporte daquele lote específico.

### Audit Log Completo
Toda ação no sistema é registrada: logins, falhas de autenticação, registros de dispositivos, criação e encerramento de viagens, leituras recebidas. O log inclui usuário, IP de origem, timestamp e detalhes da ação — em conformidade com a RDC nº 430/2020 da Anvisa.

### Gestão Multi-Dispositivo
O sistema suporta múltiplos dispositivos simultâneos. Cada ESP32 se auto-registra com um ID derivado do seu endereço MAC (único por hardware). O administrador visualiza todos os dispositivos, seus status de conectividade (online/recente/offline) e pode registrá-los formalmente, associando a uma viagem ativa.

---

## 1.4 Por Que é Importante — Os Três Pilares de Valor

### Rastreabilidade Completa da Cadeia Fria

O sistema cria uma cadeia de custódia digital de ponta a ponta. Para qualquer lote de produto transportado, é possível responder com evidência:

- A temperatura esteve dentro da faixa segura durante todo o transporte?
- Se houve desvio: quando exatamente ocorreu, em qual trecho da rota, por quanto tempo e qual foi o valor máximo registrado?
- Qual dispositivo estava monitorando? Quem o registrou? Quando?
- O produto chegou ao destino e a viagem foi formalmente encerrada? Por quem?

Isso transforma o transporte farmacêutico de uma atividade baseada em confiança para uma atividade baseada em **evidência verificável**.

### Auditoria e Conformidade Regulatória

A **RDC nº 430/2020 da Anvisa** — Regulamento de Boas Práticas de Distribuição, Armazenagem e Transporte de Medicamentos — exige explicitamente:

- Monitoramento contínuo de temperatura durante o transporte
- Registro das condições de armazenagem e transporte
- Rastreabilidade dos produtos por lote
- Identificação dos responsáveis por cada etapa
- Procedimentos documentados de desvio de temperatura

O PharmaTransport IoT implementa todos esses requisitos de forma automatizada, gerando evidências digitais auditáveis.

Além da Anvisa, o sistema está alinhado com:
- **ISO/IEC 27001**: gestão de segurança da informação (autenticação, controle de acesso, audit log)
- **GDPR / LGPD**: proteção de dados com credenciais em variáveis de ambiente e criptografia de transporte

### Planejamento e Inteligência Operacional

Com o histórico de leituras armazenado, gestores podem:

- Identificar **rotas problemáticas** — trechos onde a temperatura consistentemente desvia
- Detectar **equipamentos com falha recorrente** — dispositivos que registram desvios frequentes
- Analisar **padrões sazonais** — horários e condições em que os desvios são mais comuns
- Calcular **conformidade por fornecedor** — percentual de entregas dentro da faixa segura

Esses dados transformam a operação logística de reativa (descobrir a falha quando o produto chega) para **proativa** (prever e prevenir falhas antes que ocorram).

---

## 1.5 Por Que é um Sistema Crítico

### A Tríade CIA da Segurança da Informação

Sistemas críticos são avaliados por três propriedades fundamentais: **Confidencialidade**, **Integridade** e **Disponibilidade**. O PharmaTransport IoT trata cada uma delas como requisito não-negociável.

#### Confidencialidade

Os dados gerados por este sistema têm alto valor comercial e estratégico:

- **Rotas logísticas**: revelar os trajetos de uma empresa farmacêutica permite mapear sua rede de distribuição, identificar vulnerabilidades físicas e planejar interferências
- **Dados de lote**: volume, destino e frequência de entregas revelam demanda, contratos e posicionamento competitivo
- **Credenciais de acesso**: um atacante com acesso ao dashboard pode alterar registros, mascarar violações ou extrair dados para fins regulatórios prejudiciais

Por isso, toda comunicação usa **TLS 1.2** (criptografia de transporte), credenciais são armazenadas em variáveis de ambiente (não no código), e o acesso ao sistema exige autenticação multifator.

#### Integridade

Em um sistema de monitoramento de saúde pública, a integridade dos dados não é apenas uma questão técnica — é uma questão ética e legal.

- Uma leitura de temperatura **adulterada** pode mascarar uma violação grave, fazendo com que um produto comprometido chegue à população
- Um log de auditoria **modificado** pode encobrir responsabilidades em caso de investigação

O sistema implementa **HMAC-SHA256** em cada payload: cada mensagem carrega uma assinatura criptográfica calculada com uma chave compartilhada. Qualquer bit alterado no dado invalida a assinatura. Um **nonce aleatório** (8 bytes via `esp_random()`) em cada mensagem previne ataques de replay — impossibilitando que um atacante capture e reenvie mensagens antigas para mascarar a situação atual.

#### Disponibilidade

O transporte de vacinas não espera. Se o sistema parar de funcionar no meio de uma viagem:

- Leituras críticas são perdidas
- Violações de temperatura não são detectadas
- A cadeia de custódia é interrompida

O sistema foi projetado para **nunca perder dados**, mesmo em condições adversas:

- **Watchdog Timer** (60s): reinicialização automática do ESP32 em caso de travamento
- **Buffer SPIFFS**: até 100KB de leituras armazenadas localmente durante desconexão (~40 minutos)
- **Reconexão automática**: WiFi e MQTT com retry exponencial (5s → 10s → 20s → máx 60s)
- **Sessão MQTT persistente**: o broker HiveMQ mantém as mensagens QoS 1 enquanto o Flask está offline, entregando ao reconectar

---

## 1.6 Contexto Tecnológico e Relevância

### IoT no Setor Farmacêutico — O Mercado

O mercado global de IoT para saúde foi avaliado em **USD 52 bilhões em 2023** e deve atingir **USD 180 bilhões até 2030** (crescimento anual de ~19%). O monitoramento de cadeia fria é um dos segmentos de maior crescimento, impulsionado por regulamentações mais rígidas pós-pandemia.

No Brasil, a Anvisa intensificou a fiscalização após as falhas de 2020-2021. Empresas que não conseguem demonstrar conformidade com a RDC 430 enfrentam multas, interdições e, em casos graves, responsabilização criminal.

### Por Que Este Projeto é Relevante como TCC

Este projeto não é uma aplicação acadêmica hipotética. Ele usa:
- Tecnologias reais usadas na indústria (MQTT, TLS, Flask, MySQL)
- Hardware físico funcionando (ESP32 com sensores reais)
- Protocolos de segurança padrão de mercado (HMAC, TOTP, RBAC, TLS)
- Conformidade com regulamentação real brasileira (RDC 430/2020)

É um sistema que uma empresa farmacêutica de pequeno porte poderia adotar hoje, com custo de hardware de aproximadamente **R$ 80 por dispositivo** (ESP32 ~R$30, DHT22 ~R$15, GPS NEO-6M ~$20, caixa impressa ~R$15), usando infraestrutura de broker gratuita (HiveMQ Cloud free tier) e software 100% open-source.
