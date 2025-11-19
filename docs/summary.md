**RESUMO**

Neste trabalho apresenta-se o desenvolvimento de um sistema IoT seguro destinado à gestão do transporte de vacinas, motivado pela necessidade de garantir condições ambientais adequadas, rastreabilidade contínua e proteção dos dados envolvidos nesse processo crítico. A metodologia prevê a construção de um protótipo baseado em ESP32, responsável por coletar temperatura, umidade e localização por meio do sensor DHT22 e de um módulo GPS, estruturado segundo os pilares de Percepção, Conectividade, Análise e Ação, e integrando comunicação via MQTT com aplicação de autenticação mútua, TLS, HMAC-SHA256, controle de acesso, criptografia e hardening do broker. Os procedimentos metodológicos incluem ainda a implementação de mecanismos de continuidade e recuperação, como failover do broker, redundância de energia, backups criptografados e reconexão automática, além da execução de testes de segurança e resiliência, incluindo sniffing, MITM, DDoS e tentativas de acesso não autorizado, para comparar o comportamento do sistema antes e depois das medidas de proteção. Espera-se como resultado a validação da arquitetura proposta, demonstrando maior integridade, disponibilidade e confiabilidade na transmissão e armazenamento dos dados, bem como a eficácia operacional de um dashboard seguro para monitoramento em tempo real. Conclui-se que a aplicação integrada de IoT e práticas robustas de cibersegurança pode elevar substancialmente o nível de proteção e rastreabilidade do transporte de vacinas, contribuindo para maior segurança sanitária e conformidade regulatória.





Palavras-chave: IoT; transporte de vacinas; cibersegurança; MQTT; ESP32; continuidade de negócios.

