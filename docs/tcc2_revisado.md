
UNIVERSIDADE DO VALE DO PARAÍBA
FACULDADE DE ENGENHARIAS, ARQUITETURA E URBANISMO
CURSO DE ENGENHARIA DA COMPUTAÇÃO






Guilherme Palmanhani Valli






TRABALHO DE CONCLUSÃO II
Sistema IoT Seguro para Rastreabilidade e Monitoramento no Controle de Farmacêuticos

















SÃO JOSÉ DOS CAMPOS
2026

RESUMO
O transporte de produtos farmacêuticos termossensíveis — como vacinas, insulinas e imunobiológicos — exige controle rigoroso de temperatura ao longo de toda a cadeia logística, denominada cadeia de frio. A manutenção das condições térmicas adequadas em cada etapa do transporte é determinante para a preservação da eficácia e da segurança desses produtos, além de ser exigência prevista em regulamentação nacional. O presente trabalho apresenta o desenvolvimento do PharmaTrack IoT, um sistema de monitoramento contínuo para transporte de produtos farmacêuticos, construído sobre uma arquitetura de quatro pilares: Percepção (dispositivo embarcado ESP32 com sensores de temperatura, umidade e GPS), Conectividade (protocolo MQTT sobre TLS 1.2), Análise (backend Python Flask com banco de dados relacional MySQL) e Ação (dashboard web com visualização em tempo real). A segurança da informação foi incorporada como requisito desde a concepção do sistema, incluindo autenticação multifator baseada em TOTP, controle de acesso baseado em papéis, assinatura digital de mensagens e registro de auditoria de todas as ações. O custo de hardware por dispositivo é de aproximadamente R$ 100,00, com infraestrutura de software inteiramente baseada em componentes de código aberto. O desenvolvimento teve como referência os requisitos da Resolução RDC nº 430/2020 da Agência Nacional de Vigilância Sanitária (Anvisa) e as diretrizes da norma ISO/IEC 27001:2022. Os resultados evidenciam a viabilidade técnica do desenvolvimento de um sistema de monitoramento farmacêutico seguro, rastreável e de baixo custo, utilizando hardware de propósito geral e ferramentas amplamente disponíveis.


Palavras-chave: Internet das Coisas; cadeia de frio farmacêutica; segurança da informação; MQTT; autenticação multifator; controle de acesso; monitoramento de transporte; Anvisa.









ABSTRACT
The transportation of temperature-sensitive pharmaceutical products — such as vaccines, insulins and immunobiologicals — requires strict temperature control throughout the entire logistics chain, known as the cold chain. Maintaining adequate thermal conditions at each stage of transportation is essential for preserving the efficacy and safety of these products, and is also a requirement established by national regulation. This work presents the development of PharmaTrack IoT, a continuous monitoring system for pharmaceutical products, built on a four-pillar architecture: Perception (ESP32 embedded device with temperature, humidity and GPS sensors), Connectivity (MQTT protocol over TLS 1.2), Analysis (Python Flask backend with MySQL relational database) and Action (web dashboard with real-time visualization). Information security was incorporated as a requirement from the system's inception, including TOTP-based multi-factor authentication, role-based access control, message digital signatures, and an audit log with protection against modification of all system actions. The hardware cost per device is approximately R$ 100.00, with software infrastructure entirely based on open-source components. The development was guided by the requirements of ANVISA's RDC 430/2020 and the controls outlined in ISO/IEC 27001:2022. Results show the technical feasibility of developing a secure, traceable and low-cost pharmaceutical monitoring system using general-purpose hardware and widely available tools.


Keywords: Internet of Things; pharmaceutical cold chain; information security; MQTT; multi-factor authentication; access control; transport monitoring; ANVISA.




INTRODUÇÃO

O setor farmacêutico compreende um conjunto diversificado de produtos cujas propriedades terapêuticas dependem diretamente da manutenção de condições ambientais controladas ao longo de todo o seu ciclo de vida — da fabricação à administração ao paciente. Entre esses produtos, os denominados termossensíveis requerem atenção especial durante as etapas de distribuição e transporte, pois estão sujeitos à degradação irreversível quando expostos a temperaturas fora da faixa recomendada pelo fabricante. A logística desses produtos é organizada por meio do que se denomina cadeia de frio farmacêutica, estrutura que envolve infraestrutura de armazenamento refrigerado, veículos adequados, equipamentos de monitoramento e procedimentos operacionais padronizados (WHO, 2015).

A cadeia de frio farmacêutica é definida pela Organização Mundial da Saúde (OMS) como o sistema de armazenagem e distribuição que mantém produtos termossensíveis dentro da faixa de temperatura recomendada desde o momento de sua fabricação até o ponto de uso (WHO, 2015). A cadeia é composta por elos sequenciais — fabricante, armazém central, distribuidor regional, ponto de entrega e unidade de saúde — e cada elo deve garantir individualmente as condições térmicas e de umidade adequadas ao produto em questão, conforme mostrado na figura 1.

Figura 1: Representação esquemática da cadeia de frio farmacêutica

Fonte: O autor
A falha na manutenção das condições térmicas pode resultar em desnaturação de proteínas, perda de potência imunogênica, cristalização de compostos ou degradação química irreversível. Em muitos casos, o produto comprometido não apresenta alterações visuais perceptíveis ao operador, o que torna o monitoramento instrumental a forma necessária de verificar se as condições foram preservadas ao longo de todo o trajeto (UNICEF, 2023). A OMS estima que vacinas enviadas a países em desenvolvimento apresentam taxas de desperdício que, em algumas regiões, ultrapassam 50% do total distribuído, com condições inadequadas de armazenagem e transporte entre os principais fatores contribuintes (WHO, 2024). Segundo relatório da organização, a implementação de sistemas de monitoramento efetivos nas etapas de distribuição é um dos elementos centrais para a redução dessas perdas e para o fortalecimento dos programas nacionais de imunização.

