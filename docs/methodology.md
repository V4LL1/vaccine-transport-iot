**Metodologia**



A metodologia deste trabalho será estruturada de forma a descrever o processo de concepção, desenvolvimento e validação de um sistema de Internet das Coisas (IoT) voltado para o monitoramento seguro do transporte de vacinas. O sistema será projetado com base em uma arquitetura distribuída que integra hardware, software e protocolos de comunicação para garantir a coleta, transmissão, armazenamento e análise de dados sensíveis em tempo real. Para isso, será desenvolvido um protótipo composto por um microcontrolador ESP32, sensores DHT22 para medição de temperatura e umidade, módulo GPS para rastreamento de localização, além de um sistema de alimentação híbrido baseado em fonte de energia e bateria, assegurando a operação contínua durante o deslocamento. A comunicação entre o dispositivo e o servidor será realizada por meio do protocolo MQTT, enquanto os dados coletados serão armazenados em um banco de dados relacional para posterior análise e visualização.



A estrutura metodológica seguirá os princípios fundamentais de um sistema IoT, sendo organizada de acordo com os quatro pilares que o sustentam: Percepção, Conectividade, Análise e Ação. Essa divisão permitirá compreender, de forma sistemática, como cada etapa contribui para o funcionamento e a segurança do sistema. Assim, as subseções seguintes detalharão o papel de cada pilar dentro do contexto do projeto, abordando desde a captação dos dados ambientais até as respostas automáticas e os mecanismos de controle que asseguram a integridade, autenticidade e disponibilidade das informações monitoradas durante o transporte das vacinas.



O pilar da **Percepção** constitui a base fundamental do sistema IoT proposto, responsável por coletar, quantificar e pré-processar os dados provenientes do ambiente físico, transformando variáveis analógicas em informações digitais significativas que serão utilizadas nas etapas posteriores de análise e tomada de decisão. No contexto deste trabalho, essa camada será responsável por monitorar temperatura, umidade e localização geográfica durante o transporte de vacinas, garantindo que as condições ambientais se mantenham dentro de limites seguros e rastreáveis em tempo real.



O sistema será implementado com base no microcontrolador ESP32, que foi selecionado por oferecer um conjunto robusto de recursos de hardware e software voltados à Internet das Coisas, como conectividade Wi-Fi e Bluetooth integradas, processador dual-core de 32 bits, e suporte a múltiplas interfaces de comunicação digital (UART, I²C, SPI, ADC e PWM). O ESP32 atuará como unidade central de controle e aquisição, gerenciando a leitura dos sensores, o pré-processamento dos dados e a posterior transmissão ao servidor via protocolo MQTT.



Para o monitoramento ambiental, será utilizado o sensor DHT22, responsável por medir temperatura e umidade com resolução de 0,1°C e 0,1% de umidade relativa. A comunicação entre o DHT22 e o ESP32 ocorrerá através de um barramento digital de dados único (one-wire), utilizando uma taxa de amostragem configurada entre 2 e 5 segundos. A implementação no firmware do ESP32 incluirá rotinas de calibração e filtragem simples, como média móvel e validação de intervalos aceitáveis, a fim de reduzir ruídos e detectar anomalias de leitura.



Para o rastreamento da localização das câmaras térmicas, será empregado o módulo GPS NEO-6M, que utiliza o protocolo UART (Universal Asynchronous Receiver/Transmitter) para comunicação com o microcontrolador. O firmware será programado para interpretar sentenças NMEA (National Marine Electronics Association), extraindo parâmetros como latitude, longitude, velocidade e horário UTC. Esses dados serão agregados às medições ambientais e encapsulados em uma estrutura de mensagem padronizada em formato JSON, facilitando a interoperabilidade com o broker MQTT e o banco de dados central.



A alimentação elétrica do sistema será projetada com redundância, utilizando uma fonte de 5V CC regulada como principal e uma bateria Li-ion 18650 acoplada a um módulo de gerenciamento de carga (TP4056) como contingência. Essa solução garantirá a continuidade operacional durante quedas de energia ou falhas na rede elétrica, contribuindo para a resiliência do sistema, aspecto essencial para o transporte contínuo de vacinas. Além disso, o firmware implementará uma lógica de gerenciamento energético dinâmico, ajustando o ciclo de leitura e transmissão conforme o nível de carga da bateria e o estado de conectividade.



Os dados coletados pela camada de percepção serão então temporariamente armazenados na memória flash interna do ESP32, utilizando uma fila circular (ring buffer) para garantir que nenhuma leitura seja perdida em caso de falhas momentâneas na rede. Cada registro conterá um identificador único (UUID), timestamp sincronizado com o RTC do módulo GPS, e uma assinatura HMAC-SHA256 gerada localmente para assegurar a integridade da mensagem antes da transmissão.



O Pilar da **Conectividade** é o elo essencial entre o ambiente físico e o ambiente digital, sendo responsável por garantir a transmissão confiável, segura e contínua dos dados coletados pela camada de percepção até a infraestrutura de processamento e armazenamento. Em sistemas IoT críticos, como o proposto para o monitoramento do transporte de vacinas, a conectividade deve ser projetada com foco em segurança, disponibilidade e tolerância a falhas, considerando que interrupções na comunicação podem comprometer a rastreabilidade e a integridade das informações.



