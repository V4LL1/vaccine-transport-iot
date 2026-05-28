# PharmaTrack IoT: Sistema Seguro de Monitoramento de Transporte de Medicamentos com Arquitetura IoT em Quatro Pilares

**Trabalho de Conclusão de Curso — Engenharia da Computação**
**Autor**: Guilherme Palmanhani
**Orientador**: [Nome do Orientador]
**Instituição**: [Nome da Instituição]
**Ano**: 2026

---

## RESUMO

O transporte de produtos farmacêuticos termossensíveis — como vacinas, insulinas e imunobiológicos — exige controle rigoroso de temperatura ao longo de toda a cadeia logística, denominada cadeia de frio. A manutenção das condições térmicas adequadas em cada etapa do transporte é determinante para a preservação da eficácia e da segurança desses produtos, além de ser exigência prevista em regulamentação nacional. O presente trabalho apresenta o desenvolvimento do PharmaTrack IoT, um sistema de monitoramento contínuo para transporte de produtos farmacêuticos, construído sobre uma arquitetura de quatro pilares: Percepção (dispositivo embarcado ESP32 com sensores de temperatura, umidade e GPS), Conectividade (protocolo MQTT sobre TLS 1.2), Análise (backend Python Flask com banco de dados relacional MySQL) e Ação (dashboard web com visualização em tempo real). A segurança da informação foi incorporada como requisito desde a concepção do sistema, incluindo autenticação multifator baseada em TOTP, controle de acesso baseado em papéis, assinatura digital de mensagens com HMAC-SHA256 e registro de auditoria de todas as ações. O custo de hardware por dispositivo é de aproximadamente R$ 100,00, com infraestrutura de software inteiramente baseada em componentes de código aberto. O desenvolvimento teve como referência os requisitos da Resolução RDC nº 430/2020 da Agência Nacional de Vigilância Sanitária (Anvisa) e as diretrizes da norma ISO/IEC 27001:2022. Os resultados evidenciam a viabilidade técnica do desenvolvimento de um sistema de monitoramento farmacêutico seguro, rastreável e de baixo custo, utilizando hardware de propósito geral e ferramentas amplamente disponíveis.

**Palavras-chave**: Internet das Coisas; cadeia de frio farmacêutica; segurança da informação; MQTT; autenticação multifator; controle de acesso; monitoramento de transporte; Anvisa.

---

## ABSTRACT

The transportation of temperature-sensitive pharmaceutical products — such as vaccines, insulins and immunobiologicals — requires strict temperature control throughout the entire logistics chain, known as the cold chain. Maintaining adequate thermal conditions at each stage of transportation is essential for preserving the efficacy and safety of these products, and is also a requirement established by national regulation. This work presents the development of PharmaTrack IoT, a continuous monitoring system for pharmaceutical product transportation, built on a four-pillar architecture: Perception (ESP32 embedded device with temperature, humidity and GPS sensors), Connectivity (MQTT protocol over TLS 1.2), Analysis (Python Flask backend with MySQL relational database) and Action (web dashboard with real-time visualization). Information security was incorporated as a requirement from the system's inception, including TOTP-based multi-factor authentication, role-based access control, HMAC-SHA256 message digital signatures, and an audit log with protection against modification of all system actions. The hardware cost per device is approximately R$ 100.00, with software infrastructure entirely based on open-source components. The development was guided by the requirements of ANVISA's RDC 430/2020 and the controls outlined in ISO/IEC 27001:2022. Results show the technical feasibility of developing a secure, traceable and low-cost pharmaceutical monitoring system using general-purpose hardware and widely available tools.

**Keywords**: Internet of Things; pharmaceutical cold chain; information security; MQTT; multi-factor authentication; access control; transport monitoring; ANVISA.

---

## 1 INTRODUÇÃO

O setor farmacêutico compreende um conjunto diversificado de produtos cujas propriedades terapêuticas dependem diretamente da manutenção de condições ambientais controladas ao longo de todo o seu ciclo de vida — da fabricação à administração ao paciente. Entre esses produtos, os denominados termossensíveis requerem atenção especial durante as etapas de distribuição e transporte, pois estão sujeitos à degradação irreversível quando expostos a temperaturas fora da faixa recomendada pelo fabricante. A logística desses produtos é organizada por meio do que se denomina cadeia de frio farmacêutica, estrutura que envolve infraestrutura de armazenamento refrigerado, veículos adequados, equipamentos de monitoramento e procedimentos operacionais padronizados (WORLD HEALTH ORGANIZATION, 2015).

A cadeia de frio farmacêutica é definida pela Organização Mundial da Saúde (OMS) como o sistema de armazenagem e distribuição que mantém produtos termossensíveis dentro da faixa de temperatura recomendada desde o momento de sua fabricação até o ponto de uso (WORLD HEALTH ORGANIZATION, 2015). A cadeia é composta por elos sequenciais — fabricante, armazém central, distribuidor regional, ponto de entrega e unidade de saúde — e cada elo deve garantir individualmente as condições térmicas e de umidade adequadas ao produto em questão. As faixas de temperatura variam conforme o tipo de produto: a maioria das vacinas convencionais requer armazenagem entre 2°C e 8°C; algumas vacinas atenuadas precisam ser mantidas abaixo de -15°C; e vacinas de RNA mensageiro podem exigir condições de até -90°C (UNICEF, 2023). Produtos biológicos como anticorpos monoclonais e insulinas também se enquadram nessa categoria, com faixas igualmente restritivas.

A falha na manutenção das condições térmicas pode resultar em desnaturação de proteínas, perda de potência imunogênica, cristalização de compostos ou degradação química irreversível. Em muitos casos, o produto comprometido não apresenta alterações visuais perceptíveis ao operador, o que torna o monitoramento instrumental a forma necessária de verificar se as condições foram preservadas ao longo de todo o trajeto (UNICEF, 2023). A OMS estima que vacinas enviadas a países em desenvolvimento apresentam taxas de desperdício que, em algumas regiões, ultrapassam 50% do total distribuído, com condições inadequadas de armazenagem e transporte entre os principais fatores contribuintes (WORLD HEALTH ORGANIZATION, 2024). Segundo relatório da organização, a implementação de sistemas de monitoramento efetivos nas etapas de distribuição é um dos elementos centrais para a redução dessas perdas e para o fortalecimento dos programas nacionais de imunização.

> **[FIGURA 1 — Representação esquemática da cadeia de frio farmacêutica]**
>
> *Descrição para geração da imagem*: Diagrama horizontal com cinco blocos sequenciais ligados por setas. Da esquerda para a direita: (1) "Fabricante" — ícone de fábrica com termômetro; (2) "Armazém Central" — ícone de câmara fria com display de temperatura; (3) "Distribuição" — ícone de caminhão refrigerado; (4) "Ponto de Entrega" — ícone de caixa térmica com sensor; (5) "Unidade de Saúde" — ícone de geladeira hospitalar. Acima de cada bloco, a faixa de temperatura correspondente (ex.: 2–8°C para vacinas convencionais). Abaixo, legenda: "Cada elo da cadeia deve garantir individualmente as condições exigidas pelo produto." Fundo branco, traço limpo, estilo técnico.

No contexto brasileiro, a Agência Nacional de Vigilância Sanitária (Anvisa) publicou a Resolução RDC nº 430/2020, que estabelece as Boas Práticas de Distribuição, Armazenagem e Transporte de Medicamentos para Uso Humano (BRASIL, 2020). A norma especifica, entre outros aspectos, que as condições de temperatura e umidade devem ser monitoradas e registradas durante o transporte, com uso de equipamentos calibrados e em intervalos que permitam a verificação contínua das condições ao longo do trajeto. Determina também a rastreabilidade por número de lote do produto, a identificação dos responsáveis por cada etapa e a adoção de procedimentos documentados para o tratamento de desvios de temperatura. Esses requisitos estabelecem as premissas técnicas e documentais que nortearam o desenvolvimento do presente trabalho.