A viabilidade técnica de sistemas IoT para o monitoramento contínuo de vacinas em redes reais de distribuição foi demonstrada em implantações de larga escala. Arquiteturas compostas por sensores de temperatura de baixo consumo, gateways inteligentes e equipamentos embarcados em veículos, integradas a plataformas de análise em nuvem, atingiram taxas de perda de pacotes inferiores a 1% e viabilizaram a geração de alertas automáticos de desvios térmicos com rastreabilidade digital completa ao longo de toda a cadeia logística. Esses resultados reforçam a factibilidade do monitoramento eletrônico contínuo como alternativa concreta às abordagens tradicionais de controle manual em operações com insumos termossensíveis (JIANG; JIA; GUO, 2024).

No contexto brasileiro, a Agência Nacional de Vigilância Sanitária (Anvisa) publicou a Resolução RDC nº 430/2020, que estabelece as Boas Práticas de Distribuição, Armazenagem e Transporte de Medicamentos para Uso Humano (ANVISA, 2020). A norma específica, entre outros aspectos, que as condições de temperatura e umidade devem ser monitoradas e registradas durante o transporte, com uso de equipamentos calibrados e em intervalos que permitam a verificação contínua das condições ao longo do trajeto. Determina também a rastreabilidade por número de lote do produto, a identificação dos responsáveis por cada etapa e a adoção de procedimentos documentados para o tratamento de desvios de temperatura. Esses requisitos estabelecem as premissas técnicas e documentais que nortearam o desenvolvimento do presente trabalho.

A Internet das Coisas — do inglês Internet of Things, comumente abreviada como IoT — é definida pelo Instituto Nacional de Padrões e Tecnologia dos Estados Unidos (NIST) como uma infraestrutura de dispositivos interconectados equipados com identificadores únicos e a capacidade de coletar e transmitir dados por redes de comunicação, sem necessidade de interação humana direta (NIST, 2016). De acordo com levantamento da Statista, estima-se que o número global de dispositivos IoT ativos supere 18 bilhões de unidades em 2025, reflexo da crescente adoção da tecnologia em aplicações industriais, de saúde e de infraestrutura (STATISTA, 2025). 
No segmento de saúde, a IoT encontra aplicação direta no monitoramento de cadeias logísticas de insumos termossensíveis, possibilitando o registro contínuo e auditável das condições de transporte. Essa tecnologia permite a instalação de sensores embarcados em veículos ou embalagens de transporte que coletam e transmitem continuamente dados de temperatura, umidade e localização geográfica para plataformas de análise acessíveis remotamente, conforme mostrado na Figura 2.

Figura 2: Modelo de comunicação IoT: dispositivo embarcado, broker MQTT e dashboard web

Fonte: O autor

A ampla disseminação de dispositivos IoT em ambientes críticos — como saúde, infraestrutura e logística — amplia a superfície de ataque disponível para agentes maliciosos, tornando a segurança da informação um aspecto indissociável do projeto de tais sistemas. A Agência da União Europeia para a Cibersegurança (ENISA) documenta, em seus relatórios anuais sobre o panorama de ameaças cibernéticas, que dispositivos IoT figuram entre os vetores mais explorados em campanhas de ataque a infraestruturas críticas, frequentemente em razão de capacidade computacional limitada, longos ciclos de atualização e ausência de mecanismos de autenticação robustos (ENISA, 2024). 

A segurança do protocolo MQTT em ambientes IoT tem sido objeto de pesquisa ativa em razão das limitações computacionais dos dispositivos embarcados. Abordagens baseadas em TLS, apesar de garantirem confidencialidade e integridade das mensagens transmitidas, impõem sobrecarga de comunicação e processamento significativa em hardware com recursos restritos. Frameworks alternativos baseados em criptografia de curva elíptica demonstraram reduções de até 80% na sobrecarga de comunicação e de até 40% na sobrecarga computacional em relação ao TLS convencional, mantendo as propriedades de autenticação e integridade necessárias para a operação segura de sistemas de monitoramento IoT em larga escala (VAN GLABBEEK et al., 2022).

No contexto de sistemas de monitoramento farmacêutico, a manipulação de dados de temperatura registrados durante o transporte ou o acesso não autorizado ao sistema de gestão de rastreamentos são exemplos de ocorrências que podem ter consequências diretas para a qualidade dos produtos e para a saúde dos pacientes.

A análise dos impactos potenciais de falhas de segurança em sistemas dessa natureza pode ser estruturada segundo as três propriedades da tríade CIA. Uma violação de confidencialidade, exemplificada pelo acesso não autorizado aos dados de rastreamento armazenados, expõe informações de alto valor estratégico e comercial: rotas logísticas utilizadas, volumes e frequências de entrega por produto, destinos de distribuição e dados de identificação dos responsáveis por cada etapa da operação. Essas informações podem ser exploradas por concorrentes para mapear a rede de distribuição de uma empresa farmacêutica, ou por agentes mal-intencionados para identificar padrões de transporte e planejar interceptações físicas de cargas de alto valor. Do ponto de vista regulatório, a exposição de dados de lote e distribuição pode ainda configurar infração à Lei Geral de Proteção de Dados (LGPD), especialmente quando os registros contêm dados vinculados a pessoas físicas responsáveis pelas operações.

Uma violação de integridade, caracterizada pela adulteração de leituras de temperatura armazenadas ou pela injeção de leituras falsas no sistema, representa o risco mais grave para a saúde pública. Em um sistema de monitoramento sem mecanismos de verificação da autenticidade das mensagens, um atacante com acesso ao canal de comunicação poderia substituir leituras reais que registram temperaturas acima do limite seguro por valores dentro da faixa aceitável, mascarando uma violação que comprometeu irreversivelmente o lote. O produto seria então liberado para uso com base em dados forjados, chegando ao paciente com eficácia reduzida ou nula, sem que qualquer indicador visual ou alerta do sistema sinalizasse o problema. A ENISA destaca que ataques de falsificação de dados de sensores em sistemas IoT industriais e de saúde são crescentes e frequentemente direcionados a cenários em que a decisão de liberar ou descartar um produto depende exclusivamente do registro digital (ENISA, 2024). Além do risco direto ao paciente, registros adulterados comprometem a rastreabilidade por lote exigida pela RDC nº 430/2020, inviabilizando investigações posteriores em caso de eventos adversos.

