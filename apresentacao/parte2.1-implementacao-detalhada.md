# PARTE 2.1 — O QUE FOI IMPLEMENTADO E COMO FUNCIONA

Este documento explica, em linguagem acessível, cada componente do sistema PharmaTransport IoT — o que foi feito, por que foi feito assim, e quais tecnologias foram usadas.

---

## 1. Conexão Física — Hardware e Sensores

### O que é

O dispositivo físico é um conjunto de componentes eletrônicos montados juntos que realiza três funções ao mesmo tempo: **medir temperatura e umidade**, **registrar a localização GPS**, e **transmitir esses dados pela internet**.

### O que foi usado

| Componente | Função | Custo aproximado |
|---|---|---|
| ESP32 DevKit V1 | Microcontrolador central — o "cérebro" do dispositivo | ~R$ 30 |
| DHT22 | Sensor de temperatura (−40°C a +80°C, precisão ±0.5°C) e umidade | ~R$ 15 |
| GPS NEO-6M | Receptor GPS — fornece latitude e longitude em tempo real | ~R$ 20 |
| Caixa impressa em 3D | Proteção física do conjunto — modelada em OpenSCAD e impressa em PLA | ~R$ 15 |

**Total de hardware por dispositivo: aproximadamente R$ 80.**

### Como funciona

O ESP32 é o núcleo. Ele:
1. Lê a temperatura e umidade do DHT22 a cada 5 segundos
2. Lê as coordenadas GPS do NEO-6M continuamente (o GPS envia dados em série via protocolo NMEA)
3. Monta um pacote JSON com todos os dados
4. Envia esse pacote pela internet via MQTT

O sensor DHT22 se comunica com o ESP32 por um único fio de dados (protocolo 1-Wire). O GPS NEO-6M se comunica via UART (porta serial), enviando frases como `$GPRMC,123519,A,-23.5505,-46.6333,...` que a biblioteca TinyGPS++ interpreta.

A caixa foi desenhada com aberturas específicas: uma lateral para o sensor DHT22 (para que ele meça o ar externo, não o calor interno da eletrônica), furos de ventilação no lado oposto, e uma abertura frontal para o cabo USB de alimentação.

---

## 2. Firmware — O Programa Dentro do ESP32

### O que é

Firmware é o programa que roda diretamente dentro do ESP32, sem sistema operacional. Foi escrito em **C++ com o Arduino Framework** e compilado na Arduino IDE.

### Como funciona

O firmware segue um ciclo simples:

```
A cada 5 segundos:
  1. Ler temperatura e umidade do DHT22
  2. Ler coordenadas do GPS
  3. Montar JSON com os dados
  4. Calcular assinatura HMAC-SHA256
  5. Publicar via MQTT
     → Se sem conexão: gravar no buffer local (SPIFFS)
```

A cada 30 segundos, envia também um **heartbeat** — uma mensagem de "estou vivo" — que o servidor usa para saber se o dispositivo está online.

### Tecnologias utilizadas

- **PubSubClient**: biblioteca que implementa o protocolo MQTT no ESP32
- **ArduinoJson**: monta e lê estruturas JSON com uso eficiente de memória
- **TinyGPS++**: interpreta os dados NMEA do GPS sem alocar memória desnecessária
- **WiFiClientSecure**: versão segura (com TLS) do cliente WiFi
- **mbedtls**: biblioteca criptográfica embutida no ESP32, usada para calcular o HMAC-SHA256
- **SPIFFS**: sistema de arquivos interno do ESP32, usado para gravar leituras offline

---

## 3. Dashboard Web

### O que é

O dashboard é a interface visual do sistema — uma página web acessada pelo navegador que mostra em tempo real o estado de todos os dispositivos, as leituras de temperatura, o mapa da rota e os alarmes de violação.

### Como funciona

O dashboard é uma **Single Page Application** servida pelo Flask. Não precisa ser instalada — basta abrir o navegador e acessar `http://IP:5000`. A página atualiza sozinha a cada 10 segundos chamando as APIs do backend.

**Componentes visuais:**