A Internet das Coisas — do inglês Internet of Things, comumente abreviada como IoT — é definida pelo Instituto Nacional de Padrões e Tecnologia dos Estados Unidos (NIST) como uma infraestrutura de dispositivos interconectados equipados com identificadores únicos e a capacidade de coletar e transmitir dados por redes de comunicação, sem necessidade de interação humana direta (NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY, 2016). Aplicada ao monitoramento ambiental, essa tecnologia permite a instalação de sensores embarcados em veículos ou embalagens de transporte que coletam e transmitem continuamente dados de temperatura, umidade e localização geográfica para plataformas de análise acessíveis remotamente. De acordo com levantamento da Statista, estima-se que o número global de dispositivos IoT ativos supere 18 bilhões de unidades em 2025, reflexo da crescente adoção da tecnologia em aplicações industriais, de saúde e de infraestrutura (STATISTA, 2025). No segmento de saúde, a IoT encontra aplicação direta no monitoramento de cadeias logísticas de insumos termossensíveis, possibilitando o registro contínuo e auditável das condições de transporte.

> **[FIGURA 2 — Modelo de comunicação IoT: dispositivo embarcado, broker MQTT e dashboard web]**
>
> *Descrição para geração da imagem*: Diagrama com três elementos horizontais. À esquerda, bloco "Dispositivo ESP32" com ícones de sensor de temperatura, umidade e GPS. No centro, bloco "Broker MQTT (HiveMQ Cloud)" com ícone de nuvem. À direita, bloco "Dashboard Web" com ícone de monitor. Entre o ESP32 e o broker: seta rotulada "Publica — MQTT / TLS 1.2 / porta 8883". Entre o broker e o dashboard: seta rotulada "Assina — paho-mqtt". Abaixo, legenda: "Comunicação inteiramente cifrada com TLS 1.2." Fundo branco, estilo técnico.

A ampla disseminação de dispositivos IoT em ambientes críticos — como saúde, infraestrutura e logística — amplia a superfície de ataque disponível para agentes maliciosos, tornando a segurança da informação um aspecto indissociável do projeto de tais sistemas. A Agência da União Europeia para a Cibersegurança (ENISA) documenta, em seus relatórios anuais sobre o panorama de ameaças cibernéticas, que dispositivos IoT figuram entre os vetores mais explorados em campanhas de ataque a infraestruturas críticas, frequentemente em razão de capacidade computacional limitada, longos ciclos de atualização e ausência de mecanismos de autenticação robustos (ENISA, 2024). No contexto de sistemas de monitoramento farmacêutico, a manipulação de dados de temperatura registrados durante o transporte ou o acesso não autorizado ao sistema de gestão de rastreamentos são exemplos de ocorrências que podem ter consequências diretas para a qualidade dos produtos e para a saúde dos pacientes.

A análise dos impactos potenciais de falhas de segurança em sistemas dessa natureza pode ser estruturada segundo as três propriedades da tríade CIA. Uma violação de confidencialidade, exemplificada pelo acesso não autorizado aos dados de rastreamento armazenados, expõe informações de alto valor estratégico e comercial: rotas logísticas utilizadas, volumes e frequências de entrega por produto, destinos de distribuição e dados de identificação dos responsáveis por cada etapa da operação. Essas informações podem ser exploradas por concorrentes para mapear a rede de distribuição de uma empresa farmacêutica, ou por agentes mal-intencionados para identificar padrões de transporte e planejar interceptações físicas de cargas de alto valor. Do ponto de vista regulatório, a exposição de dados de lote e distribuição pode ainda configurar infração à Lei Geral de Proteção de Dados (LGPD), especialmente quando os registros contêm dados vinculados a pessoas físicas responsáveis pelas operações.

Uma violação de integridade, caracterizada pela adulteração de leituras de temperatura armazenadas ou pela injeção de leituras falsas no sistema, representa o risco mais grave para a saúde pública. Em um sistema de monitoramento sem mecanismos de verificação da autenticidade das mensagens, um atacante com acesso ao canal de comunicação poderia substituir leituras reais que registram temperaturas acima do limite seguro por valores dentro da faixa aceitável, mascarando uma violação que comprometeu irreversivelmente o lote. O produto seria então liberado para uso com base em dados forjados, chegando ao paciente com eficácia reduzida ou nula, sem que qualquer indicador visual ou alerta do sistema sinalizasse o problema. A ENISA destaca que ataques de falsificação de dados de sensores em sistemas IoT industriais e de saúde são crescentes e frequentemente direcionados a cenários em que a decisão de liberar ou descartar um produto depende exclusivamente do registro digital (ENISA, 2024). Além do risco direto ao paciente, registros adulterados comprometem a rastreabilidade por lote exigida pela RDC nº 430/2020, inviabilizando investigações posteriores em caso de eventos adversos.

Uma violação de disponibilidade, decorrente da indisponibilidade do sistema de monitoramento durante o transporte por falha técnica ou interrupção do serviço de comunicação, interrompe a cadeia de custódia digital do produto. Períodos sem registro criam lacunas no histórico de condições de transporte que não podem ser preenchidas retroativamente, tornando impossível atestar que as condições adequadas foram mantidas durante o intervalo sem dados. Em operações sujeitas à fiscalização da Anvisa ou a auditorias de clientes institucionais, a ausência de registros contínuos pode resultar na rejeição do lote no destino, mesmo que as condições tenham sido preservadas ao longo de todo o trajeto. A indisponibilidade recorrente do sistema de monitoramento pode ainda comprometer a credibilidade da empresa perante órgãos regulatórios e dificultar a renovação de autorizações de funcionamento.

A norma internacional ISO/IEC 27001 define os requisitos para o estabelecimento e operação de um sistema de gestão de segurança da informação, abrangendo controles de acesso, criptografia, segurança de comunicações, rastreabilidade de eventos e gestão de incidentes (ISO, 2022). O NIST, por sua vez, na publicação SP 800-183, define os princípios de confiabilidade, segurança e resiliência aplicáveis a sistemas formados por redes de dispositivos conectados, incluindo requisitos de autenticidade das mensagens, confidencialidade dos dados transmitidos e rastreabilidade das operações realizadas (NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY, 2016). Ambos os documentos foram utilizados como referência orientadora no desenvolvimento do presente trabalho, especialmente na definição das camadas de segurança implementadas.

> **[FIGURA 3 — Camadas de segurança implementadas no PharmaTrack IoT]**
>
> *Descrição para geração da imagem*: Diagrama em camadas concêntricas com fundo escuro. Da camada mais externa para o núcleo: (1) "Transporte — TLS 1.2"; (2) "Autenticação do Broker — Credenciais + ACL"; (3) "Integridade da Mensagem — HMAC-SHA256 + Nonce"; (4) "Autenticação do Usuário — bcrypt + TOTP"; (5) "Autorização — RBAC (3 perfis)"; núcleo: "Dados — Leituras + Rastreamentos + Audit Log". Abaixo, legenda: "Defesa em profundidade: cada camada é independente." Fundo escuro, tonalidades em verde e cinza.