Uma violação de disponibilidade, decorrente da indisponibilidade do sistema de monitoramento durante o transporte por falha técnica ou interrupção do serviço de comunicação, interrompe a cadeia de custódia digital do produto. Períodos sem registro criam lacunas no histórico de condições de transporte que não podem ser preenchidas retroativamente, tornando impossível atestar que as condições adequadas foram mantidas durante o intervalo sem dados. Em operações sujeitas à fiscalização da Anvisa ou a auditorias de clientes institucionais, a ausência de registros contínuos pode resultar na rejeição do lote no destino, mesmo que as condições tenham sido preservadas ao longo de todo o trajeto. A indisponibilidade recorrente do sistema de monitoramento pode ainda comprometer a credibilidade da empresa perante órgãos regulatórios e dificultar a renovação de autorizações de funcionamento.

A norma internacional ISO/IEC 27001 define os requisitos para o estabelecimento e operação de um sistema de gestão de segurança da informação, abrangendo controles de acesso, criptografia, segurança de comunicações, rastreabilidade de eventos e gestão de incidentes (ISO, 2022). O NIST, por sua vez, na publicação SP 800-183, define os princípios de confiabilidade, segurança e resiliência aplicáveis a sistemas formados por redes de dispositivos conectados, incluindo requisitos de autenticidade das mensagens, confidencialidade dos dados transmitidos e rastreabilidade das operações realizadas (NIST, 2016). Ambos os documentos foram utilizados como referência orientadora no desenvolvimento do presente trabalho, especialmente na definição das camadas de segurança implementadas, conforme mostrado na Figura 3.

Figura 3: Camadas de segurança implementadas

Fonte: O autor


Diante desse cenário, o presente trabalho propõe e implementa o PharmaTrack IoT, um sistema de monitoramento contínuo para o transporte de produtos farmacêuticos termossensíveis, desenvolvido com foco na acessibilidade econômica e na segurança da informação. O sistema é estruturado seguindo quatro pilares para sistemas IoT: Percepção, Conectividade, Análise e Ação. Estes compõem a arquitetura do projeto, conforme mostrado na Figura 4.
O pilar de Percepção é composto por um dispositivo embarcado baseado no microcontrolador ESP32, equipado com sensor DHT22 para medição de temperatura e umidade e receptor GPS NEO-6M.
O pilar de Conectividade utiliza o protocolo MQTT sobre TLS 1.2, com broker em nuvem gerenciada. 
O pilar de Análise compreende um backend desenvolvido em Python com o framework Flask e banco de dados MySQL, responsável pelo processamento das mensagens, pela detecção de violações de temperatura e pelos controles de autenticação e autorização. 
O pilar de Ação é um dashboard web acessível por navegador, com atualização automática a cada dez segundos, que apresenta gráficos de temperatura, mapa interativo da rota percorrida, painel de alertas e interfaces de gestão administrativa.

Figura 4: Arquitetura do PharmaTrack IoT
Fonte: O autor

A principal motivação para o desenvolvimento do PharmaTrack IoT é a acessibilidade econômica. Apesar da existência de soluções comerciais para monitoramento de cadeia de frio, elas apresentam alto custo e limitada transparência em relação à segurança dos dados, dificultando sua adoção em operações de menor escala. A utilização de hardware de propósito geral disponível no mercado nacional, associada a uma pilha de software inteiramente composta por ferramentas de código aberto, resulta em um custo de implantação por dispositivo significativamente menor. Esse diferencial torna viável a adoção de monitoramento eletrônico contínuo em operações logísticas de menor escala. Sob a perspectiva acadêmica, o trabalho demonstra como princípios consolidados de segurança da informação — autenticação multifator, controle de acesso por perfis, assinatura digital de mensagens e defesa em profundidade — podem ser aplicados de forma integrada em um sistema IoT de baixo custo, com referência direta à regulamentação vigente aplicável ao setor farmacêutico brasileiro.


























OBJETIVO GERAL

O objetivo geral do presente trabalho é desenvolver e implementar o PharmaTrack IoT, um sistema de baixo custo para monitoramento contínuo e rastreabilidade no transporte de produtos farmacêuticos termossensíveis, integrando hardware embarcado, software de análise, protocolos de comunicação e controles de cibersegurança em um sistema IoT, tendo como referência os requisitos da Resolução RDC nº 430/2020 da Anvisa e as diretrizes da norma ISO/IEC 27001:2022.

OBJETIVOS ESPECÍFICOS

Arquitetar e implementar um dispositivo embarcado de baixo custo e baixo consumo energético baseado no microcontrolador ESP32, capaz de capturar temperatura com precisão de ±0,5°C e coordenadas geográficas com precisão de ±2,5 metros, operando em ciclos de coleta de cinco segundos.

Construir uma aplicação servidor capaz de receber e processar mensagens MQTT, detectar automaticamente violações de temperatura em relação aos limites cadastrados por produto e armazenar os dados em banco de dados relacional; e desenvolver um dashboard web com monitoramento em tempo real de métricas operacionais — temperatura, localização, alarmes e indicadores de conectividade —, com interfaces de gestão de dispositivos, rastreamentos, usuários, produtos farmacêuticos e lotes, e suporte a múltiplas empresas em uma única instalação.

Aplicar um conjunto integrado de controles de segurança para proteger a confidencialidade e a integridade dos dados no sistema, incluindo: transmissão cifrada via MQTT sobre TLS 1.2 com autenticação por credenciais e controle de acesso por lista de permissões no broker, assegurando a confidencialidade do canal e impedindo o acesso de clientes não autorizados, uma vez que dispositivos IoT operam frequentemente em redes compartilhadas sem proteção nativa de transporte (VAN GLABBEEK et al., 2022); assinatura digital HMAC-SHA256 com nonce gerado por hardware para prevenção de ataques de repetição, garantindo a autenticidade e a integridade de cada mensagem transmitida e tornando detectável qualquer adulteração de conteúdo após sua geração, mecanismo reconhecido como padrão para autenticação de mensagens em canais com chave simétrica (STALLINGS, 2022); autenticação multifator baseada em TOTP, que acrescenta uma segunda camada de verificação independente da senha e demonstra resistência efetiva a ataques de força bruta e ao comprometimento de credenciais estáticas em ambientes IoT (BAMASHMOS; CHILAMKURTI; SALEHI SHAHRAKI, 2024); controle de acesso baseado em papéis com três níveis de permissão distintos, aplicando o princípio de menor privilégio de forma que cada perfil de usuário opere exclusivamente dentro do escopo necessário à sua função; e registro de auditoria imutável de todas as ações realizadas no sistema, atendendo ao requisito de rastreabilidade e não repúdio estabelecido como controle obrigatório para sistemas de informação em ambientes regulados (ISO, 2022).

