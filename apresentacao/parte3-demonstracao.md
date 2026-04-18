# PARTE 3 — DEMONSTRAÇÃO AO VIVO

---

## Preparação Antes de Começar

Antes de subir para apresentar, verificar:

- [ ] `iniciar.bat` rodando (MySQL + Flask)
- [ ] ESP32 ligado e conectado (LED WiFi estável)
- [ ] Serial Monitor fechado (libera porta COM)
- [ ] Browser aberto em `http://127.0.0.1:5000`
- [ ] Google Authenticator no celular com conta `PharmaTransport IoT`
- [ ] HiveMQ console aberto em outra aba (para o passo 5)

---

## Passo 1 — Login com Autenticação Multifator

**O que mostrar**: tela de login → credenciais → código TOTP → dashboard

1. Abrir `http://127.0.0.1:5000` — redireciona para `/login`
2. Inserir: `admin@logistica.com` / `admin123`
3. Abrir Google Authenticator no celular — mostrar o código de 6 dígitos girando com o timer
4. Inserir o código → entrar no dashboard

**Fala sugerida**:
> "O acesso ao sistema exige dois fatores: a senha e um código temporário gerado no celular. Esse código muda a cada 30 segundos e é calculado localmente no aplicativo, sem comunicação com o servidor. Isso é o protocolo TOTP — Time-based One-Time Password, RFC 6238. Mesmo que alguém descubra a senha, sem o celular não entra."

---

## Passo 2 — Dashboard em Operação Normal

**O que mostrar**: badge MQTT, card do dispositivo online, gráfico, mapa

1. Apontar para o badge **MQTT** verde no topo — broker conectado
2. Mostrar o card do dispositivo com status **Online** e "visto há Xs"
3. Selecionar o lote ativo no combobox — viagem carrega automaticamente
4. Mostrar o gráfico de temperatura (linha do tempo com dados reais)
5. Mostrar o mapa com a rota em verde e posição atual

**Fala sugerida**:
> "O dashboard atualiza a cada 10 segundos automaticamente. Aqui vemos o dispositivo online — o heartbeat chegou há menos de 60 segundos. No gráfico temos a linha de temperatura ao longo do tempo; as linhas tracejadas são os limites da faixa segura do produto. No mapa, a rota percorrida e a última posição GPS registrada."

---

## Passo 3 — Modo Offline (WiFi desligado)

**O que mostrar**: ESP32 sem WiFi → buffer SPIFFS → dispositivo offline no dashboard

1. Desligar o hotspot do iPhone (ou WiFi do roteador)
2. Aguardar ~15 segundos
3. O dashboard mostra o dispositivo mudando para **Offline** (após 60s sem heartbeat)
4. Se tiver Serial Monitor disponível: mostrar as linhas `[WiFi] Falha. Gravando offline.` e `[Buffer] Leitura salva.`

**Fala sugerida**:
> "Simulando perda de sinal — o que acontece em um veículo entrando em uma área sem cobertura. O dispositivo detecta que perdeu a rede e automaticamente começa a gravar as leituras localmente no SPIFFS, o sistema de arquivos interno do ESP32. Nenhuma leitura é perdida. O dashboard já reflete que o dispositivo está offline."

---

## Passo 4 — Reconexão e Flush do Buffer

**O que mostrar**: WiFi volta → ESP32 envia tudo → spike no gráfico

1. Religar o hotspot
2. Aguardar reconexão (10–15 segundos)
3. O dashboard mostra o dispositivo voltando para **Online**
4. Mostrar no gráfico: várias leituras chegando de uma vez (lacuna preenchida)

**Fala sugerida**:
> "Ao reconectar, o sistema faz o flush automático — envia todas as leituras acumuladas em ordem cronológica. Podem perceber no gráfico que a lacuna foi preenchida: os dados do período offline chegaram em sequência. A cadeia de custódia permanece íntegra, sem buracos no histórico."

---

## Passo 5 — Broker Indisponível (MQTT offline)

**O que mostrar**: broker cai → ESP32 entra em modo offline → badge vermelho

1. No console HiveMQ: **Access Management** → excluir credencial `esp32-device`
2. Aguardar ~30 segundos
3. Mostrar badge MQTT virando **vermelho** no dashboard (Flask também perde conexão)
4. Mostrar que o dispositivo continua operando (se tiver Serial Monitor, mostrar `rc=5 Not Authorized` → modo offline)

**Fala sugerida**:
> "Agora simulamos o broker inacessível — credenciais revogadas. O ESP32 recebe `rc=5 Not Authorized` ao tentar reconectar e entra em modo offline novamente, continuando a gravar no buffer. O dashboard sinaliza a perda de conexão com o broker. Para restaurar: recriar as credenciais no HiveMQ."

5. Recriar credencial `esp32-device` / `Esp32Mqtt@2026` no HiveMQ
6. Aguardar reconexão automática e flush

---

## Passo 6 — Painel de Alarmes

**O que mostrar**: violações de temperatura detectadas automaticamente

1. Navegar para o painel de alarmes (sidebar ou seção no dashboard)
2. Mostrar as violações listadas com: lote, temperatura registrada, limite violado, timestamp, localização

**Fala sugerida**:
> "Qualquer leitura fora da faixa segura do produto aparece aqui automaticamente. O sistema compara cada leitura com o `min_temp` e `max_temp` cadastrados para aquele produto. Aqui vemos que em determinado momento a temperatura subiu para -10°C, acima do limite de -15°C do Spikevax. O operador sabe exatamente quando ocorreu e onde a carga estava."

---

## Passo 7 — Audit Log (Admin)

**O que mostrar**: rastreabilidade completa de ações

1. Navegar para Audit Log no menu (visível apenas para admin)
2. Mostrar registros: `login_ok`, `reading_received`, `device_registered`, `trip_created`
3. Destacar as colunas: usuário, IP de origem, ação, timestamp, detalhes

**Fala sugerida**:
> "O audit log registra absolutamente tudo: logins, falhas de autenticação, leituras recebidas, dispositivos registrados, viagens criadas e encerradas. Cada registro tem o usuário responsável, o IP de origem e o timestamp exato. Isso é o que a RDC nº 430/2020 da Anvisa exige — e o sistema gera automaticamente, sem nenhuma ação manual."

---

## Encerramento

**Fala sugerida**:
> "O PharmaTransport IoT transforma o transporte farmacêutico de uma atividade baseada em confiança para uma atividade baseada em evidência verificável. Com hardware de aproximadamente R$80 por dispositivo, broker cloud gratuito e software 100% open-source, entrega monitoramento contínuo, rastreabilidade por lote, segurança em múltiplas camadas e conformidade com a Anvisa desde o primeiro dia. O diferencial não está no hardware caro — está na arquitetura."