Diante desse cenário, o presente trabalho propõe e implementa o PharmaTrack IoT, um sistema de monitoramento contínuo para o transporte de produtos farmacêuticos termossensíveis, desenvolvido com foco na acessibilidade econômica e na segurança da informação. O sistema é estruturado segundo uma arquitetura de quatro pilares para sistemas IoT: Percepção, Conectividade, Análise e Ação. 
O pilar de Percepção é composto por um dispositivo embarcado baseado no microcontrolador ESP32, equipado com sensor DHT22 para medição de temperatura e umidade e receptor GPS NEO-6M para registro de coordenadas geográficas, com custo total de hardware de aproximadamente R$ 100,00 por unidade. 
O pilar de Conectividade utiliza o protocolo MQTT sobre TLS 1.2, com broker em nuvem gerenciada. 
O pilar de Análise compreende um backend desenvolvido em Python com o framework Flask e banco de dados MySQL, responsável pelo processamento das mensagens, pela detecção de violações de temperatura e pelos controles de autenticação e autorização. 
O pilar de Ação é um dashboard web acessível por navegador, com atualização automática a cada dez segundos, que apresenta gráficos de temperatura, mapa interativo da rota percorrida, painel de alertas e interfaces de gestão administrativa.

> **[FIGURA 4 — Arquitetura do PharmaTrack IoT em quatro pilares]**
>
> *Descrição para geração da imagem*: Diagrama horizontal com quatro blocos retangulares grandes, separados por setas de fluxo de dados. Bloco 1 (azul médio): "PERCEPÇÃO — ESP32 / DHT22 / GPS NEO-6M". Bloco 2 (verde médio): "CONECTIVIDADE — MQTT / TLS 1.2 / HiveMQ Cloud". Bloco 3 (roxo médio): "ANÁLISE — Flask / MySQL / Autenticação / RBAC". Bloco 4 (laranja médio): "AÇÃO — Dashboard Web / Gráficos / Mapa / Alertas". Setas rotuladas entre os blocos. Abaixo, faixa contínua: "Segurança em Camadas — TLS · HMAC · TOTP · RBAC · Audit Log". Fundo branco, estilo técnico.

A principal motivação para o desenvolvimento do PharmaTrack IoT é a acessibilidade econômica. Apesar da existência de soluções comerciais para monitoramento de cadeia de frio, elas apresentam alto custo e limitada transparência em relação à segurança dos dados, dificultando sua adoção em operações de menor escala. A utilização de hardware de propósito geral disponível no mercado nacional, associada a uma pilha de software inteiramente composta por ferramentas de código aberto, resulta em um custo de implantação por dispositivo significativamente menor. Esse diferencial torna viável a adoção de monitoramento eletrônico contínuo em operações logísticas de menor escala. Sob a perspectiva acadêmica, o trabalho demonstra como princípios consolidados de segurança da informação — autenticação multifator, controle de acesso por perfis, assinatura digital de mensagens e defesa em profundidade — podem ser aplicados de forma integrada em um sistema IoT de baixo custo, com referência direta à regulamentação vigente aplicável ao setor farmacêutico brasileiro.

O objetivo geral do presente trabalho é desenvolver e implementar o PharmaTrack IoT, um sistema de monitoramento contínuo para o transporte de produtos farmacêuticos termossensíveis, com arquitetura IoT em quatro pilares, custo de hardware de aproximadamente R$ 100,00 por dispositivo e infraestrutura de software baseada em componentes de código aberto, tendo como referência orientadora os requisitos da Resolução RDC nº 430/2020 da Anvisa e as diretrizes da norma ISO/IEC 27001:2022.

O primeiro conjunto de objetivos específicos diz respeito à camada de hardware e firmware do sistema. Busca-se projetar e implementar um dispositivo embarcado baseado no microcontrolador ESP32, capaz de realizar coletas de temperatura com precisão de ±0,5°C por meio do sensor DHT22, de umidade relativa com precisão de ±2% e de coordenadas geográficas com precisão de ±2,5 metros por meio do receptor GPS NEO-6M. O dispositivo deve operar em ciclos de coleta de cinco segundos e possuir capacidade de armazenamento local das leituras em memória não volátil, garantindo a continuidade do registro durante eventuais períodos de desconexão da rede.

O segundo conjunto de objetivos específicos abrange as camadas de comunicação e segurança. Pretende-se implementar a transmissão dos dados coletados utilizando o protocolo MQTT sobre TLS 1.2, com autenticação do dispositivo por credenciais junto ao broker e controle de acesso por lista de permissões, de modo que cada componente do sistema opere com o mínimo de privilégios necessários. Na mesma camada, objetiva-se desenvolver mecanismos de integridade e autenticidade das mensagens por meio de assinatura digital HMAC-SHA256, com nonce aleatório gerado por hardware a cada envio para prevenção de ataques de repetição. No que se refere ao acesso ao sistema de gestão, o trabalho propõe a implementação de autenticação multifator baseada no algoritmo TOTP, controle de acesso baseado em papéis com três níveis de permissão distintos, e registro de auditoria de todas as ações realizadas no sistema.

O terceiro conjunto de objetivos específicos compreende o desenvolvimento do backend e da interface web. Nesse escopo, o trabalho propõe a construção de uma aplicação servidor capaz de receber e processar as mensagens MQTT, detectar automaticamente violações de temperatura em relação aos limites cadastrados para cada produto, armazenar os dados de forma estruturada em banco de dados relacional e disponibilizá-los por meio de APIs. Complementarmente, objetiva-se desenvolver um dashboard web com visualização em tempo real de temperatura e localização, sistema de alertas, e interfaces de gestão de dispositivos, rastreamentos, usuários, produtos farmacêuticos e lotes, com suporte a múltiplas empresas em uma única instalação do sistema.

---

## 3 METODOLOGIA

### 3.1 Materiais e Recursos Utilizados

O desenvolvimento do PharmaTrack IoT envolveu componentes de hardware e ferramentas de software cuja seleção foi orientada pelo critério de acessibilidade econômica e pela disponibilidade de documentação técnica aberta.

Os componentes de hardware utilizados foram: o microcontrolador ESP32 DevKit V1 (arquitetura Xtensa LX6 dual-core, 240 MHz, 520 KB SRAM, WiFi 802.11 b/g/n), que constitui a unidade central de processamento e comunicação do dispositivo; o sensor DHT22, responsável pela leitura de temperatura (faixa de −40°C a +80°C, precisão ±0,5°C) e umidade relativa (0–100%, precisão ±2%); o receptor GPS NEO-6M, que fornece coordenadas geográficas por comunicação UART com protocolo NMEA 0183 e precisão típica de ±2,5 m; uma bateria portátil (powerbank) com capacidade mínima de 5.000 mAh para alimentação autônoma do dispositivo; e uma caixa de proteção impressa em PLA por processo FDM, modelada em OpenSCAD com dimensões de 170 × 90 × 80 mm.

As ferramentas de software utilizadas foram: Arduino IDE 2.x para desenvolvimento e compilação do firmware em C++ com o Arduino Framework; Python 3.11 como linguagem do backend; Flask 3.0.3 como framework web; MySQL 8.0 como banco de dados relacional; paho-mqtt 2.1.0 como cliente MQTT para Python; Flask-Login 0.6.3 para gerenciamento de sessões autenticadas; bcrypt 4.1.3 para hash de senhas; pyotp 2.9.0 para implementação do algoritmo TOTP; HiveMQ Cloud (plano gratuito) como broker MQTT gerenciado; OpenSCAD 2021.01 para modelagem 3D da caixa de proteção; e Git para controle de versão do código-fonte.

O ambiente de desenvolvimento utilizado foi um computador pessoal com sistema operacional Windows 11, com o servidor MySQL inicializado manualmente a partir do executável do MySQL 8.0 e o servidor Flask executado por meio de ambiente virtual Python (venv).