| Elemento | Tecnologia | O que mostra |
|---|---|---|
| Mapa da rota | Leaflet.js + OpenStreetMap | Trajeto completo, posição atual, pontos de leitura |
| Gráfico de temperatura | Chart.js | Linha do tempo com linhas tracejadas nos limites da faixa segura |
| Badge MQTT | HTML/CSS puro | Verde = broker conectado, Vermelho = sem conexão |
| Painel de alarmes | Template Flask + JS | Violações de temperatura com timestamp e localização |
| Lista de dispositivos | API REST + JS | Status online/recente/offline de cada ESP32 |
| Audit log | Tabela HTML | Histórico completo de ações — apenas para admins |

O mapa usa **OpenStreetMap** como base cartográfica (gratuito, sem limite de requisições) e a biblioteca **Leaflet.js** para renderizar rotas e marcadores diretamente no navegador.

### Tecnologias utilizadas

- **Flask**: framework web em Python que serve as páginas e as APIs
- **Jinja2**: motor de templates embutido no Flask (gera HTML dinâmico no servidor)
- **Leaflet.js**: biblioteca JavaScript para mapas interativos
- **Chart.js**: biblioteca JavaScript para gráficos de linha
- **CSS puro com variáveis**: visual escuro e responsivo, sem frameworks externos

---

## 4. Comunicação MQTT e Servidor de Mensagens

### O que é

MQTT (Message Queuing Telemetry Transport) é um protocolo de comunicação criado especificamente para dispositivos IoT. Funciona como um **serviço de entrega de mensagens**: o ESP32 publica mensagens, e o servidor Flask as recebe — sem que os dois precisem estar conectados diretamente entre si.

### Por que MQTT e não HTTP

| | MQTT | HTTP |
|---|---|---|
| Tamanho do cabeçalho | ~2 bytes | ~500 bytes |
| Overhead de conexão | Conexão persistente | Nova conexão a cada mensagem |
| Adequação para IoT | Projetado para isso | Projetado para web |
| Funcionamento offline | QoS 1 guarda mensagens | Não nativo |

Para um dispositivo enviando dados a cada 5 segundos em uma rede que pode ser instável, MQTT é dramaticamente mais eficiente.

### Arquitetura

```
ESP32                    Broker MQTT                  Flask
  │                    (HiveMQ Cloud)                   │
  │──── publica ────► vaccines/readings ◄──── lê ──────│
  │──── publica ────► vaccines/heartbeat ◄─── lê ──────│
```

O **broker** (servidor de mensagens) é o **HiveMQ Cloud** — um serviço gratuito na nuvem. Ele age como intermediário: o ESP32 envia para ele, e o Flask lê dele. Isso significa que o Flask e o ESP32 nunca precisam estar na mesma rede.

### QoS 1 — Garantia de Entrega

O sistema usa **QoS nível 1** (Quality of Service), que garante que cada mensagem seja entregue **pelo menos uma vez**. Se o Flask estiver offline momentaneamente, o broker guarda as mensagens e as entrega quando o Flask reconectar.

### Tecnologias utilizadas

- **PubSubClient** (ESP32): cliente MQTT para Arduino
- **paho-mqtt** (Python): cliente MQTT para o Flask
- **HiveMQ Cloud**: broker MQTT gratuito com suporte a TLS e credenciais

---

## 5. TLS e Autoridade Certificadora (CA)

### O que é

TLS (Transport Layer Security) é o protocolo que **cifra a comunicação** entre dois sistemas. É o mesmo protocolo que protege conexões HTTPS em sites bancários. Sem TLS, qualquer pessoa na mesma rede poderia ler as mensagens MQTT em texto puro.

### Como foi implementado

Toda comunicação MQTT — tanto do ESP32 quanto do Flask — ocorre na **porta 8883** com TLS 1.2 obrigatório. A porta 1883 (sem criptografia) foi desativada.

O ESP32 usa o `WiFiClientSecure` para estabelecer a conexão TLS. Para isso, precisa conhecer o certificado da autoridade certificadora (CA) — um arquivo que prova que o broker é legítimo e não um impostor.

```
ESP32 pergunta: "Quem é você?"
Broker apresenta seu certificado
ESP32 verifica: "Esse certificado foi assinado pela CA que conheço?"
Se sim → conexão estabelecida com criptografia
Se não → conexão recusada (proteção contra MITM)
```