Integrar estratégias de continuidade e recuperação que assegurem a operação e a disponibilidade do sistema, por meio de armazenamento local temporário das leituras em memória não volátil durante períodos de desconexão de rede, com envio automático em ordem cronológica ao restabelecer a conectividade, e temporizador de vigilância com reinicialização automática do microcontrolador em caso de travamento do ciclo principal de execução.












METODOLOGIA

A metodologia deste trabalho foi estruturada de forma a descrever o processo de concepção, desenvolvimento e validação de um sistema de Internet das Coisas (IoT) voltado para o monitoramento seguro do transporte de vacinas. O sistema foi projetado com base em uma arquitetura distribuída que integra hardware, software e protocolos de comunicação para garantir a coleta, transmissão, armazenamento e análise de dados sensíveis em tempo real. Para isso, foi desenvolvido um protótipo composto por um microcontrolador ESP32, sensores DHT22 para medição de temperatura e umidade, módulo GPS para rastreamento de localização, além de um sistema de alimentação baseado em bateria portátil, assegurando a operação contínua durante o deslocamento. A comunicação entre o dispositivo e o servidor foi realizada por meio do protocolo MQTT, enquanto os dados coletados foram armazenados em um banco de dados relacional para análise e visualização.

A estrutura metodológica seguiu os princípios fundamentais de um sistema IoT, sendo organizada de acordo com os quatro pilares que o sustentam: Percepção, Conectividade, Análise e Ação. Essa divisão permite compreender, de forma sistemática, como cada etapa contribui para o funcionamento e a segurança do sistema. Assim, as subseções seguintes detalham o papel de cada pilar dentro do contexto do projeto, abordando desde a captação dos dados ambientais até os processos que asseguram a integridade, autenticidade e disponibilidade das informações monitoradas durante o transporte das vacinas.

O desenvolvimento do PharmaTrack IoT envolveu componentes de hardware e ferramentas de software cuja seleção foi orientada pelo critério de acessibilidade econômica e pela disponibilidade de documentação técnica aberta.

Os componentes de hardware utilizados foram: o microcontrolador ESP32 DevKit V1 (arquitetura Xtensa LX6 dual-core, 240 MHz, 520 KB SRAM, WiFi 802.11 b/g/n), que constitui a unidade central de processamento e comunicação do dispositivo; o sensor DHT22, responsável pela leitura de temperatura (faixa de −40°C a +80°C, precisão ±0,5°C) e umidade relativa (0–100%, precisão ±2%); o receptor GPS NEO-6M, que fornece coordenadas geográficas por comunicação UART com protocolo NMEA 0183 e precisão típica de ±2,5 m; uma bateria portátil (powerbank) com capacidade de 10.000 mAh para alimentação autônoma do dispositivo; e uma caixa de proteção impressa em PLA por processo FDM, modelada em OpenSCAD com dimensões de 170 × 90 × 80 mm.

As ferramentas de software utilizadas foram: Arduino IDE para desenvolvimento e compilação do firmware em C++ com o Arduino Framework; Python 3.11 como linguagem do backend; Flask 3.0.3 como framework web; MySQL 8.0 como banco de dados relacional; paho-mqtt 2.1.0 como cliente MQTT para Python; Flask-Login 0.6.3 para gerenciamento de sessões autenticadas; bcrypt 4.1.3 para hash de senhas; pyotp 2.9.0 para implementação do algoritmo TOTP; HiveMQ Cloud (plano gratuito) como broker MQTT gerenciado; AutoDesk Fusion para modelagem 3D da caixa de proteção; e Git para controle de versão do código-fonte.

O ambiente de desenvolvimento utilizado foi um computador pessoal com sistema operacional Windows 11, com o servidor MySQL e Flask.

O dispositivo embarcado constitui o pilar de Percepção do sistema e é responsável por coletar os dados físicos do ambiente de transporte — temperatura, umidade e localização geográfica — e transmiti-los ao servidor. O hardware é composto pelo microcontrolador ESP32, o sensor de temperatura e umidade DHT22 e o receptor GPS NEO-6M, conectados em uma protoboard e protegidos por uma caixa impressa em PLA

O firmware foi desenvolvido em linguagem C++ com o Arduino Framework, utilizando as bibliotecas PubSubClient (cliente MQTT), ArduinoJson (serialização JSON), TinyGPS++ (interpretação de dados NMEA do receptor GPS) e WiFiClientSecure (comunicação TLS). A lógica principal do firmware opera em ciclos de cinco segundos: a cada ciclo, o sensor DHT22 é lido, as coordenadas GPS são atualizadas e um pacote JSON é montado e transmitido. O trecho a seguir ilustra a leitura dos sensores e a montagem do payload:


O campo 'device_id' é derivado automaticamente do endereço MAC do hardware, garantindo unicidade por dispositivo sem necessidade de configuração manual. O campo 'nonce' recebe um valor aleatório único gerado pelo gerador de números aleatórios por hardware do ESP32 a cada envio, garantindo que dois payloads nunca sejam idênticos.

Para garantir a continuidade do registro durante períodos de desconexão da rede, o firmware utiliza o sistema de arquivos SPIFFS (SPI Flash File System), presente na memória flash interna do ESP32. Quando a publicação MQTT falha, a leitura é gravada localmente em um arquivo no formato JSON Lines (uma entrada por linha). Ao restabelecer a conexão, o firmware realiza o envio das leituras acumuladas em ordem cronológica antes de retomar a operação normal:


O firmware também implementa um Watchdog Timer (WDT) configurado para 60 segundos. Caso o ciclo principal do programa trave por qualquer motivo, o WDT provoca uma reinicialização automática do microcontrolador, garantindo retomada da operação sem intervenção manual.