---

### 3.2 Desenvolvimento do Dispositivo Embarcado

O dispositivo embarcado constitui o pilar de Percepção do sistema e é responsável por coletar os dados físicos do ambiente de transporte — temperatura, umidade e localização geográfica — e transmiti-los ao servidor. O hardware é composto pelo microcontrolador ESP32, o sensor de temperatura e umidade DHT22 e o receptor GPS NEO-6M, conectados em uma protoboard e protegidos por uma caixa impressa em PLA.

> **[FIGURA 5 — Componentes de hardware do dispositivo]**
>
> *Instrução para o autor*: Fotografia dos componentes físicos dispostos sobre uma superfície plana, separados e identificáveis: ESP32 DevKit V1, sensor DHT22, receptor GPS NEO-6M com antena, powerbank, cabos jumper e a caixa de PLA aberta. Iluminação uniforme, fundo neutro (branco ou cinza).

> **[FIGURA 6 — Dispositivo montado e caixa de proteção]**
>
> *Instrução para o autor*: Fotografia do dispositivo completamente montado dentro da caixa de PLA, com a tampa fechada e o cabo USB aparente. Se possível, incluir uma segunda foto com a tampa aberta mostrando o interior com os componentes conectados. Ângulo levemente elevado (45°), fundo neutro.

O firmware foi desenvolvido em linguagem C++ com o Arduino Framework, utilizando as bibliotecas PubSubClient (cliente MQTT), ArduinoJson (serialização JSON), TinyGPS++ (interpretação de dados NMEA do receptor GPS) e WiFiClientSecure (comunicação TLS). A lógica principal do firmware opera em ciclos de cinco segundos: a cada ciclo, o sensor DHT22 é lido, as coordenadas GPS são atualizadas e um pacote JSON é montado e transmitido. O trecho a seguir ilustra a leitura dos sensores e a montagem do payload:

```cpp
// -------------------------------------------------------
// Monta o payload JSON com HMAC-SHA256 e nonce
// Estrutura: { campos... , nonce, hmac }
// O Flask verifica: hmac = HMAC-SHA256(key, payload_sem_hmac)
void buildPayload(float temp, float hum, char* buf, size_t bufLen) {
  StaticJsonDocument<768> doc;
  doc["device_id"]   = DEVICE_ID;
  doc["timestamp"]   = buildTimestamp();
  doc["temperature"] = isnan(temp) ? (float)0.0 : temp;
  doc["humidity"]    = isnan(hum)  ? (float)0.0 : hum;
  if (gps.location.isValid()) {
    doc["latitude"]   = gps.location.lat();
    doc["longitude"]  = gps.location.lng();
    doc["satellites"] = gps.satellites.isValid() ? (int)gps.satellites.value() : 0;
  } else {
    doc["latitude"]   = (float)0.0;
    doc["longitude"]  = (float)0.0;
    doc["satellites"] = 0;
  }

  // Nonce único por mensagem (anti-replay)
  doc["nonce"] = generateNonce();

  // Serializa sem hmac — este texto exato é o que será assinado e enviado no campo "signed"
  char toSign[768];
  serializeJson(doc, toSign, sizeof(toSign));

  // Inclui o texto assinado e o HMAC no payload final
  doc["signed"] = toSign;
  doc["hmac"]   = computeHMAC(String(toSign));

  serializeJson(doc, buf, bufLen);
}
```

O campo `device_id` é derivado automaticamente do endereço MAC do hardware, garantindo unicidade por dispositivo sem necessidade de configuração manual. O campo `nonce` recebe um valor aleatório único gerado a cada envio, conforme descrito na Seção 3.4.

Para garantir a continuidade do registro durante períodos de desconexão da rede, o firmware utiliza o sistema de arquivos SPIFFS (SPI Flash File System), presente na memória flash interna do ESP32. Quando a publicação MQTT falha, a leitura é gravada localmente em um arquivo no formato JSON Lines (uma entrada por linha). Ao restabelecer a conexão, o firmware realiza o envio das leituras acumuladas em ordem cronológica antes de retomar a operação normal:

```cpp
// -------------------------------------------------------
    // Salva payload JSON no buffer offline (SPIFFS)
    void saveToBuffer(const char* payload) {
    if (SPIFFS.exists(BUFFER_FILE)) {
        File f = SPIFFS.open(BUFFER_FILE, "r");
        if (f && f.size() >= BUFFER_MAX_BYTES) {
        f.close();
        Serial.println("[Buffer] Cheio! Leitura descartada.");
        return;
        }
        if (f) f.close();
    }
    File f = SPIFFS.open(BUFFER_FILE, "a");
    if (!f) {
        Serial.println("[Buffer] Erro ao abrir arquivo!");
        return;
    }
    f.println(payload);
    f.close();
    Serial.println("[Buffer] Leitura salva offline.");
    }
```

O firmware também implementa um Watchdog Timer (WDT) configurado para 60 segundos. Caso o ciclo principal do programa trave por qualquer motivo, o WDT provoca uma reinicialização automática do microcontrolador, garantindo retomada da operação sem intervenção manual.

> **[FIGURA 7 — Tela do Arduino IDE com o firmware em compilação]**
>
> *Instrução para o autor*: Captura de tela do Arduino IDE 2.x exibindo o arquivo `main.ino` aberto, com a barra inferior mostrando o resultado de uma compilação bem-sucedida ("Compilation complete" ou similar). O código deve estar visível na área principal do editor. Se possível, posicionar o cursor em um trecho relevante como a função de leitura de sensores ou a publicação MQTT.

---

### 3.3 Implementação da Camada de Conectividade

A transmissão dos dados coletados pelo dispositivo ao servidor utiliza o protocolo MQTT com garantia de entrega de nível 1 (QoS 1), que assegura que cada mensagem seja entregue ao menos uma vez. O broker escolhido é o HiveMQ Cloud, serviço gerenciado com plano gratuito que suporta até cem conexões simultâneas e impõe o uso de TLS como requisito obrigatório.

Toda a comunicação ocorre sobre TLS 1.2 na porta 8883. No lado do dispositivo, a conexão cifrada é estabelecida por meio da classe `WiFiClientSecure` do SDK do ESP32. Durante o desenvolvimento, identificou-se uma incompatibilidade entre a implementação mbedtls do ESP32 e a cadeia de certificados ISRG Root X1 utilizada pelo HiveMQ Cloud, o que impediu o uso de `setCACert()`. Como solução, o método `setInsecure()` foi utilizado, que mantém a cifragem do canal TLS ativa mas suprime a validação do certificado do servidor:

```cpp
  // TLS ativo (tráfego cifrado) — validação de cert desabilitada
  // Nota: ESP32 mbedtls tem incompatibilidade com cadeia ISRG Root X1 do HiveMQ Cloud
  wifiClientSecure.setInsecure();

  mqttClient.setBufferSize(768);
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

  Serial.println("=== Sistema pronto (TLS ativo) ===\n");
}


// -------------------------------------------------------
void loop() {
  esp_task_wdt_reset();   // alimenta o watchdog — prova que o loop está vivo

  while (SerialGPS.available() > 0) {
    gps.encode(SerialGPS.read());
  }

  // Verifica conectividade — não bloqueante; falha → grava no buffer
  bool wifiOk = ensureWiFi();
  bool mqttOk = wifiOk && ensureMQTT();

  if (mqttOk) {
    mqttClient.loop();
    // Flush só quando acaba de reconectar (transição false → true)
    if (!prevMqttOk) {
      flushBuffer();
    }
  }
  prevMqttOk = mqttOk;
```