O certificado da CA fica gravado diretamente no código do firmware como uma string de texto (no segmento `PROGMEM` para não ocupar RAM).

**Para o HiveMQ Cloud**, o certificado é assinado pela Let's Encrypt (CA pública confiável) — não foi necessário gerar CA própria. Para um broker Mosquitto local (usado em testes), os certificados foram gerados com `openssl` via script `certs/gerar_certs.sh`.

### Por que isso importa

Sem TLS:
- Um roteador comprometido veria temperatura, localização, credenciais em texto puro
- Um atacante poderia injetar leituras falsas (ex: temperatura sempre dentro do limite)

Com TLS:
- Todo o tráfego é cifrado — interceptar a comunicação resulta em texto ininteligível
- A identidade do broker é verificada criptograficamente

---

## 6. HTTPS — Comunicação Segura com o Dashboard

### O que é

Da mesma forma que o MQTT usa TLS, o acesso ao dashboard web também pode usar HTTPS — a versão segura do HTTP. Isso cifra toda a comunicação entre o navegador do operador e o servidor Flask.

### Como foi implementado

O Flask foi configurado para servir o dashboard com um certificado TLS quando os arquivos `flask.crt` e `flask.key` estão presentes na pasta `certs/`:

```python
app.run(ssl_context=(ssl_cert, ssl_key))
```

Se os certificados não estiverem presentes, o Flask cai automaticamente para HTTP — comportamento adequado para ambiente de desenvolvimento local. Em produção, os certificados garantem que a sessão de login, os dados das leituras e o audit log não trafeguem em texto puro.

---

## 7. MFA — Autenticação Multifator

### O que é

MFA (Multi-Factor Authentication) significa que para entrar no sistema são necessários **dois fatores independentes**:
1. **Algo que você sabe**: a senha
2. **Algo que você tem**: o celular com o código temporário

Mesmo que alguém descubra a senha, sem o celular não consegue entrar.

### Como funciona — TOTP

O sistema usa **TOTP** (Time-based One-Time Password), definido pela RFC 6238 — o mesmo padrão usado pelo Google, GitHub e bancos.

**Fluxo de login:**
```
Usuário digita email + senha
     ↓
Servidor verifica a senha com bcrypt
     ↓
Redireciona para página de código TOTP
     ↓
Usuário abre Google Authenticator no celular
     ↓
Digita o código de 6 dígitos (válido por 30 segundos)
     ↓
Servidor verifica o código com pyotp
     ↓
Acesso liberado
```

**Primeiro acesso** (sem TOTP configurado):
```
Login com senha → Tela de setup → QR Code aparece na tela
→ Usuário escaneia com Google Authenticator
→ Digita o código para confirmar
→ Secret TOTP gravado no banco para aquele usuário
→ Próximos logins exigem o código
```

O código TOTP é calculado a partir de um **segredo compartilhado** (string aleatória de 32 caracteres) e do **horário atual** — sem comunicação com nenhum servidor externo. O Google Authenticator e o servidor Flask calculam o mesmo código independentemente, e se baterem, a autenticação é válida.

### Tecnologias utilizadas

- **pyotp**: biblioteca Python que implementa TOTP/HOTP (RFC 6238/4226)
- **qrcode**: gera a imagem do QR Code exibida na tela de setup
- **Google Authenticator**: aplicativo no celular do usuário

---

## 8. RBAC — Controle de Acesso por Perfil

### O que é

RBAC (Role-Based Access Control) significa que diferentes usuários têm diferentes permissões no sistema. Não é todo mundo que pode fazer tudo.

### Como foi implementado

O sistema tem dois perfis:

| Permissão | Admin | Operador |
|---|---|---|
| Ver dashboard, leituras, dispositivos, alarmes | ✅ | ✅ |
| Ver audit log | ✅ | ❌ |
| Registrar e desativar dispositivos | ✅ | ❌ |
| Criar e encerrar viagens | ✅ | ❌ |
| Gerenciar usuários | ✅ | ❌ |
| Cadastrar produtos e lotes | ✅ | ❌ |

No backend, cada rota protegida tem um decorator:

```python
@require_permission("view_audit")
def audit_log():
    ...
```