A transmissão dos dados coletados pelo dispositivo ao servidor utiliza o protocolo MQTT com garantia de entrega de nível 1 (QoS 1), que assegura que cada mensagem seja entregue ao menos uma vez. O broker escolhido é o HiveMQ Cloud, serviço gerenciado com plano gratuito que suporta até cem conexões simultâneas e impõe o uso de TLS como requisito obrigatório.

Toda a comunicação ocorre sobre TLS 1.2 na porta 8883. No lado do dispositivo, a conexão cifrada é estabelecida por meio da classe 'WiFiClientSecure' do SDK do ESP32. Durante o desenvolvimento, identificou-se uma incompatibilidade entre a implementação mbedtls do ESP32 e a cadeia de certificados ISRG Root X1 utilizada pelo HiveMQ Cloud, o que impediu o uso de 'setCACert()'. Como solução, o método 'setInsecure()' foi utilizado, que mantém a cifragem do canal TLS ativa mas suprime a validação do certificado do servidor:



O uso de 'setInsecure()' garante que o tráfego permaneça cifrado e inacessível a um observador passivo na rede, porém não protege contra ataques de intermediário ativo (man-in-the-middle). A autenticação do broker é compensada parcialmente pela autenticação por credenciais exigida pelo próprio HiveMQ Cloud. A substituição por 'setCACert()' com a CA raiz correta constitui uma das melhorias identificadas para trabalhos futuros.
O controle de acesso no broker é implementado por meio de uma lista de permissões (ACL) que restringe as operações de cada usuário MQTT aos tópicos que lhe são pertinentes. O dispositivo possui permissão apenas para publicar nos tópicos 'vaccines/readings' e 'vaccines/heartbeat', enquanto o backend Flask possui permissão apenas para assinar esses mesmos tópicos — sem capacidade de publicação. Essa separação garante que nenhum componente possa executar operações fora do seu escopo definido.

No lado do servidor, o subscriber MQTT é executado em uma thread separada da aplicação Flask, utilizando a biblioteca paho-mqtt. A sessão é configurada como persistente ('clean_session=False'), o que permite ao broker reter e entregar mensagens que chegaram enquanto o servidor estava temporariamente indisponível:


Para garantir a autenticidade e a integridade de cada mensagem enviada pelo dispositivo, o firmware calcula uma assinatura digital utilizando o algoritmo HMAC-SHA256. O cálculo é realizado com a biblioteca 'mbedtls', nativa do ESP32, que aproveita o acelerador criptográfico em hardware. A chave utilizada é compartilhada entre o dispositivo e o servidor:



A assinatura resultante é incluída no campo 'hmac' do payload JSON. Qualquer alteração no conteúdo da mensagem após sua geração produz um HMAC completamente diferente, permitindo ao servidor detectar adulterações.

Para suportar a prevenção de ataques de repetição — nos quais um atacante captura uma mensagem válida e a reencaminha posteriormente —, cada mensagem inclui um campo 'nonce', um valor aleatório de 64 bits gerado pelo gerador de números aleatórios por hardware do ESP32. A verificação e deduplicação desse valor no servidor, utilizando a tabela 'seen_nonces', está prevista como etapa de segurança complementar:








O acesso ao sistema de gestão é protegido por dois fatores sequenciais. O primeiro é a verificação da senha, realizada com o algoritmo bcrypt. O bcrypt é um algoritmo de hash projetado especificamente para senhas, com fator de custo configurável que torna o processo de verificação intencionalmente lento, dificultando ataques de força bruta. As senhas são armazenadas no banco de dados exclusivamente em formato de hash, nunca em texto puro:













O segundo fator é um código TOTP (Time-based One-Time Password), gerado pelo aplicativo Google Authenticator no dispositivo móvel do usuário. O código é válido por 30 segundos e é calculado de forma independente pelo aplicativo e pelo servidor, ambos a partir do mesmo segredo compartilhado. A verificação no servidor é realizada pela biblioteca pyotp:



O sistema implementa controle de acesso baseado em papéis com três níveis: 'superadmin' (acesso global a todas as empresas), 'admin' (acesso completo à empresa cadastrada) e 'operator' (acesso de leitura). Cada rota da API Flask que exige permissão específica é protegida por um decorator que verifica o perfil do usuário autenticado antes de executar a função:









A verificação ocorre no servidor — independentemente do que esteja visível na interface web. Todas as ações relevantes do sistema são registradas na tabela 'audit_log' do banco de dados, incluindo logins, falhas de autenticação, registros de dispositivos e criação ou encerramento de rastreamentos. A tabela não possui rotas de exclusão ou edição expostas pela API.






Figura 19: Ações relevantes do sistema registradas

Fonte: O autor

O backend é uma aplicação Flask organizada em Blueprints — módulos independentes que agrupam as rotas por domínio funcional. Os quatro Blueprints implementados são: 'auth_bp' (autenticação e gerenciamento de sessão), 'dashboard_bp' (APIs de consulta e páginas de visualização), 'admin_bp' (operações de gestão administrativa) e 'debug_bp' (publicação manual de payloads para fins de teste, restrita a administradores). A separação facilita a manutenção e permite que cada módulo seja desenvolvido e testado de forma independente.

O banco de dados MySQL 8.0 é composto por nove tabelas relacionais, cujas dependências estão representadas no diagrama da Figura 20. A tabela 'companies' é a raiz do esquema: todas as demais entidades possuem um campo 'company_id' que restringe o acesso aos dados da própria empresa do usuário autenticado — com exceção do papel 'superadmin', que enxerga todas as empresas.

A hierarquia e os relacionamentos de dados farmacêuticos estão mostrados na Figura 5, seguindo o encadeamento 'vaccines' → 'vaccine_batch' → 'trips' → 'readings': o produto define as faixas de temperatura segura ('min_temp' e 'max_temp'), o lote registra o código e a validade, o rastreamento vincula o lote a um dispositivo com origem e destino, e as leituras armazenam os dados de temperatura, umidade e GPS recebidos via MQTT. A tabela 'devices' mantém o ciclo de vida dos dispositivos — 'pending', 'active' ou 'inactive' — e o campo 'last_seen' atualizado a cada ciclo. As tabelas 'audit_log' e 'seen_nonces' dão suporte, respectivamente, ao registro de auditoria com proteção contra alterações e à deduplicação de nonces para prevenção futura de ataques de repetição.