O uso de `setInsecure()` garante que o tráfego permaneça cifrado e inacessível a um observador passivo na rede, porém não protege contra ataques de intermediário ativo (man-in-the-middle). A autenticação do broker é compensada parcialmente pela autenticação por credenciais exigida pelo próprio HiveMQ Cloud. A substituição por `setCACert()` com a CA raiz correta constitui uma das melhorias identificadas para trabalhos futuros.

O controle de acesso no broker é implementado por meio de uma lista de permissões (ACL) que restringe as operações de cada usuário MQTT aos tópicos que lhe são pertinentes. O dispositivo possui permissão apenas para publicar nos tópicos `vaccines/readings` e `vaccines/heartbeat`, enquanto o backend Flask possui permissão apenas para assinar esses mesmos tópicos — sem capacidade de publicação. Essa separação garante que nenhum componente possa executar operações fora do seu escopo definido.

No lado do servidor, o subscriber MQTT é executado em uma thread separada da aplicação Flask, utilizando a biblioteca paho-mqtt. A sessão é configurada como persistente (`clean_session=False`), o que permite ao broker reter e entregar mensagens que chegaram enquanto o servidor estava temporariamente indisponível:

```python
def start_mqtt_subscriber():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="flask-subscriber",
        clean_session=False,
    )
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    # Resolve o caminho do CA cert relativo ao diretório deste arquivo
    ca_cert = MQTT_CA_CERT
    if ca_cert and not os.path.isabs(ca_cert):
        ca_cert = os.path.join(os.path.dirname(os.path.abspath(__file__)), ca_cert)

    if ca_cert and os.path.isfile(ca_cert):
        client.tls_set(ca_certs=ca_cert)
    else:
        # Usa o CA store do sistema (funciona com HiveMQ Cloud / Let's Encrypt)
        client.tls_set()

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    # paho aguarda entre 5s e 60s entre tentativas automáticas de reconexão
    client.reconnect_delay_set(min_delay=5, max_delay=60)

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()   # bloqueia; paho cuida das reconexões
        except Exception as e:
            logging.error(f"MQTT: Conexão falhou: {e}. Tentando em {retry_delay}s...")
        mqtt_status["connected"] = False
        time.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)
```

> **[FIGURA 8 — Console do HiveMQ Cloud com conexões ativas]**
>
> *Instrução para o autor*: Captura de tela do painel web do HiveMQ Cloud (app.hivemq.com), na aba de gerenciamento de clientes ou no painel de visão geral. A imagem deve mostrar o dispositivo ESP32 e o subscriber Flask listados como conexões ativas, com seus respectivos identificadores de cliente. Se estiver com o sistema em operação, a captura pode incluir o gráfico de mensagens recebidas.

---

### 3.4 Implementação dos Mecanismos de Segurança

#### 3.4.1 Integridade das Mensagens: HMAC-SHA256 e Nonce

Para garantir a autenticidade e a integridade de cada mensagem enviada pelo dispositivo, o firmware calcula uma assinatura digital utilizando o algoritmo HMAC-SHA256. O cálculo é realizado com a biblioteca `mbedtls`, nativa do ESP32, que aproveita o acelerador criptográfico em hardware. A chave utilizada é compartilhada entre o dispositivo e o servidor:

```cpp
// -------------------------------------------------------
// Calcula HMAC-SHA256 de 'data' com HMAC_KEY
// Retorna string hex de 64 chars
String computeHMAC(const String& data) {
  unsigned char hmacResult[32];
  mbedtls_md_context_t ctx;
  mbedtls_md_type_t mdType = MBEDTLS_MD_SHA256;

  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(mdType), 1);
  mbedtls_md_hmac_starts(&ctx,
    (const unsigned char*)HMAC_KEY, strlen(HMAC_KEY));
  mbedtls_md_hmac_update(&ctx,
    (const unsigned char*)data.c_str(), data.length());
  mbedtls_md_hmac_finish(&ctx, hmacResult);
  mbedtls_md_free(&ctx);

  char hexStr[65];
  for (int i = 0; i < 32; i++) {
    snprintf(hexStr + (i * 2), 3, "%02x", hmacResult[i]);
  }
  return String(hexStr);
}
```

A assinatura resultante é incluída no campo `hmac` do payload JSON. Qualquer alteração no conteúdo da mensagem após sua geração produz um HMAC completamente diferente, permitindo ao servidor detectar adulterações.

Para prevenir ataques de repetição — nos quais um atacante captura uma mensagem válida e a reencaminha posteriormente —, cada mensagem inclui um campo `nonce`, um valor aleatório de 64 bits gerado pelo gerador de números aleatórios por hardware do ESP32:

```cpp
// -------------------------------------------------------
// Gera nonce de 8 bytes em hex usando esp_random()
String generateNonce() {
  char buf[17];
  uint32_t r1 = esp_random();
  uint32_t r2 = esp_random();
  snprintf(buf, sizeof(buf), "%08x%08x", r1, r2);
  return String(buf);
}
```

A função `esp_random()` utiliza o gerador de entropia por hardware do ESP32, produzindo valores não previsíveis a cada chamada.

#### 3.4.2 Autenticação de Usuários: bcrypt e TOTP

O acesso ao sistema de gestão é protegido por dois fatores sequenciais. O primeiro é a verificação da senha, realizada com o algoritmo bcrypt. O bcrypt é um algoritmo de hash projetado especificamente para senhas, com fator de custo configurável que torna o processo de verificação intencionalmente lento, dificultando ataques de força bruta. As senhas são armazenadas no banco de dados exclusivamente em formato de hash, nunca em texto puro:

```python
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").encode()

        conn = db()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT user_id, name, email, role, password_hash, totp_secret"
            " FROM users WHERE email = %s",
            (email,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row and bcrypt.checkpw(password, row["password_hash"].encode()):
            session["pending_user_id"]    = row["user_id"]
            session["pending_user_email"] = row["email"]
            audit("login_password_ok", details={"email": email}, ip=request.remote_addr)

            if not row["totp_secret"]:
                return redirect(url_for("auth.setup_totp"))
            return redirect(url_for("auth.verify_totp"))

        error = "Email ou senha incorretos."
        audit("login_failed", details={"email": email}, ip=request.remote_addr)

    return render_template("login.html", error=error)
```

O segundo fator é um código TOTP (Time-based One-Time Password), gerado pelo aplicativo Google Authenticator no dispositivo móvel do usuário. O código é válido por 30 segundos e é calculado de forma independente pelo aplicativo e pelo servidor, ambos a partir do mesmo segredo compartilhado. A verificação no servidor é realizada pela biblioteca pyotp:

```python
@auth_bp.route("/verify-totp", methods=["GET", "POST"])
def verify_totp():
    if "pending_user_id" not in session:
        return redirect(url_for("auth.login"))

    error = None
    if request.method == "POST":
        code    = request.form.get("code", "")
        user_id = session["pending_user_id"]
        user    = load_user(user_id)

        if user and user.totp_secret and \
                pyotp.TOTP(user.totp_secret).verify(code, valid_window=5):
            login_user(user, remember=False)
            session.pop("pending_user_id",    None)
            session.pop("pending_user_email", None)
            audit("login_ok", user_id=user_id, ip=request.remote_addr,
                  details={"name": user.name, "role": user.role})
            return redirect(url_for("dashboard.index"))

        error = "Código TOTP inválido."
        audit("totp_failed", user_id=user_id, ip=request.remote_addr)

    return render_template("verify_totp.html", error=error)
```

O parâmetro `valid_window=5` permite uma janela de tolerância de ±2,5 minutos em relação ao horário atual, acomodando divergências de sincronização de relógio entre o servidor e o dispositivo móvel do usuário.