Se um operador tentar acessar `/api/audit` diretamente (mesmo autenticado), recebe HTTP 403 — Acesso negado. A verificação acontece no servidor, não no frontend — não adianta "esconder" botões no HTML.

O dashboard também adapta a interface visualmente: operadores não veem o menu de Administração, mas essa é apenas a camada de UX — a proteção real está no backend.

---

## 9. HMAC — Assinatura Digital das Mensagens

### O que é

HMAC (Hash-based Message Authentication Code) é uma técnica que permite ao servidor verificar que uma mensagem **veio de um ESP32 legítimo e não foi alterada no caminho**.

Funciona como um lacre criptográfico: o ESP32 calcula uma "impressão digital" da mensagem usando uma chave secreta. O servidor recalcula a mesma impressão. Se bater, a mensagem é autentica e íntegra.

### Como funciona

```
ESP32:
  dados = {"temp": 28.5, "humidity": 60.1, "lat": -23.55, ...}
  nonce = esp_random() → "a3f9c1b2" (8 bytes aleatórios)
  hmac = HMAC-SHA256(dados + nonce, chave_secreta)
  publica: dados + nonce + hmac

Flask (verificação — implementada):
  recalcula = HMAC-SHA256(dados + nonce, mesma_chave_secreta)
  se recalcula == hmac recebido → mensagem autêntica
  se diferente → mensagem rejeitada (adulteração detectada)
```

O **nonce** (número aleatório único por mensagem) previne **replay attacks** — um atacante que capturar uma mensagem válida não pode reenviá-la mais tarde, porque o servidor verificaria se aquele nonce já foi usado antes.

### Tecnologias utilizadas

- **mbedtls** (ESP32): calcula HMAC-SHA256 usando o acelerador criptográfico em hardware
- **esp_random()** (ESP32 IDF): gera bytes aleatórios verdadeiros via hardware RNG
- **hmac + hashlib** (Python): recalcula e verifica o HMAC no servidor

---

## 10. BCP — Continuidade Offline (Buffer SPIFFS)

### O que é

BCP (Business Continuity Plan) — plano de continuidade de negócios — aqui se refere à capacidade do sistema de **continuar funcionando e não perder nenhuma leitura** mesmo quando a conexão com a internet cai.

### O problema

Um veículo pode entrar em áreas sem cobertura de rede: túneis, zonas rurais, áreas industriais com bloqueio de sinal. Sem uma solução de continuidade, todas as leituras durante esse período seriam perdidas — criando um buraco na cadeia de custódia.

### Como foi implementado

O ESP32 tem um sistema de arquivos interno chamado **SPIFFS** (SPI Flash File System) — uma pequena área de memória flash (~100KB) que pode guardar arquivos mesmo sem energia.

**Fluxo:**
```
Tentou publicar via MQTT?
  → Sucesso: segue normalmente
  → Falhou (sem WiFi ou broker offline):
       → Grava leitura em /buffer.jsonl (uma linha JSON por leitura)
       → Continua gravando a cada 5 segundos

Quando reconectar:
  → Lê /buffer.jsonl linha por linha
  → Publica cada leitura via MQTT (QoS 1 — aguarda confirmação)
  → Só apaga a linha após confirmação do broker
  → Quando o arquivo esvazia, volta ao modo normal
```

O arquivo `.jsonl` (JSON Lines) armazena uma leitura por linha — formato que permite leitura incremental sem carregar tudo na memória de uma vez.

**Capacidade**: aproximadamente 600 leituras (cada JSON tem ~200 bytes; 100KB / 200 bytes ≈ 500 entradas). A 1 leitura a cada 5 segundos, isso cobre **~50 minutos de desconexão** sem perda de dados.

### O resultado visível no dashboard

Quando a reconexão acontece, o gráfico de temperatura mostra um "spike" de pontos chegando de uma vez — a lacuna do período offline é preenchida em ordem cronológica, mantendo a cadeia de custódia íntegra.

---

## 11. BCP — Continuidade de Energia (Powerbank / Bateria)

### O que é

A segunda dimensão de continuidade: o dispositivo deve continuar funcionando mesmo se a **energia do veículo for cortada** — intencionalmente (sabotagem) ou não (pane elétrica).

