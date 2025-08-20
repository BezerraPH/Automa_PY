# Essa é uma automação para testar a inserção e atualização de processos no sistema interno da diretoria da instituição que trabalho.
# Basicamente eu pegava todos os dados no nosso sistema interno através de SQL, exportava em CSV e depois rodava o script para atualizar o sistema da diretoria.
# Ou seja, se você não entendeu até agora, sim, aqui nós utilizamos dois sistemas para controlar a mesma informação, a diferença é que um é local (regional) e o outro nacional.

# Em resumo, a automação faz o seguinte:
# 1. Abre o navegador (Edge);
# 2. Acessa a página principal (login);
# 3. Faz o login;
# 4. Depois de logado, acessa a página de processos físicos;
# 5. Faz o filtro pelo CPF para verificar se tem algum processo cadastrado;
# 6. Se, processo cadastrado? -> verificar se o protocolo já está cadastrado, Se protocolo cadastrado -> iniciar atualização;
# 7. Senão, processo não cadastrado? -> cadastrar processo -> verificar cadastro;
# 8. Repetir o processo para todas as linhas da planilha;

# Antes que você se pergunte porque eu não fiz a filtragem/busca pelo protocolo, é porque no sistema da diretoria, eles não colocaram o protocolo como chave primária, na verdade, 
# só adicionaram o protocolo depois que eu liguei pra lá e pedi para adicionar, pois, sem chave primária, não tem como você manter a tabela atualizada de maneira correta. 
# Imagine o seguinte, uma pessoa (CPF) pode dar entrada em vários processos na mesma data, com a mesma atividade, e todas podem estar no mesmo status (em análise), 
# a chave primária da tabela processo, obviamente seria o protocolo, mas só foi adicionado depois, como um campo texto livre. então por esse motivo, arrumei esse "jeitinho" de Filtrar pelo cpf, 
# depois pesquisar pela coluna de "Comentários" pra só aí fazer a atualização/inserção do processo.