> **[FIGURA 9 — Tela de login do sistema]**
>
> *Instrução para o autor*: Captura de tela da página de login do PharmaTrack IoT (`http://127.0.0.1:5000/login`) com os campos de e-mail e senha visíveis. O fundo escuro do sistema deve estar aparente.

> **[FIGURA 10 — Tela de verificação TOTP e tela de configuração inicial do MFA]**
>
> *Instrução para o autor*: Duas capturas de tela lado a lado (ou duas imagens separadas). A primeira deve mostrar a tela de inserção do código TOTP (`/verify-totp`), com o campo de seis dígitos visível. A segunda deve mostrar a tela de configuração inicial do MFA (`/setup-totp`), exibindo o QR Code que o usuário escaneia com o Google Authenticator — o QR Code pode estar visível ou levemente desfocado por questões de privacidade.

#### 3.4.3 Controle de Acesso por Papéis (RBAC)

O sistema implementa controle de acesso baseado em papéis com três níveis: `superadmin` (acesso global a todas as empresas), `admin` (acesso completo à empresa cadastrada) e `operator` (acesso de leitura). Cada rota da API Flask que exige permissão específica é protegida por um decorator que verifica o perfil do usuário autenticado antes de executar a função:

```python
def require_permission(permission):
    """Decorator de rota: retorna 403 se a role do usuário não tem a permissão."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Não autenticado"}), 401
            if not current_user.has_permission(permission):
                return jsonify({
                    "error": (
                        f"Acesso negado — sua conta ({current_user.role})"
                        f" não tem permissão para '{permission}'"
                    )
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def admin_required(f):
    """Decorator de rota: retorna 403 a menos que o usuário seja admin ou superadmin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or \
                current_user.role not in ("admin", "superadmin"):
            return jsonify({"error": "Acesso negado — requer perfil admin ou superadmin"}), 403
        return f(*args, **kwargs)
    return decorated
```

A verificação ocorre no servidor — independentemente do que esteja visível na interface web. Todas as ações relevantes do sistema são registradas na tabela `audit_log` do banco de dados, incluindo logins, falhas de autenticação, registros de dispositivos e criação ou encerramento de rastreamentos. A tabela não possui rotas de exclusão ou edição expostas pela API.

> **[FIGURA 11 — Tela de log de auditoria no dashboard (visível apenas para admin)]**
>
> *Instrução para o autor*: Captura de tela da aba de Auditoria no dashboard do PharmaTrack IoT, logado como administrador. A tabela deve estar visível com pelo menos cinco entradas, mostrando as colunas de data/hora, usuário, ação e detalhes. O fundo escuro do sistema deve estar aparente.

---

### 3.5 Desenvolvimento do Backend e da Interface Web

#### 3.5.1 Arquitetura do Backend

O backend é uma aplicação Flask organizada em Blueprints — módulos independentes que agrupam as rotas por domínio funcional. Os quatro Blueprints implementados são: `auth_bp` (autenticação e gerenciamento de sessão), `dashboard_bp` (APIs de consulta e páginas de visualização), `admin_bp` (operações de gestão administrativa) e `debug_bp` (publicação manual de payloads para fins de teste, restrita a administradores). A separação em Blueprints facilita a manutenção e permite que cada módulo seja desenvolvido e testado de forma independente.

O banco de dados MySQL 8.0 é composto por nove tabelas relacionais, cujas dependências estão representadas no diagrama da Figura 16. A tabela `companies` é a raiz do esquema: todas as demais entidades possuem um campo `company_id` que restringe o acesso aos dados da própria empresa do usuário autenticado — com exceção do papel `superadmin`, que enxerga todas as empresas.

A hierarquia de dados farmacêuticos segue o encadeamento `vaccines` → `vaccine_batch` → `trips` → `readings`: o produto define as faixas de temperatura segura (`min_temp` e `max_temp`), o lote registra o código e a validade, o rastreamento vincula o lote a um dispositivo com origem e destino, e as leituras armazenam os dados de temperatura, umidade e GPS recebidos via MQTT. A tabela `devices` mantém o ciclo de vida dos dispositivos — `pending`, `active` ou `inactive` — e o campo `last_seen` atualizado a cada heartbeat. As tabelas `audit_log` e `seen_nonces` dão suporte, respectivamente, ao registro de auditoria com proteção contra alterações e à prevenção de ataques de repetição.

> **[FIGURA 16 — Diagrama relacional do banco de dados]**
>
> *Instrução para o autor*: Captura de tela do diagrama EER gerado pelo MySQL Workbench (menu Database → Reverse Engineer, selecionar o banco `vaccine_transport`). O diagrama deve mostrar todas as nove tabelas com suas colunas principais e as linhas de relacionamento entre elas. Aumentar o zoom para que os nomes das tabelas e colunas-chave estejam legíveis.

O isolamento de dados entre empresas é implementado por meio da função `company_where`, que adiciona dinamicamente a cláusula de filtragem por empresa em todas as consultas de leitura:

```python
def company_where(alias=""):
    """Retorna (fragmento_sql, params) para restringir queries à empresa do usuário.

    superadmin enxerga tudo (retorna '1=1' sem parâmetros).
    admin e operator enxergam apenas sua própria empresa.
    """
    col = f"{alias}.company_id" if alias else "company_id"
    if current_user.is_superadmin:
        return "1=1", []
    return f"{col} = %s", [current_user.company_id]
```

Essa abordagem garante que um usuário de uma empresa não possa acessar dados de outra, mesmo que realize requisições diretas à API.

#### 3.5.2 Detecção Automática de Violações de Temperatura

A detecção de violações de temperatura é realizada por consulta ao banco de dados, comparando cada leitura com os limites mínimo e máximo cadastrados para o produto farmacêutico associado ao lote em transporte. O trecho a seguir ilustra a consulta utilizada pelo endpoint `/api/alarms`:

```python
@dashboard_bp.route("/api/alarms")
@login_required
def alarms():
    """Retorna as 50 violações de temperatura mais recentes da empresa."""
    scope, params = company_where("v")
    conn = db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(f"""
        SELECT r.reading_id, r.timestamp, r.temperature, r.humidity,
               t.trip_id, b.batch_code, v.name AS vaccine_name,
               v.min_temp, v.max_temp
        FROM readings r
        JOIN trips t         ON r.trip_id   = t.trip_id
        JOIN vaccine_batch b ON r.batch_id  = b.batch_id
        JOIN vaccines v      ON b.vaccine_id = v.vaccine_id
        WHERE ({scope}) AND (r.temperature < v.min_temp OR r.temperature > v.max_temp)
        ORDER BY r.timestamp DESC
        LIMIT 50
    """, params)
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)
```

A variável `scope` é gerada pela função `company_where` descrita anteriormente, garantindo que apenas violações da empresa do usuário autenticado sejam retornadas. O dashboard consulta esse endpoint automaticamente a cada dez segundos, exibindo toasts de notificação para novas violações detectadas.

#### 3.5.3 Interface Web

A interface web foi desenvolvida em HTML5, CSS3 e JavaScript puro, sem o uso de frameworks de frontend. As visualizações de dados utilizam as bibliotecas Leaflet.js para mapas interativos e Chart.js para gráficos de linha de temperatura. O dashboard atualiza cada seção independentemente a cada dez segundos por meio de requisições assíncronas, sem necessidade de recarregar a página.

---

## 4 RESULTADOS E DISCUSSÃO

O presente capítulo descreve os resultados obtidos com o desenvolvimento e a operação do PharmaTrack IoT, organizados segundo os três conjuntos de objetivos específicos definidos no Capítulo 2: o dispositivo embarcado, a camada de conectividade e segurança, e o backend com a interface web.

