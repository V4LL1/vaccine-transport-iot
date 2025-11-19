METODOLOGIA

A metodologia deste trabalho será estruturada de forma a descrever o processo de concepção, desenvolvimento e validação de um sistema de Internet das Coisas (IoT) voltado para o monitoramento seguro do transporte de vacinas. O sistema será projetado com base em uma arquitetura distribuída que integra hardware, software e protocolos de comunicação para garantir a coleta, transmissão, armazenamento e análise de dados sensíveis em tempo real. Para isso, será desenvolvido um protótipo composto por um microcontrolador ESP32, sensores DHT22 para medição de temperatura e umidade, módulo GPS para rastreamento de localização, além de um sistema de alimentação híbrido baseado em fonte de energia e bateria, assegurando a operação contínua durante o deslocamento. A comunicação entre o dispositivo e o servidor será realizada por meio do protocolo MQTT, enquanto os dados coletados serão armazenados em um banco de dados relacional para posterior análise e visualização.

A estrutura metodológica seguirá os princípios fundamentais de um sistema IoT, sendo organizada de acordo com os quatro pilares que o sustentam: Percepção, Conectividade, Análise e Ação. Essa divisão permitirá compreender, de forma sistemática, como cada etapa contribui para o funcionamento e a segurança do sistema. Assim, as subseções seguintes detalharão o papel de cada pilar dentro do contexto do projeto, abordando desde a captação dos dados ambientais até os processos que asseguram a integridade, autenticidade e disponibilidade das informações monitoradas durante o transporte das vacinas.

O pilar da Percepção constitui a base fundamental do sistema IoT proposto, responsável por coletar, quantificar e pré-processar os dados provenientes do ambiente físico, transformando variáveis analógicas em informações digitais significativas que serão utilizadas nas etapas posteriores. No contexto deste trabalho, essa camada será responsável por monitorar temperatura, umidade e localização geográfica durante o transporte de vacinas, permitindo rastreabilidade contínua e avaliação das condições ambientais ao longo do deslocamento.

O sistema será implementado com base no microcontrolador ESP32, que foi selecionado por oferecer um conjunto robusto de recursos para aplicações IoT, como conectividade Wi-Fi e Bluetooth integradas, processador dual-core de 32 bits e suporte a múltiplas interfaces de comunicação digital. O ESP32 atuará como unidade central de aquisição e coordenação, gerenciando a leitura dos sensores, o pré-processamento dos dados e a transmissão ao servidor via MQTT.

Para o monitoramento ambiental, será utilizado o sensor DHT22, responsável por medir temperatura e umidade com resolução de 0,1°C e 0,1% de umidade relativa. A comunicação entre o DHT22 e o ESP32 ocorrerá por um barramento digital único, com taxa de amostragem entre 2 e 5 segundos. O firmware aplicará rotinas de filtragem, como média móvel e validação de limites, reduzindo ruídos e possibilitando a detecção inicial de leituras anômalas.

Para rastreamento geográfico será utilizado o módulo GPS NEO-6M, que se comunica com o ESP32 via UART. Os dados de localização serão agregados às medições ambientais e estruturados em mensagens padronizadas, facilitando sua interoperabilidade com o broker MQTT e o banco de dados.

O sistema de alimentação utilizará redundância energética, combinando uma fonte regulada de 5 V e uma bateria Li-ion 18650 gerenciada por módulo TP4056, assegurando operação contínua durante interrupções externas. Essa redundância é essencial para sistemas críticos e contribui diretamente para disponibilidade, um dos requisitos centrais do monitoramento de vacinas \[8].



Figura 1: Coleta de dados pelos sensores e GPS no dispositivo IoT



Fonte: O autor













O Pilar da Conectividade é responsável por garantir a transmissão confiável e segura dos dados coletados até a infraestrutura de processamento. Em sistemas sensíveis como o transporte de vacinas, a comunicação deve priorizar segurança, disponibilidade e tolerância a falhas.

Neste projeto, a conectividade será implementada por meio do protocolo MQTT sobre TLS, assegurando confidencialidade, integridade e autenticação mútua entre o dispositivo e o servidor central. O MQTT, por ser leve e baseado no padrão publish/subscribe, é amplamente recomendado para IoT, especialmente em contextos com restrições de energia e banda, conforme discutido em BANKS et al. \[9].

O ESP32 atuará como cliente MQTT, publicando periodicamente mensagens em tópicos predefinidos (/vacina/temperatura, /vacina/umidade, /vacina/localizacao e /vacina/status). O broker, hospedado em servidor seguro, empregará autenticação baseada em certificados X.509, reforçando a proteção contra ataques de impersonação e interceptação, conforme destacado por García-Murillo et al. \[10].

Para aumentar a resiliência da comunicação, o sistema utilizará QoS 1, garantindo entrega ao menos uma vez, além de mecanismos automáticos de reconexão e failover para um broker secundário caso o principal se torne indisponível. Esses mecanismos atendem às recomendações para sistemas distribuídos tolerantes a falhas em ambientes IoT críticos.