Figura 5: Banco de dados relacional

Fonte: O autor

A detecção de violações de temperatura é realizada por consulta ao banco de dados, comparando cada leitura com os limites mínimo e máximo cadastrados para o produto farmacêutico associado ao lote em transporte. O trecho a seguir ilustra a consulta utilizada pelo endpoint '/api/alarms':
Figura 21: Banco de dados relacional

Fonte: O autor

A variável 'scope' é gerada pela função 'company_where' descrita anteriormente, garantindo que apenas violações da empresa do usuário autenticado sejam retornadas. O dashboard consulta esse endpoint automaticamente a cada dez segundos, exibindo toasts de notificação para novas violações detectadas.

A interface web segue uma arquitetura de duas camadas: o backend em Python com Flask é responsável pela lógica de negócio, autenticação, acesso ao banco de dados e exposição das APIs REST; o frontend, desenvolvido em HTML5, CSS3 e JavaScript, é responsável pela renderização e pela interação no navegador. Flask serve as páginas iniciais por meio de templates Jinja2, e a partir daí o JavaScript assume o controle, consultando as APIs do backend de forma assíncrona a cada dez segundos para atualizar cada seção do dashboard sem recarregar a página. As visualizações de dados utilizam as bibliotecas Leaflet.js para mapas interativos e Chart.js para gráficos de linha de temperatura, ambas executadas inteiramente no navegador do usuário.
RESULTADOS E DISCUSSÃO 

O presente capítulo descreve os resultados obtidos com o desenvolvimento e a operação do PharmaTrack IoT, organizados segundo o conjunto de objetivos específicos definidos na seção anterior

O dispositivo embarcado, mostrado nas Figuras 6 e 7, foi implementado e testado em ambiente de operação real. O firmware opera em ciclos de cinco segundos: a cada ciclo, o sensor DHT22 é lido, as coordenadas GPS são atualizadas a partir do buffer serial do receptor NEO-6M e um pacote JSON é montado, assinado e publicado via MQTT. Em testes realizados com o dispositivo em operação contínua, as leituras de temperatura apresentaram estabilidade e ausência de leituras com erro. O receptor GPS NEO-6M requereu posicionamento com visibilidade do céu para aquisição de sinal (tempo de aquisição inicial típico de 30 a 60 segundos); após a primeira fixação de satélites, as coordenadas foram atualizadas a cada ciclo de leitura do buffer serial.

Figura 6: Componentes de hardware do dispositivo

Fonte: O autor



Figura 7: Dispositivo montado e caixa de proteção

Fonte: O autor


O custo total de hardware do dispositivo totalizou aproximadamente R$ 100,00 por unidade, com todos os componentes adquiridos no mercado nacional.

A comunicação MQTT sobre TLS 1.2 foi estabelecida com êxito utilizando o broker HiveMQ Cloud no plano gratuito. O certificado da Autoridade Certificadora ISRG Root X1 foi embarcado no firmware no segmento PROGMEM; porém, em razão da incompatibilidade entre a implementação mbedtls do ESP32 e a cadeia de certificados do HiveMQ Cloud descrita na Seção 2, a validação do certificado do servidor permanece desabilitada por meio de 'setInsecure()'. O tráfego é cifrado — inacessível a observadores passivos na rede —, mas a proteção contra ataques de intermediário ativo não está ativa nesta versão do firmware. A autenticação do dispositivo junto ao broker por credenciais MQTT foi validada — tentativas de conexão com credenciais incorretas foram rejeitadas pelo broker com código de retorno 4 (credenciais incorretas), e o firmware entrou corretamente em modo sem conexão nesses casos.

O controle de acesso por lista de permissões (ACL) no broker foi validado, conforme mostrado na Figura 8. O cliente do dispositivo ('esp32-device') não conseguiu assinar tópicos para os quais não tinha permissão, e o cliente do backend ('flask-subscriber') não conseguiu publicar mensagens. Cada tentativa de operação não autorizada gerou o código de retorno de acesso negado e foi registrada nos logs do broker.

Figura 8: Console do HiveMQ Cloud com conexões ativas

Fonte: O autor

A assinatura HMAC-SHA256 foi implementada no firmware utilizando a biblioteca mbedtls nativa do ESP32. O campo 'hmac' está presente em todos os payloads publicados. O campo 'nonce' é preenchido com 8 bytes (16 caracteres hexadecimais) gerados pelo gerador de números aleatórios por hardware a cada envio. A verificação do HMAC no servidor está implementada e em operação: ao receber uma mensagem, o backend extrai o campo 'signed', recomputa o HMAC esperado com a chave compartilhada e compara ao campo 'hmac' recebido por meio de comparação resistente a ataques de temporização ('hmac.compare_digest'). Mensagens com HMAC inválido são imediatamente rejeitadas e registradas no 'audit_log' como 'hmac_failed'. A deduplicação de nonces, que previne ataques de repetição utilizando a tabela 'seen_nonces', está estruturada no banco de dados mas ainda não está ativa no processamento das mensagens.

A autenticação multifator com TOTP foi validada em operação, o fluxo completo de login, mostrado nas Figuras 9 e 10, (senha + código TOTP gerado pelo Google Authenticator) foi testado com os usuários cadastrados. O código expira após 30 segundos e o parâmetro da biblioteca pyotp acomoda divergências de até ±30 segundos entre o relógio do servidor e o do dispositivo móvel. A configuração inicial do MFA, gera o QR Code para escaneamento pelo aplicativo e persiste o segredo TOTP no banco de dados para uso nas verificações subsequentes.

Figura 9: Tela de login

Fonte: O autor

Figura 10: Tela para verificação em dois fatores

Fonte: O autor

O backend Flask foi executado de forma estável em ambiente de desenvolvimento, recebendo e processando mensagens MQTT em tempo real por meio da thread subscriber em segundo plano. As APIs REST responderam corretamente às requisições do dashboard, com isolamento de dados por empresa funcionando conforme esperado: usuários de uma empresa não visualizam dados de outra empresa, conforme mostrado na Figura 11. O papel superadmin visualizou dados de ambas as empresas, conforme o comportamento definido na função 'company_where'.