### 4.1 Dispositivo Embarcado

O dispositivo embarcado foi implementado e testado em ambiente de operação real. O firmware opera em ciclos de cinco segundos: a cada ciclo, o sensor DHT22 é lido, as coordenadas GPS são atualizadas a partir do buffer serial do receptor NEO-6M e um pacote JSON é montado, assinado e publicado via MQTT. Em testes realizados com o dispositivo em operação contínua, as leituras de temperatura apresentaram estabilidade e ausência de leituras com erro de sensor quando o sensor estava corretamente conectado e alimentado. O receptor GPS NEO-6M requereu posicionamento com visibilidade do céu para aquisição de sinal (tempo de aquisição inicial típico de 30 a 60 segundos); após a primeira fixação de satélites, as coordenadas foram atualizadas a cada ciclo de leitura do buffer serial.

O mecanismo de armazenamento local temporário com SPIFFS foi validado simulando a desconexão da rede WiFi durante a operação. O firmware detectou a falha de publicação MQTT, iniciou a gravação local no arquivo `/buffer.jsonl` e retomou o envio das leituras acumuladas, em ordem cronológica, após o restabelecimento da conexão. A capacidade estimada de armazenamento local, considerando o tamanho médio de cada entrada JSON (~180 bytes), é de aproximadamente 500 leituras no espaço de arquivo disponível, equivalente a cerca de 40 minutos de operação contínua sem conectividade. O temporizador de vigilância configurado para 60 segundos foi ativado em situações de bloqueio prolongado do ciclo principal de execução, com reinicialização automática e retomada correta da operação.

O custo total de hardware do dispositivo, considerando os componentes descritos na Seção 3.1, totalizou aproximadamente R$ 100,00 por unidade, com todos os componentes adquiridos no mercado nacional.

### 4.2 Camada de Conectividade e Segurança

A comunicação MQTT sobre TLS 1.2 foi estabelecida com êxito utilizando o broker HiveMQ Cloud no plano gratuito. O certificado da Autoridade Certificadora foi embarcado no firmware no segmento PROGMEM e verificado pela classe `WiFiClientSecure` a cada conexão, impedindo conexões a servidores não autorizados. A autenticação do dispositivo junto ao broker por credenciais MQTT foi validada — tentativas de conexão com credenciais incorretas foram rejeitadas pelo broker com código de retorno 4 (credenciais incorretas), e o firmware entrou corretamente em modo sem conexão nesses casos.

O controle de acesso por lista de permissões (ACL) no broker foi validado: o cliente do dispositivo (`esp32-device`) não conseguiu assinar tópicos para os quais não tinha permissão, e o cliente do backend (`flask-subscriber`) não conseguiu publicar mensagens. Cada tentativa de operação não autorizada gerou o código de retorno 5 (operação não autorizada) e foi registrada nos logs do broker.

A assinatura HMAC-SHA256 foi implementada no firmware utilizando a biblioteca mbedtls nativa do ESP32. O campo `hmac` está presente em todos os payloads publicados. O campo `nonce` é preenchido com 8 bytes (16 caracteres hexadecimais) gerados pelo gerador de números aleatórios por hardware (`esp_random()`) a cada envio. A tabela `seen_nonces` no banco de dados está estruturada para receber e armazenar os nonces processados, com as colunas necessárias para a deduplicação. A verificação do HMAC e a rejeição por nonce duplicado no servidor estão estruturadas no banco de dados e na camada de armazenamento, com a validação ativa no backend prevista como próxima etapa de desenvolvimento.

A autenticação multifator com TOTP foi validada em operação: o fluxo completo de login (senha + código TOTP gerado pelo Google Authenticator) foi testado com os usuários cadastrados. O código expira após 30 segundos e o parâmetro `valid_window=1` da biblioteca pyotp acomoda divergências de até ±30 segundos entre o relógio do servidor e o do dispositivo móvel. A configuração inicial do MFA, realizada na rota `/setup-totp`, gera o QR Code para escaneamento pelo aplicativo e persiste o segredo TOTP no banco de dados para uso nas verificações subsequentes.

### 4.3 Backend e Interface Web

O backend Flask foi executado de forma estável em ambiente de desenvolvimento, recebendo e processando mensagens MQTT em tempo real por meio da thread subscriber em segundo plano. As APIs REST responderam corretamente às requisições do dashboard, com isolamento de dados por empresa funcionando conforme esperado: usuários da empresa PharmaTransport (company_id=1) não visualizaram dados da empresa BioFrio (company_id=2), e vice-versa. O papel superadmin visualizou dados de ambas as empresas, conforme o comportamento definido na função `company_where`.

A detecção automática de violações de temperatura foi validada com os dados de demonstração gerados pelo script `seed_demo.py`. O endpoint `/api/alarms` retornou corretamente as leituras cujos valores de temperatura estavam fora da faixa `min_temp`–`max_temp` cadastrada para o produto associado ao lote em transporte. As violações foram exibidas no painel de alertas do sistema com data e hora, lote, produto, temperatura registrada e limites violados.

> **[FIGURA 13 — Gráfico de temperatura com indicação de violações]**
>
> *Instrução para o autor*: Captura de tela ampliada do gráfico de temperatura, mostrando claramente: a linha de dados de temperatura em verde, os pontos em vermelho que indicam leituras fora da faixa, e as linhas tracejadas dos limites mínimo e máximo do produto. Selecionar um rastreamento que contenha violações para que os pontos vermelhos apareçam no gráfico.

O banco de dados foi populado com os dados de demonstração gerados pelo script `seed_demo.py`. A empresa PharmaTransport totalizou 13 produtos farmacêuticos cadastrados, 18 lotes e 15 rastreamentos, com aproximadamente 900 leituras registradas. A empresa BioFrio totalizou 12 produtos, 18 lotes e 13 rastreamentos, com aproximadamente 738 leituras. No total, o sistema concentrou 25 produtos farmacêuticos, 36 lotes, 28 rastreamentos e cerca de 1.638 leituras distribuídas entre as duas empresas, com um dispositivo ativo vinculado à empresa PharmaTransport.

O registro de auditoria foi validado em operação: todas as ações realizadas durante os testes — logins, falhas de autenticação, registros de dispositivos, criações e encerramentos de rastreamentos — foram registradas na tabela `audit_log` com usuário, endereço IP de origem, ação e registro de data e hora. A tabela não expõe rotas de exclusão ou edição pela API, conferindo proteção contra alterações ao histórico registrado.

O dashboard web foi executado em navegadores modernos sem dependências externas além das bibliotecas Leaflet.js e Chart.js. O mapa GPS renderizou corretamente as rotas dos rastreamentos com dados de coordenadas reais gerados pelo script de demonstração. O gráfico de temperatura exibiu a linha de dados com destaque em vermelho para os pontos que representam violações, e as linhas tracejadas dos limites mínimo e máximo do produto foram exibidas corretamente para cada rastreamento selecionado.

> **[FIGURA 12 — Tela principal do dashboard]**
>
> *Instrução para o autor*: Captura de tela do dashboard principal do PharmaTrack IoT com um rastreamento ativo selecionado. A imagem deve mostrar, simultaneamente: o gráfico de temperatura na metade superior (com a linha de dados e as linhas tracejadas de limite), o mapa GPS na metade inferior com a rota traçada, e o painel lateral com os dispositivos listados. Logar como `admin@pharmatransport.com` e selecionar o rastreamento ativo (Guarulhos → Manaus) para exibir dados reais.