Adicionalmente, mensagens transmitidas incluirão assinaturas HMAC-SHA256, timestamps e nonces, prevenindo ataques de repetição e adulteração. Em caso de perda temporária de conectividade, o ESP32 armazenará leituras em buffer local, retransmitindo-as assim que a conexão for reestabelecida.



Figura 2: Transmissão segura das informações via MQTT com TLS



Fonte: O autor

O Pilar da Análise é responsável pelo processamento, validação, armazenamento e interpretação dos dados recebidos, transformando medições brutas em informações relevantes para auditoria, rastreabilidade e avaliação de conformidade. Esse pilar garante que os dados de temperatura, umidade e localização sejam avaliados continuamente segundo normas sanitárias e diretrizes de transporte de insumos termossensíveis (ANVISA, 2020; WHO, 2023) \[11]\[12].

Os dados recebidos do broker MQTT serão encaminhados a um servidor de aplicação que realizará validação de integridade (HMAC/SHA256), registro de logs e persistência em banco de dados MySQL. A escolha do MySQL se justifica pela robustez, integridade transacional e aderência a ambientes industriais e acadêmicos (SILVA et al., 2022) \[13].

O banco de dados será estruturado com tabelas específicas para leituras ambientais, localização, eventos, usuários e dispositivos IoT, permitindo rastreabilidade completa do histórico de transporte. Um módulo de auditoria registrará eventos críticos, como falhas de autenticação, desconexões inesperadas e variações abruptas de leitura, apoiando investigações forenses e atendendo às exigências de compliance (ISO/IEC 27001) \[14].

Uma interface de visualização (dashboard) permitirá acompanhamento em tempo real de dados ambientais e trajetos, além de emissão de alertas em caso de violações de parâmetros críticos. O dashboard implementará autenticação RBAC, assegurando níveis de acesso distintos conforme o perfil do usuário.

Para garantir continuidade operacional, serão implementadas rotinas automáticas de backup criptografado e replicação assíncrona para servidor secundário, alinhadas às recomendações de continuidade de negócios e recuperação de desastres descritas no NIST SP 800-34 \[15].

Figura 3: Processamento e visualização dos dados no servidor e dashboard



Fonte: O autor

O Pilar da Ação abrange os mecanismos que garantem a continuidade do funcionamento seguro do sistema, a preservação do fluxo de dados e a supervisão operacional durante o transporte de vacinas. Embora o sistema não execute ações sobre o ambiente físico, este pilar assegura que o processo de monitoramento permaneça ativo mesmo sob condições adversas, preservando integridade e rastreabilidade.

Um dos elementos essenciais neste pilar é a redundância energética: o ESP32 realiza monitoramento contínuo da alimentação e, em caso de falha da fonte principal, migra automaticamente para a bateria sem interromper seu funcionamento. Essa estratégia segue boas práticas de resiliência operacional recomendadas pelo NIST \[15].



Outro componente importante é o mecanismo de reconexão e sincronização. Quando ocorre perda momentânea de conectividade, o ESP32 registra leituras na memória não volátil (SPIFFS/EEPROM). Após o restabelecimento da conexão, as mensagens pendentes são retransmitidas com controle de integridade baseado em timestamps e identificadores únicos, evitando duplicações e garantindo ordenação, conforme diretrizes do NIST SP 800-183 \[16].

O dashboard também desempenha papel relevante neste pilar, oferecendo supervisão, registro de incidentes, visualização de rotas e geração de relatórios. Esses elementos contribuem para rastreabilidade e conformidade com RDC nº 430/2020 e normas GDP de cadeia fria \[17].

As comunicações entre broker, servidor e dashboard utilizarão TLS 1.3, reforçando a segurança dos dados em trânsito. Além disso, mecanismos de backup criptografado, failover e verificação pós-recuperação garantirão integridade e continuidade mesmo em caso de falhas severas ou ataques de negação de serviço.





\[8] Rao, A. et al. IoT Power Systems for Critical Monitoring. IEEE, 2021.

\[9] Banks, A. et al. MQTT – The Standard for IoT Messaging. OASIS, 2022.

\[10] García-Murillo, M. et al. Secure MQTT Architectures with X.509 Authentication. Sensors, 2021.

\[11] ANVISA. Boas Práticas de Distribuição e Armazenamento. RDC 430/2020.

\[12] WHO. Guidelines on the International Packaging and Shipping of Vaccines. WHO Press, 2023.

\[13] Silva, T. et al. MySQL in Industrial IoT Architectures. Journal of Systems Engineering, 2022.

\[14] ISO/IEC 27001. Information Security Management Systems. ISO, 2022.

\[15] NIST. Contingency Planning Guide for Federal Information Systems. SP 800-34, 2023.

\[16] NIST. Network-of-Things Framework. SP 800-183, 2020.

\[17] GDP. Good Distribution Practices for Temperature-Sensitive Products. 2023.