### Como foi implementado

O dispositivo é alimentado por uma **powerbank comum** conectada à entrada Micro-USB do ESP32. Powerbanks possuem bateria Li-Ion interna com carga suficiente para manter o ESP32 operando por várias horas.

**Por que isso é BCP:**
- Se alguém desligar o veículo ou cortar a energia intencionalmente, o dispositivo continua gravando no buffer SPIFFS
- O ESP32 consome ~240mA em operação normal com WiFi ativo; uma powerbank de 10.000mAh sustenta o dispositivo por ~40 horas

**Watchdog Timer (WDT):**
Além da redundância de energia, o firmware tem um **Watchdog Timer de hardware** configurado para 60 segundos. Se o programa travar por qualquer motivo (loop infinito, deadlock, falha de memória), o WDT força um reset automático do ESP32. O dispositivo reinicia, reconecta ao WiFi e ao MQTT, e retoma o monitoramento — sem nenhuma intervenção manual.

```cpp
esp_task_wdt_init(60, true);  // reinicia se travar por 60s
esp_task_wdt_add(NULL);       // monitora a task principal
// Em cada ciclo:
esp_task_wdt_reset();         // "ainda estou vivo"
```

---

## 12. DRP — Recuperação de Desastre (Flush do Buffer)

### O que é

DRP (Disaster Recovery Plan) — plano de recuperação de desastres — aqui se refere ao processo de **recuperar e enviar todos os dados acumulados** após um período de indisponibilidade, garantindo que nada seja perdido permanentemente.

### Como funciona

Quando o ESP32 reconecta à rede (seja WiFi ou broker MQTT), executa automaticamente o **flush do buffer**:

```
1. Verifica se /buffer.jsonl existe e não está vazio
2. Se sim: entra em modo "flush"
3. Lê uma linha por vez do arquivo
4. Publica via MQTT com QoS 1
5. Aguarda ACK do broker (confirmação de entrega)
6. Só remove aquela linha do arquivo após ACK
7. Repete até o arquivo estar vazio
8. Deleta /buffer.jsonl
9. Retorna ao modo normal
```

A confirmação antes de apagar garante que, se a conexão cair novamente no meio do flush, os dados não apagados são reenviados na próxima reconexão. Nenhuma leitura é perdida, mesmo em cenários de múltiplas quedas consecutivas.

**No dashboard**, o flush se manifesta visualmente como várias leituras chegando de uma vez no gráfico — os pontos "preenchem" o intervalo em que o dispositivo esteve offline, em ordem cronológica.

---

## 13. Backup do Banco de Dados

### O que é

Backup é a cópia dos dados do banco MySQL para um local externo e seguro, garantindo que mesmo em caso de falha do servidor (HD com defeito, corrupção, acidente) os dados históricos possam ser recuperados.

### O que foi implementado

O banco de dados MySQL é exportado com `mysqldump`, que gera um arquivo SQL completo com todas as tabelas e dados. Esse arquivo pode ser:

- **Armazenado localmente**: como ponto de restauração rápida
- **Comprimido e enviado para nuvem**: Google Drive, OneDrive, ou qualquer storage — garantindo sobrevivência a falhas físicas do servidor

**Script de backup:**
```bash
mysqldump -u root -p vaccine_transport > backup_$(date +%Y%m%d).sql
# Compressão com GPG para backup cifrado:
gpg --symmetric backup_$(date +%Y%m%d).sql
```

O agendamento pode ser configurado via **Task Scheduler do Windows** para rodar automaticamente em horários programados (ex: toda noite às 2h).

---

## 14. Segurança das Senhas no Banco de Dados

### O problema

Se o banco de dados for comprometido (vazamento, acesso indevido), um atacante que visse as senhas em texto puro teria acesso imediato a todas as contas. Isso é um problema crítico especialmente se os usuários reutilizarem senhas em outros sistemas.

### Como foi implementado — bcrypt

As senhas **nunca são armazenadas em texto puro**. O sistema usa **bcrypt** — um algoritmo de hash especialmente projetado para senhas, com as seguintes propriedades:

**1. Hash unidirecional**: é computacionalmente impossível reverter o hash para descobrir a senha original.