Figura 11: Tela de cadastro de novo usuário

Fonte: O autor




A detecção automática de violações de temperatura foi validada com os dados reais. O endpoint '/api/alarms' retornou corretamente as leituras cujos valores de temperatura estavam fora da faixa mínima e máxima de temperatura cadastrada para o produto associado ao lote em transporte. As violações foram exibidas no painel de alertas do sistema com data e hora, lote, produto, temperatura registrada e limites violados, conforme mostrado na Figura 12.

Figura 12: Alertas de violações

Fonte: O autor


O banco de dados foi populado com os dados de demonstração gerados pelo script 'seed_demo.py'. A empresa PharmaTransport totalizou 13 produtos farmacêuticos cadastrados, 18 lotes e 15 rastreamentos, com aproximadamente 900 leituras registradas. A empresa BioFrio totalizou 12 produtos, 18 lotes e 13 rastreamentos, com aproximadamente 738 leituras. No total, o sistema concentrou 25 produtos farmacêuticos, 36 lotes, 28 rastreamentos e cerca de 1.638 leituras distribuídas entre as duas empresas, com um dispositivo ativo vinculado à empresa PharmaTransport.
O registro de auditoria foi validado em operação: todas as ações realizadas durante os testes — logins, falhas de autenticação, registros de dispositivos, criações e encerramentos de rastreamentos — foram registradas na tabela 'audit_log' com usuário, endereço IP de origem, ação e registro de data e hora. A tabela não expõe rotas de exclusão ou edição pela API, conferindo proteção contra alterações ao histórico registrado.

O gráfico de temperatura, desenvolvido com a biblioteca Chart.js, exibiu a série temporal das leituras de cada rastreamento selecionado com linha contínua, pontos de violação destacados em vermelho e linhas tracejadas indicando os limites mínimo e máximo cadastrados para o produto associado ao lote. A escala temporal é ajustada automaticamente à duração do rastreamento, permitindo a identificação visual imediata de desvios térmicos e do intervalo em que ocorreram ao longo do trajeto, conforme mostrado na Figura 13.

O mapa interativo, desenvolvido com a biblioteca Leaflet.js, renderizou corretamente as rotas a partir das coordenadas GPS registradas nas leituras, representando cada rastreamento como uma polilinha com marcador de origem em verde e marcador de posição atual em laranja. O dashboard oferece ainda um modo de visualização combinada, no qual múltiplos rastreamentos são exibidos simultaneamente com cores distintas sobre o mesmo mapa, permitindo a comparação visual entre rotas de diferentes lotes e períodos. A Figura 14 ilustra um exemplo de rota renderizada. As Figuras 15 e 16 apresentam as telas de configuração do dispositivo ESP32 e do rastreamento, respectivamente.









Figura 13: Gráfico de temperatura com indicação de violações

Fonte: O autor


Figura 14: Mapa GPS com rota do rastreamento

Fonte: O autor


Figura 15: Configuração do dispositivo ESP32

Fonte: O autor

Figura 16: Configuração do Rastreamento

Fonte: O autor

Os resultados obtidos demonstram a viabilidade da construção. O uso do broker HiveMQ Cloud no plano gratuito mostrou-se adequado para o contexto do trabalho, com suporte obrigatório a TLS e autenticação por credenciais. A limitação do plano gratuito de cem conexões simultâneas é suficiente para operações de pequeno porte, mas exigiria migração para planos pagos ou para infraestrutura própria em operações com maior volume de dispositivos simultâneos.

O mecanismo de armazenamento local temporário com SPIFFS foi validado, conforme mostrado na Figura 17, simulando a desconexão da rede WiFi durante a operação. O firmware detectou a falha de publicação MQTT, iniciou a gravação local no arquivo '/buffer.jsonl' e retomou o envio das leituras acumuladas, em ordem cronológica, após o restabelecimento da conexão. A capacidade estimada de armazenamento local, considerando o tamanho médio de cada entrada JSON (~180 bytes), é de aproximadamente 600 leituras no espaço de arquivo disponível, equivalente a cerca de 40 minutos de operação contínua sem conectividade. O temporizador de vigilância configurado para 60 segundos foi ativado em situações de bloqueio prolongado do ciclo principal de execução, com reinicialização automática e retomada correta da operação.

O armazenamento local temporário com SPIFFS atendeu ao objetivo de continuidade do registro durante períodos de desconexão. A capacidade de armazenamento de aproximadamente 600 leituras é adequada para desconexões de curta duração. Para operações em regiões com desconexões prolongadas, a capacidade poderia ser ampliada por meio de armazenamento externo (cartão microSD) ou pela redução do intervalo de coleta.

Figura 17: Armazenamento local temporário

Fonte: O autor

A deduplicação de nonces no processamento das mensagens pelo servidor constitui a principal etapa de segurança ainda não finalizada. A estrutura de banco de dados para suportar essa verificação já está implementada (tabela 'seen_nonces'), e a ativação no backend representa um incremento pontual sobre a arquitetura existente. Sua ausência não compromete as demais camadas de segurança já ativas — TLS com cifração de canal, autenticação por credenciais, verificação HMAC-SHA256 com rejeição de mensagens adulteradas, bcrypt, TOTP e RBAC —, mas deixa em aberto a proteção contra ataques de repetição de mensagens válidas, que deve ser endereçada antes da adoção em ambiente de produção.

Figura 31: Verificação das mensagens 

Fonte: O autor
















CONCLUSÃO

O presente trabalho apresentou o desenvolvimento do PharmaTrack IoT, um sistema de monitoramento contínuo para o transporte de produtos farmacêuticos termossensíveis utilizando componentes e ferramentas disponíveis no mercado nacional e de baixo custo.

O dispositivo embarcado baseado no ESP32 realiza coletas de temperatura, umidade e coordenadas GPS em ciclos de cinco segundos, com buffer offline em SPIFFS para garantir a continuidade do registro durante desconexões de rede. A transmissão ocorre via MQTT sobre TLS 1.2, com autenticação por credenciais no broker e controle de acesso por lista de permissões. Os mecanismos de segurança implementados — HMAC-SHA256 com geração de nonce por hardware, bcrypt com fator de custo 12, autenticação multifator TOTP e controle de acesso baseado em papéis — formam um conjunto de camadas independentes que endereçam as propriedades de confidencialidade, integridade e disponibilidade definidas na tríade CIA. O backend Flask com banco de dados MySQL realiza a detecção automática de violações de temperatura, o isolamento de dados por empresa e o registro de auditoria com proteção contra alterações. O dashboard web oferece visualização em tempo real com gráfico de temperatura, mapa GPS interativo e painel de alertas.