Neste projeto, a conectividade será implementada por meio do protocolo MQTT (Message Queuing Telemetry Transport) operando sobre TLS (Transport Layer Security), o que garantirá confidencialidade, integridade e autenticação mútua entre o protótipo e o servidor central. O MQTT foi escolhido por ser um protocolo leve, baseado em publicações e assinaturas (publish/subscribe), altamente eficiente para dispositivos embarcados com recursos limitados e ambientes com largura de banda reduzida (BANKS et al., 2022).



A comunicação será estruturada de forma hierárquica: o ESP32 atuará como cliente MQTT, publicando periodicamente mensagens em tópicos predefinidos — como /vacina/temperatura, /vacina/umidade, /vacina/localizacao e /vacina/status — enquanto o broker MQTT, hospedado em um servidor seguro, gerenciará a distribuição das mensagens aos assinantes autorizados. O broker será configurado com autenticação baseada em certificados X.509, exigindo a apresentação de credenciais válidas tanto do cliente (ESP32) quanto do servidor, assegurando assim autenticação mútua e proteção contra ataques de impersonação e “man-in-the-middle” (GARCÍA-MURILLO et al., 2021).



Para mitigar falhas de comunicação e ataques de negação de serviço (DDoS), o sistema contará com mecanismos de reconexão automática e failover, permitindo que o ESP32 se conecte a um broker secundário em caso de indisponibilidade do principal. Adicionalmente, será configurada uma política de QoS (Quality of Service) do tipo QoS 1, que garante a entrega da mensagem ao menos uma vez, mantendo o equilíbrio entre confiabilidade e eficiência energética.



Do ponto de vista da infraestrutura, o servidor MQTT será implementado em uma instância virtual Linux, com o serviço Mosquitto ou EMQX, ambos amplamente utilizados em ambientes industriais e acadêmicos. Esse servidor será protegido por firewalls de camada de aplicação, listas de controle de acesso (ACLs) e monitoramento contínuo de tráfego para detectar padrões anômalos. O tráfego MQTT será encapsulado dentro de uma VPN (Virtual Private Network) quando trafegar entre redes externas, reforçando a confidencialidade e o isolamento do canal de comunicação.



Além da segurança em trânsito, a camada de conectividade implementará assinaturas digitais (HMAC-SHA256) em cada mensagem transmitida, combinadas a timestamps e nonces, prevenindo ataques de repetição (replay attacks) e adulteração. Caso uma perda momentânea de conexão ocorra, o ESP32 armazenará os dados localmente em buffer e tentará retransmiti-los quando a conectividade for restabelecida, evitando perda de amostras críticas.



O Pilar da **Análise** representa a camada responsável por processar, armazenar e interpretar os dados coletados pelos sensores, transformando-os em informações úteis para a tomada de decisão e resposta operacional. Em um sistema IoT crítico, como o proposto para o transporte de vacinas, essa etapa é fundamental para garantir que as variáveis monitoradas — como temperatura, umidade e localização geográfica — sejam continuamente avaliadas quanto à conformidade com os limites estabelecidos pelas normas sanitárias (ANVISA, 2020; WHO, 2023).



Nesta fase, os dados recebidos do broker MQTT serão encaminhados para um servidor de aplicação que atuará como intermediário entre o dispositivo embarcado e a base de dados. Esse servidor será responsável por validar a integridade das mensagens (verificação HMAC/SHA256), registrar logs de auditoria e realizar a persistência das informações em um banco de dados relacional MySQL. A escolha do MySQL justifica-se pela sua robustez, suporte a transações, integridade referencial e compatibilidade com sistemas analíticos, além de permitir futuras expansões para arquiteturas distribuídas ou replicadas (SILVA et al., 2022).



O banco de dados será estruturado com tabelas dedicadas às entidades principais do sistema, como Leituras Ambientais, Localização, Eventos do Sistema, Usuários e Dispositivos IoT, cada uma com chaves primárias e estrangeiras que permitam a rastreabilidade completa das informações. Os dados de sensores (temperatura e umidade) incluirão metadados temporais e identificadores únicos do dispositivo, permitindo a reconstrução do histórico de transporte de cada câmara térmica.



Uma camada de análise será implementada no servidor, responsável por processar os dados em tempo quase real. Essa camada aplicará verificações de conformidade (por exemplo, temperatura fora da faixa de +2 °C a +8 °C) e cálculos estatísticos para identificar padrões ou anomalias operacionais, como flutuações abruptas de temperatura, perda de sinal GPS ou falhas de transmissão. Esses algoritmos poderão ser desenvolvidos em Python, utilizando bibliotecas como Pandas e NumPy, integradas ao servidor via API REST.



