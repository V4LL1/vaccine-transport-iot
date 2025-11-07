**Metodologia**



A metodologia deste trabalho será estruturada de forma a descrever o processo de concepção, desenvolvimento e validação de um sistema de Internet das Coisas (IoT) voltado para o monitoramento seguro do transporte de vacinas. O sistema será projetado com base em uma arquitetura distribuída que integra hardware, software e protocolos de comunicação para garantir a coleta, transmissão, armazenamento e análise de dados sensíveis em tempo real. Para isso, será desenvolvido um protótipo composto por um microcontrolador ESP32, sensores DHT22 para medição de temperatura e umidade, módulo GPS para rastreamento de localização, além de um sistema de alimentação híbrido baseado em fonte de energia e bateria, assegurando a operação contínua durante o deslocamento. A comunicação entre o dispositivo e o servidor será realizada por meio do protocolo MQTT, enquanto os dados coletados serão armazenados em um banco de dados relacional para posterior análise e visualização.



A estrutura metodológica seguirá os princípios fundamentais de um sistema IoT, sendo organizada de acordo com os quatro pilares que o sustentam: Percepção, Conectividade, Análise e Ação. Essa divisão permitirá compreender, de forma sistemática, como cada etapa contribui para o funcionamento e a segurança do sistema. Assim, as subseções seguintes detalharão o papel de cada pilar dentro do contexto do projeto, abordando desde a captação dos dados ambientais até as respostas automáticas e os mecanismos de controle que asseguram a integridade, autenticidade e disponibilidade das informações monitoradas durante o transporte das vacinas.



O pilar da Percepção representa a camada responsável pela aquisição de dados do ambiente físico, sendo o ponto de partida de todo o sistema IoT. Nesta etapa, o sistema será projetado para coletar informações críticas relacionadas às condições de transporte das vacinas, como temperatura, umidade e localização geográfica. O núcleo dessa camada será o microcontrolador ESP32, escolhido por sua alta integração de recursos e suporte a conectividade sem fio, atuando como unidade de controle e processamento local. O sensor DHT22 será utilizado para realizar as medições de temperatura e umidade com precisão adequada ao contexto biomédico, enquanto o módulo GPS NEO-6M será responsável por fornecer as coordenadas geográficas em tempo real, permitindo o rastreamento contínuo da câmara térmica durante o deslocamento.



A arquitetura física dessa camada compreenderá a integração direta dos sensores e módulos ao ESP32 por meio de interfaces digitais e seriais, garantindo baixo consumo energético e comunicação eficiente. O sistema contará ainda com uma fonte de alimentação híbrida, composta por fonte de energia externa e bateria recarregável, assegurando a continuidade da operação mesmo em situações de falha elétrica. Os dados capturados serão periodicamente processados e preparados para transmissão, incluindo metadados como timestamp e identificadores únicos, de modo a possibilitar a rastreabilidade e integridade das leituras. Embora o foco principal desta etapa seja a coleta e organização dos dados brutos, serão aplicadas técnicas básicas de filtragem e validação local, reduzindo ruídos e garantindo a qualidade das informações antes do envio ao servidor central.