**2. Salt automático**: cada senha recebe um valor aleatório único (salt) antes de ser processada. Duas pessoas com a mesma senha têm hashes completamente diferentes no banco.

**3. Custo configurável**: o bcrypt foi configurado com **12 rounds** — significa que calcular um único hash leva ~0.3 segundos intencionalmente. Um ataque de força bruta em 1 bilhão de senhas levaria décadas.

```python
# Ao criar/alterar senha:
hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt(rounds=12))
# Armazena: "$2b$12$EixZaYVK1fsbw1ZfbX3OXe..."

# Ao verificar login:
bcrypt.checkpw(senha_digitada.encode(), hash_do_banco)
# Retorna True/False — a senha original nunca é decifrada
```

**O que está no banco de dados** para cada usuário:
```
$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36DQBuMpV9h.L7MfxlJiUAy
```
Isso é tudo que um invasor veria — um hash bcrypt que não pode ser revertido.

### Credenciais fora do código-fonte

Além das senhas dos usuários, as **credenciais de infraestrutura** (senha do MySQL, chave secreta do Flask, credenciais MQTT, chave HMAC) são armazenadas em um arquivo `.env` — **fora do código-fonte** e fora do controle de versão (`.gitignore` garante que esse arquivo nunca vai para o GitHub).

```
# .env — NUNCA sobe para o repositório
DB_PASSWORD=VaccineSecure@2026
FLASK_SECRET_KEY=chave-aleatoria-longa
MQTT_USERNAME=flask-subscriber
MQTT_PASSWORD=FlaskMqtt@2026
```

---

## 15. Audit Log — Rastreabilidade Completa

### O que é

O audit log é um registro imutável de **tudo que acontece no sistema** — cada login, cada falha de autenticação, cada leitura recebida, cada dispositivo registrado, cada viagem criada ou encerrada.

### Como funciona

Toda ação relevante chama a função `audit()` no backend:

```python
audit("login_ok", user_id=user.id, ip=request.remote_addr,
      details={"name": user.name, "role": user.role})
```

Cada registro tem:
- **Usuário responsável** (ou NULL para ações automáticas do sistema)
- **Ação**: `login_ok`, `login_failed`, `totp_failed`, `device_registered`, `trip_created`, `trip_closed`, `reading_received`, `logout`
- **IP de origem**
- **Timestamp exato**
- **Detalhes em JSON**: o que foi feito especificamente

### Por que importa

A RDC nº 430/2020 da Anvisa exige identificação dos responsáveis por cada etapa do transporte. O audit log fornece exatamente isso:

> *"Quem registrou esse dispositivo?"* → `device_registered`, user_id=2, ip=192.168.1.1, 2026-04-10 14:23:11
> *"Alguém tentou invadir o sistema?"* → `login_failed` repetido do mesmo IP
> *"A viagem foi formalmente encerrada?"* → `trip_closed`, user_id=1, 2026-04-12 18:45:00

O audit log é visível apenas para admins no dashboard, e não pode ser deletado ou editado por nenhuma rota da API.

---

## 16. Segurança em Camadas — Visão Consolidada

O sistema foi projetado com múltiplas camadas de proteção independentes. Uma falha em uma camada não compromete as demais:

```
Camada 1 — Transporte:    TLS 1.2 cifra todo o tráfego (MQTT + HTTPS)
Camada 2 — Autenticação:  Senha + TOTP (MFA) para acessar o dashboard
Camada 3 — Autorização:   RBAC controla o que cada usuário pode fazer
Camada 4 — Integridade:   HMAC-SHA256 garante que dados não foram adulterados
Camada 5 — Replay:        Nonce único por mensagem previne reenvio de mensagens antigas
Camada 6 — Dados em BD:   bcrypt + salt protege senhas armazenadas
Camada 7 — Credenciais:   Variáveis de ambiente (.env) isolam segredos do código
Camada 8 — Rastreabilidade: Audit log registra todas as ações para auditoria
Camada 9 — Continuidade:  Buffer offline + powerbank + watchdog garantem dados íntegros
```

Essa abordagem — chamada de **defense in depth** — garante que um atacante que supere uma camada ainda enfrente as demais.