A principal contribuição do trabalho está na demonstração de que os requisitos técnicos de um sistema de monitoramento farmacêutico seguro e rastreável — habitualmente associados a soluções proprietárias de alto custo — podem ser satisfeitos com hardware de propósito geral e uma pilha de software inteiramente composta por ferramentas de código aberto. O custo baixo de hardware por dispositivo, combinado com a disponibilidade de brokers MQTT gerenciados em planos gratuitos, torna viável a adoção de monitoramento eletrônico contínuo em operações logísticas de menor escala que não dispõem de orçamento para soluções comerciais.

Como limitações do trabalho, destacam-se: a deduplicação de nonces no processamento das mensagens pelo servidor ainda não foi finalizada, deixando em aberto a proteção contra ataques de repetição de mensagens válidas; a validação do certificado do servidor no ESP32 está desabilitada por meio de 'setInsecure()' devido à incompatibilidade mbedtls com a cadeia ISRG Root X1, expondo o canal a ataques de intermediário ativo; a chave HMAC está armazenada diretamente no firmware em vez de utilizar armazenamento seguro no NVS (Non-Volatile Storage) do ESP32; e o sistema não foi submetido a testes de carga ou de penetração formais.

Como trabalhos futuros, propõem-se: a conclusão da deduplicação de nonces no backend para prevenção de ataques de repetição; a substituição de 'setInsecure()' por 'setCACert()' com a CA raiz correta, eliminando a limitação de validação do certificado no ESP32; a migração da chave HMAC para o armazenamento seguro NVS via biblioteca 'Preferences.h'; a implementação de cifração em repouso dos campos de leitura no banco de dados; a adição de geração de relatórios por rastreamento em formato PDF; a realização de testes de segurança documentados, incluindo análise de tráfego com Wireshark, simulação de ataques de repetição e testes de injeção SQL; e a avaliação do comportamento do sistema em escala com múltiplos dispositivos simultâneos.









REFERÊNCIAS 

WORLD HEALTH ORGANIZATION (WHO). WHO-IVB-15.04: Temperature sensitivity of vaccines. Geneva: WHO, 2015. Disponível em: https://www.who.int/publications/i/item/WHO-IVB-15.04. Acesso em: abr. 2026.

UNICEF. What is the cold chain? UNICEF Supply Division, 2023. Disponível em: https://www.unicef.org/supply/what-cold-chain. Acesso em: abr. 2026.

WORLD HEALTH ORGANIZATION (WHO). Immunization Agenda 2030: A Global Strategy to Leave No One Behind. Geneva: WHO, 2024. Disponível em: https://www.who.int/publications/i/item/9789240109544. Acesso em: abr. 2026.

JIANG, Shaojun; JIA, Sumei; GUO, Hongjun. Internet of Things (IoT)-enabled framework for a sustainable vaccine cold chain management system. Heliyon, v. 10, n. 7, e28910, 2024. DOI: 10.1016/j.heliyon.2024.e28910. Disponível em: https://pmc.ncbi.nlm.nih.gov/articles/PMC10998091/. Acesso em: mai. 2026.

AGÊNCIA NACIONAL DE VIGILÂNCIA SANITÁRIA (Anvisa). Resolução de Diretoria Colegiada – RDC n. 430, de 8 de outubro de 2020. Dispõe sobre as Boas Práticas de Distribuição, Armazenagem e Transporte de Medicamentos para Uso Humano. Diário Oficial da União, Brasília, DF, 9 out. 2020. Disponível em: https://www.in.gov.br/en/web/dou/-/resolucao-de-diretoria-colegiada-rdc-n-430-de-8-de-outubro-de-2020-282070593. Acesso em: abr. 2026.

NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY (NIST). NIST Special Publication 800-183: Networks of 'Things'. Gaithersburg: NIST, 2016. Disponível em: https://csrc.nist.gov/pubs/sp/800/183/final. Acesso em: abr. 2026.

STATISTA. Internet of Things (IoT) connected devices installed base worldwide from 2015 to 2025. Statista, 2025. Disponível em: https://www.statista.com/statistics/1183457/iot-connected-devices-worldwide/. Acesso em: abr. 2026.

EUROPEAN UNION AGENCY FOR CYBERSECURITY (ENISA). Threat Landscape. ENISA, 2024. Disponível em: https://www.enisa.europa.eu/topics/cyber-threats/threat-landscape. Acesso em: abr. 2026.

VAN GLABBEEK, Roald; DEAC, Diana; PERALE, Thomas; STEENHAUT, Kris; BRAEKEN, An. Flexible and efficient security framework for many-to-many communication in a publish/subscribe architecture. Sensors, Basel, v. 22, n. 19, art. 7391, 2022. DOI: 10.3390/s22197391. Disponível em: https://pmc.ncbi.nlm.nih.gov/articles/PMC9572294/. Acesso em: mai. 2026.

INTERNATIONAL ORGANIZATION FOR STANDARDIZATION (ISO). ISO/IEC 27001: Information security, cybersecurity and privacy protection — Information security management systems — Requirements. Geneva: ISO, 2022. Disponível em: https://www.iso.org/standard/27001. Acesso em: abr. 2026.

STALLINGS, William. Cryptography and Network Security: Principles and Practice. 8. ed. Hoboken: Pearson, 2022. ISBN 978-1-292-43748-4.

BAMASHMOS, Saeed; CHILAMKURTI, Naveen; SALEHI SHAHRAKI, Ahmad. Two-layered multi-factor authentication using decentralized blockchain in an IoT environment. Sensors, Basel, v. 24, n. 11, art. 3575, 2024. DOI: 10.3390/s24113575. Disponível em: https://pmc.ncbi.nlm.nih.gov/articles/PMC11175277/. Acesso em: mai. 2026.

















































