Para aprimorar a detecção de incidentes e a rastreabilidade, será implementado um módulo de auditoria, que armazenará eventos críticos como desconexões inesperadas, tentativas de autenticação malsucedidas e divergências de dados. Esse registro será fundamental para análises forenses em caso de suspeita de violação de integridade ou falha operacional, atendendo às exigências de compliance com normas de boas práticas de distribuição (GDP) e de segurança da informação (ISO/IEC 27001).



Além disso, será desenvolvida uma interface de visualização (dashboard) que permitirá ao usuário autorizado acompanhar em tempo real as medições e alertas do sistema. O dashboard exibirá gráficos de temperatura e umidade, rotas percorridas (via integração com APIs de mapas) e notificações automáticas em caso de violação de parâmetros críticos. A autenticação no dashboard seguirá o modelo RBAC (Role-Based Access Control), garantindo diferentes níveis de acesso conforme o perfil do usuário (por exemplo, técnico, gestor, auditor).



Por fim, visando resiliência e continuidade operacional, o sistema contará com rotinas automáticas de backup criptografado dos dados, além de um mecanismo de replicação assíncrona para um servidor secundário, permitindo a recuperação rápida em caso de falhas ou ataques de negação de serviço. Essa camada de redundância é parte integrante das práticas de Business Continuity Planning (BCP) e Disaster Recovery Planning (DRP) recomendadas por normas internacionais (NIST SP 800-34, 2023).



O Pilar da **Ação** constitui a camada responsável por executar as respostas e intervenções derivadas da análise dos dados coletados, fechando o ciclo de funcionamento do sistema IoT. Nesta etapa, o sistema não apenas identifica condições anômalas, mas também atua de forma proativa ou reativa, garantindo que a integridade das vacinas seja mantida e que a operação do transporte continue de forma segura, mesmo em situações de falha ou contingência.



No contexto deste projeto, o pilar da Ação estará centrado na integração entre o servidor de análise, o dashboard e o protótipo físico, permitindo que decisões automatizadas ou manuais possam ser executadas com base em critérios previamente definidos. Embora o foco principal do sistema seja o monitoramento e rastreabilidade, algumas ações corretivas automáticas poderão ser implementadas localmente no protótipo, reduzindo a dependência de conectividade constante.



Entre essas ações, destaca-se o acionamento de mecanismos de contingência de energia. O protótipo contará com uma fonte de alimentação híbrida (fonte principal e bateria de backup), que será gerenciada pelo firmware embarcado no ESP32. Esse microcontrolador, ao detectar falhas de energia na fonte principal, comutará automaticamente para o modo de operação com bateria, mantendo o envio periódico dos dados essenciais (temperatura, umidade e localização) por meio do módulo de comunicação celular. Essa funcionalidade será implementada utilizando sensores de tensão e rotinas de detecção no código-fonte do dispositivo, garantindo alta disponibilidade e continuidade operacional, conforme boas práticas de Disaster Recovery Planning (DRP) (NIST, 2023).



Outro componente essencial do pilar da Ação é o mecanismo de reconexão segura e sincronização de dados. Caso o sistema identifique uma interrupção temporária na conectividade MQTT, o firmware do ESP32 armazenará localmente os dados em memória não volátil (SPIFFS ou EEPROM) e, ao restabelecer a conexão, realizará a retransmissão autenticada das informações pendentes. Esse processo utilizará timestamps e identificadores únicos de mensagem (message ID) para evitar duplicações e manter a integridade temporal do histórico de transporte. Essa abordagem está alinhada às recomendações de resiliência de comunicação para IoT definidas pelo NIST SP 800-183 (2020).



Além das respostas automáticas no dispositivo, o dashboard seguro fornecerá mecanismos de ação remota e supervisão humana. Usuários com permissões específicas (definidas via RBAC) poderão acionar notificações, registrar incidentes operacionais e gerar relatórios de conformidade diretamente pela interface web. Embora o sistema não inclua envio de comandos diretos ao protótipo (por motivos de segurança e escopo), a camada de ação humana continuará desempenhando um papel fundamental na gestão de eventos críticos, como falhas de comunicação, temperatura fora dos limites ou alertas de integridade do sistema.



Do ponto de vista técnico, as ações de software e hardware serão coordenadas de forma segura, utilizando protocolos autenticados e criptografados (TLS 1.3 no MQTT) e implementando mecanismos de auditoria que registram todas as decisões e respostas executadas. Esses registros serão armazenados no banco de dados e vinculados às leituras de sensores correspondentes, permitindo rastreabilidade completa durante auditorias ou análises pós-incidente, em conformidade com as exigências da RDC nº 430/2020 da ANVISA e das diretrizes da Good Distribution Practice (GDP, 2023).



Por fim, o pilar da Ação também contempla os planos de continuidade e recuperação (BCP/DRP), assegurando que, em caso de falhas graves — como indisponibilidade do broker MQTT, interrupção prolongada de energia ou perda de conectividade — o sistema seja capaz de restaurar suas operações sem perda significativa de dados. Para isso, serão utilizados backups automáticos criptografados, failover do broker MQTT e rotinas de verificação de integridade pós-recuperação, garantindo a resiliência global do sistema frente a incidentes cibernéticos e falhas físicas.



