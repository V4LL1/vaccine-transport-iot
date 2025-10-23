**Metodologia**



A metodologia proposta para o desenvolvimento do sistema IoT seguro para monitoramento, controle e rastreamento de transporte de vacinas será estruturada em etapas que permitem planejar e organizar a execução do projeto no TCC2. Inicialmente, será realizado um levantamento detalhado dos requisitos do sistema, considerando aspectos críticos como o monitoramento de temperatura e umidade, rastreabilidade por GPS, controle de dispositivos de refrigeração, registro de identificadores únicos de lote e tokens de entrega, além de critérios de segurança da informação e continuidade operacional. Essa etapa permitirá definir as especificações técnicas do protótipo e os objetivos de desempenho e segurança a serem atingidos.



Na fase seguinte, será feita a seleção de hardware e software, priorizando componentes compatíveis com IoT, como microcontroladores ESP32, sensores ambientais, módulo GPS e relés, além de tecnologias de comunicação seguras, como MQTT sobre TLS. Também será definida a arquitetura do sistema, com divisão modular das responsabilidades entre o dispositivo IoT, o broker MQTT e o dashboard web, garantindo escalabilidade, manutenção simplificada e implementação de medidas de segurança em camadas.



O desenvolvimento do protótipo incluirá a implementação de mecanismos de segurança, como criptografia ponta a ponta, assinatura digital de mensagens, proteção contra replay attacks, autenticação multifator e controle de acesso baseado em papéis. Serão planejados testes de funcionalidade e segurança para validar a precisão das medições, o correto funcionamento do controle de refrigeração, a integridade e confidencialidade dos dados transmitidos e a resiliência do sistema frente a falhas ou ataques.

