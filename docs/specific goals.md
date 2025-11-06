1. Arquitetar e desenvolver um sistema IoT seguro, capaz de medir temperatura, umidade, localização e confirmação de recebimento das câmaras de transporte de vacinas, enviando periodicamente essas informações a um servidor via protocolo MQTT.
   
2. Aplicar um conjunto integrado de medidas de segurança para proteger a comunicação, autenticação e integridade dos dados no sistema IoT, incluindo:



* Implementação de comunicação segura MQTT sobre TLS com autenticação mútua entre o protótipo e o servidor, garantindo confidencialidade, integridade e autenticação das partes envolvidas;



* Uso de assinatura digital (HMAC/SHA256) e inclusão de timestamp e nonce em cada mensagem para mitigar ataques de replay;



* Aplicação de controle de acesso baseado em papéis (RBAC) e autenticação multifator (MFA) no dashboard e nas interfaces de controle;



* Rotação periódica de chaves e certificados X.509, minimizando riscos de credenciais comprometidas;



* Criptografia de dados em repouso, abrangendo informações sobre temperatura, umidade, localização e status das câmaras;



* Hardening do broker MQTT, com autenticação forte, controle de ACLs e desativação de protocolos inseguros.





3\. Integrar estratégias de continuidade e recuperação (BCP/DRP) que assegurem a operação e a disponibilidade do sistema, incluindo:



* Failover do broker MQTT para garantir funcionamento mesmo em falhas de servidor ou ataques DDoS;



* Backups automáticos criptografados dos registros e logs do sistema;



* Procedimentos automáticos de restauração de dados e reconexão após falhas;



* Redundância de alimentação, garantindo que o protótipo continue operando durante quedas de energia;





4\. Realizar testes de segurança e resiliência, incluindo sniffing, MITM, DDoS e tentativas de acesso não autorizado, comparando resultados antes e depois da aplicação das medidas de segurança e continuidade.



5\. Construir um dashboard seguro para visualização em tempo real de métricas operacionais, como temperatura, umidade, localização, alarmes e indicadores de continuidade (uptime, tempo de recuperação e perda de dados tolerada).

