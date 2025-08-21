

# 🤖 Automação para Inserção e Atualização de Processos

## 🎯 Visão Geral

Esta é uma automação desenvolvida para testar e realizar a inserção e atualização de processos no sistema da diretoria da instituição.

Basicamente, o fluxo de trabalho consiste em extrair dados do nosso sistema interno (regional) via SQL, exportá-los para um arquivo CSV e, em seguida, executar este script para sincronizar e atualizar as informações no sistema nacional da diretoria.

> **Nota:** Sim, utilizamos dois sistemas diferentes para controlar a mesma informação. Esta automação serve como uma ponte para manter a consistência entre a base de dados local (regional) e a nacional.

## ⚙️ Como Funciona

Em resumo, a automação executa os seguintes passos:

1.  **Abre o navegador** (Microsoft Edge).
2.  **Acessa a página** principal do sistema.
3.  **Faz o login** com as credenciais fornecidas.
4.  Após o login, navega até a página de **processos físicos**.
5.  **Filtra pelo CPF** para verificar se existe algum processo cadastrado para o indivíduo.
6.  **Se o processo for encontrado:**
    * Verifica se o **protocolo** específico já está registrado para aquele CPF.
    * Se o protocolo existir, inicia o procedimento de **atualização** do processo.
7.  **Se o processo não for encontrado:**
    * Inicia o procedimento para **cadastrar um novo processo**.
    * Após o cadastro, realiza uma verificação para confirmar a inserção.
8.  **Repete o ciclo** para todas as linhas da planilha de dados (arquivo CSV).

## 🤔 Observação Importante: A Lógica de Busca

Antes que você se pergunte por que a filtragem/busca não é feita diretamente pelo **protocolo**, há um motivo técnico importante.

No sistema da diretoria, o campo `protocolo` não foi implementado como chave primária. Na verdade, ele só foi adicionado como um campo de texto livre após uma solicitação direta, pois, sem uma chave primária, é impossível garantir a atualização correta e segura dos dados.

Imagine o seguinte cenário:
* Uma pessoa (identificada por um CPF) pode dar entrada em vários processos na mesma data.
* Esses processos podem ser para a mesma atividade.
* Todos eles podem estar no mesmo status (ex: "em análise").

Neste caso, a única forma de diferenciar um processo do outro seria através de um identificador único, que obviamente deveria ser o protocolo.

Por causa dessa limitação, foi necessário criar esta solução alternativa: filtrar primeiro pelo CPF e, em seguida, realizar uma busca na coluna de "Comentários" (ou campo similar onde o protocolo foi inserido) para só então fazer a atualização ou a inserção do processo correto.

## ⚠️ Pré-requisitos

**LEMBRE-SE DE BAIXAR O WEBDRIVER PARA O MICROSOFT EDGE**

Para que a automação possa controlar o navegador Edge, é essencial ter o driver correspondente à sua versão do navegador.

➡️ **Link para Download:** [Microsoft Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/?form=MA13LH#downloads)
