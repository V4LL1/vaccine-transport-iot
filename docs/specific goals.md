1. Desenvolver um sistema IoT seguro baseado em ESP32 capaz de medir temperatura, umidade, localização e confirmação de recebimento das câmaras de transporte de vacinas, enviando essas informações ao servidor via MQTT e gerando sinais digitais para que sistemas externos possam tomar ações corretivas quando necessário.
   
2. Implementar comunicação segura entre o protótipo e o servidor utilizando MQTT sobre TLS com autenticação mútua e certificados X.509, assegurando a confidencialidade, integridade e proteção de dados críticos em trânsito.
   
3. Aplicar um conjunto integrado de medidas de segurança no sistema, incluindo controle de acesso baseado em papéis (RBAC) e autenticação multifator (MFA) para o dashboard e interfaces de controle, rotação periódica de chaves e certificados X.509 e criptografia de dados sensíveis, abrangendo informações de temperatura, umidade, localização e status das câmaras.
   
4. Implementar estratégias de continuidade e recuperação (BCP/DRP) integradas ao sistema, incluindo failover do broker MQTT para garantir disponibilidade em casos de falhas ou ataques DDoS, backups automáticos criptografados dos registros do sistema e procedimentos de restauração de dados críticos.
   
5. Assegurar redundância de alimentação para que o protótipo continue operando durante quedas de energia ou falhas elétricas, garantindo a continuidade do monitoramento e da comunicação.
   
6. Realizar testes de segurança e resiliência, incluindo sniffing, ataques MITM, DDoS e tentativas de acesso não autorizado, comparando resultados antes e depois da aplicação das medidas de segurança e continuidade.
   
7. Construir um dashboard seguro e funcional para visualização em tempo real das métricas operacionais, como temperatura, umidade, localização, confirmação de recebimento, alarmes e indicadores de continuidade (uptime, tempo de recuperação e perda de dados tolerada).
   
8. Avaliar o impacto das medidas integradas de segurança e continuidade — incluindo redundância de alimentação — na confidencialidade, integridade, disponibilidade e confiabilidade geral do sistema IoT proposto.