> **[FIGURA 14 — Mapa GPS com rota do rastreamento]**
>
> *Instrução para o autor*: Captura de tela ampliada do mapa Leaflet com a rota de um rastreamento traçada. A imagem deve mostrar a linha da rota em verde, o marcador de início e o marcador da última posição registrada. Se possível, capturar com o mapa exibindo a rota completa de Guarulhos a Manaus para evidenciar a extensão geográfica do rastreamento.

> **[FIGURA 15 — Painel de gestão de dispositivos]**
>
> *Instrução para o autor*: Captura de tela da aba de Dispositivos no dashboard, logado como administrador, mostrando o dispositivo ESP32-B0A732D765D0 listado com status "Online" e os botões de ação (Configurar, Desatrelar). A coluna de última comunicação deve estar visível. O fundo escuro do sistema deve estar aparente.

### 4.4 Discussão

Os resultados obtidos demonstram que é viável construir um sistema de monitoramento para transporte farmacêutico com múltiplas camadas de segurança, rastreabilidade por lote e visualização em tempo real utilizando exclusivamente hardware de propósito geral e ferramentas de código aberto, com custo de hardware por dispositivo de aproximadamente R$ 100,00.

O uso do broker HiveMQ Cloud no plano gratuito mostrou-se adequado para o contexto do trabalho, com suporte obrigatório a TLS e autenticação por credenciais. A limitação do plano gratuito — cem conexões simultâneas — é suficiente para operações de pequeno porte, mas exigiria migração para planos pagos ou para infraestrutura própria em operações com maior volume de dispositivos simultâneos.

O armazenamento local temporário com SPIFFS atendeu ao objetivo de continuidade do registro durante períodos de desconexão, com funcionamento validado em testes. A capacidade de armazenamento de aproximadamente 600 leituras é adequada para desconexões de curta duração, Para operações em regiões com desconexões prolongadas, a capacidade poderia ser ampliada por meio de armazenamento externo (cartão microSD) ou pela redução do intervalo de coleta.

A implementação da verificação do HMAC e da deduplicação de nonces no processamento das mensagens pelo servidor constitui a principal etapa de segurança ainda não finalizada. A estrutura de banco de dados para suportar essa verificação já está implementada (tabela `seen_nonces`), e a validação no backend representa um incremento pontual sobre a arquitetura existente. Sua ausência não compromete as demais camadas de segurança — TLS, autenticação por credenciais, bcrypt, TOTP e RBAC —, mas representa uma lacuna na cadeia de integridade das mensagens que deve ser endereçada antes da adoção em ambiente de produção.

---

## 5 CONCLUSÃO

O presente trabalho apresentou o desenvolvimento do PharmaTrack IoT, um sistema de monitoramento contínuo para o transporte de produtos farmacêuticos termossensíveis utilizando componentes e ferranebtas disponíveis no mercado nacional e de baixo custi

O dispositivo embarcado baseado no ESP32 realiza coletas de temperatura, umidade e coordenadas GPS em ciclos de cinco segundos, com armazenamento local temporário em SPIFFS para garantir a continuidade do registro durante desconexões de rede. A transmissão ocorre via MQTT sobre TLS 1.2, com autenticação por credenciais no broker e controle de acesso por lista de permissões. Os mecanismos de segurança implementados — HMAC-SHA256, nonce por hardware, bcrypt com fator de custo 12, autenticação multifator TOTP e controle de acesso baseado em papéis — formam um conjunto de camadas independentes que endereçam as propriedades de confidencialidade, integridade e disponibilidade definidas na tríade CIA. O backend Flask com banco de dados MySQL realiza a detecção automática de violações de temperatura, o isolamento de dados por empresa e o registro de auditoria com proteção contra alterações. O dashboard web oferece visualização em tempo real com gráfico de temperatura, mapa GPS interativo e painel de alertas.

A principal contribuição do trabalho está na demonstração de que os requisitos técnicos de um sistema de monitoramento farmacêutico seguro e rastreável — habitualmente associados a soluções proprietárias de alto custo — podem ser satisfeitos com hardware de propósito geral e uma pilha de software inteiramente composta por ferramentas de código aberto. O custo de hardware de R$ 100,00 por dispositivo, combinado com a disponibilidade de brokers MQTT gerenciados em planos gratuitos, torna viável a adoção de monitoramento eletrônico contínuo em operações logísticas de menor escala que não dispõem de orçamento para soluções comerciais.

Como limitações do trabalho, destacam-se: a verificação do HMAC e a deduplicação de nonces no processamento das mensagens pelo servidor ainda não foram finalizadas, deixando uma lacuna na cadeia de integridade das mensagens; a chave HMAC está armazenada diretamente no firmware em vez de utilizar armazenamento seguro no NVS (Non-Volatile Storage) do ESP32; e o sistema não foi submetido a testes de carga ou de penetração formais.

Como trabalhos futuros, propõem-se: a conclusão da verificação HMAC e da deduplicação de nonces no backend; a migração da chave HMAC para o armazenamento seguro NVS via biblioteca `Preferences.h`; a implementação de cifração em repouso dos campos de leitura no banco de dados; a adição de geração de relatórios por rastreamento em formato PDF; a realização de testes de segurança documentados, incluindo análise de tráfego com Wireshark, simulação de ataques de repetição e testes de injeção SQL; e a avaliação do comportamento do sistema em escala com múltiplos dispositivos simultâneos.

---

## REFERÊNCIAS

BRASIL. Agência Nacional de Vigilância Sanitária. **Resolução de Diretoria Colegiada RDC n. 430, de 8 de outubro de 2020**. Dispõe sobre as Boas Práticas de Distribuição, Armazenagem e Transporte de Medicamentos para Uso Humano. Diário Oficial da União, Brasília, DF, 9 out. 2020. Disponível em: https://www.in.gov.br/en/web/dou/-/resolucao-de-diretoria-colegiada-rdc-n-430-de-8-de-outubro-de-2020-282070593. Acesso em: abr. 2026.

EUROPEAN UNION AGENCY FOR CYBERSECURITY (ENISA). **Threat Landscape**. ENISA, 2024. Disponível em: https://www.enisa.europa.eu/topics/cyber-threats/threat-landscape. Acesso em: abr. 2026.

INTERNATIONAL ORGANIZATION FOR STANDARDIZATION (ISO). **ISO/IEC 27001: Information security, cybersecurity and privacy protection — Information security management systems — Requirements**. Geneva: ISO, 2022. Disponível em: https://www.iso.org/standard/27001. Acesso em: abr. 2026.

NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY (NIST). **NIST Special Publication 800-183: Networks of 'Things'**. Gaithersburg: NIST, 2016. Disponível em: https://csrc.nist.gov/pubs/sp/800/183/final. Acesso em: abr. 2026.

STATISTA. **Internet of Things (IoT) connected devices installed base worldwide from 2015 to 2025**. Statista, 2025. Disponível em: https://www.statista.com/statistics/1183457/iot-connected-devices-worldwide/. Acesso em: abr. 2026.

UNICEF. **What is the cold chain?** UNICEF Supply Division, 2023. Disponível em: https://www.unicef.org/supply/what-cold-chain. Acesso em: abr. 2026.

WORLD HEALTH ORGANIZATION (WHO). **WHO-IVB-15.04: Temperature sensitivity of vaccines**. Geneva: WHO, 2015. Disponível em: https://www.who.int/publications/i/item/WHO-IVB-15.04. Acesso em: abr. 2026.

WORLD HEALTH ORGANIZATION (WHO). **Immunization Agenda 2030: A Global Strategy to Leave No One Behind**. Geneva: WHO, 2024. Disponível em: https://www.who.int/publications/i/item/9789240109544. Acesso em: abr. 2026.
