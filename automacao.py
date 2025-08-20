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

# Imports de bibliotecas
import pandas as pd
import time
import logging
import re
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.remote.webelement import WebElement

# Imports específicos para o Edge
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions

# --- CONFIGURAÇÕES ---
URL_BASE = "http://10.0.0.0.0.0"
URL_PROCESSOS = "http://10.0.0.0.0.0"
USUARIO = "seulogin"
SENHA = "suasenha"
ARQUIVO_CSV = "nome_do_arquivo_que_vai_ser_lido.csv"
ARQUIVO_LOG = "relatorio_execucao.log"

# --- PARÂMETROS DE EXECUÇÃO ---
TEMPO_ESPERA_MAXIMO = 60
TEMPO_ESPERA_CURTO = 5
MAX_TENTATIVAS = 3
PAUSA_ENTRE_ACOES = 0.5
PAUSA_RETENTATIVA = 5

# --- MAPEAMENTO DE DADOS ---
# Tive que fazer esse tratamento pois na nossa base de dados interna consta um valor no campo da atividade e no sistema da diretoria, consta outro valor. 
# Não sei o motivo dessa divergência, orgão público é assim, tudo muito confuso e pouco coeso. Por esse motivo tive que tratar os dados.
ATIVIDADE_MAP = {
    "REVALIDAÇÃO DE CR": "Revalidação para Pessoa Física",
    "AUTORIZAÇÃO AQUISIÇÃO DE PCE USO PERMITIDO": "Autorizar Aquisição de PCE no Mercado Nacional CAC",
    "REGISTRO (CONCESSÃO) DE CR": "Concessão de Registro para Pessoa Física - CAC",
    "REVALIDAÇÃO DE REGISTRO DE ARMA DE FOGO (CRAF)": "Revalidação de Certificado de Registro de Arma de Fogo CRAF",
    "AQUISIÇÃO DE PCE POR IMPORTAÇÃO": "Autorizar Aquisição de PCE por Importação - CII",
    "TRANSFERÊNCIA DE PROPRIEDADE DE ARMA DE FOGO - CAC/CAC": "Transferir Propriedade de arma-CAC (entre CACs)",
    "APOSTILAMENTO AO CR - MUDANÇA DE NÍVEL DE ATIRADOR DESPORTIVO": "Apostilar mudança de nível de atirador desportivo",
    "AUTORIZAÇÃO PARA AQUISIÇÃO DE MUNIÇÃO/INSUMO": "Autorizar Aquisição PCE Merc Nacional- munição além previsto",
    "REGISTRO E APOSTILAMENTO DE ARMA DE FOGO - CAC": "Registro e Apostilamento de Armas de CAC",
    "TRANSFERÊNCIA DE PROPRIEDADE DE ARMA DE FOGO - SINARM/SIGMA": "Transferir Propriedade de arma para CAC ( do SINARM para o SIGMA)",
    "2ª VIA DE REGISTRO DE ARMA DE FOGO (CRAF)": "2ª Via de Certificado de Registro de Arma de Fogo (CRAF)",
    "APOSTILAMENTO AO CR - ATUALIZAÇÃO DE ENDEREÇO": "Apostilamento CR PF - Atualização de Endereço do Acervo",
    "TRANSFERÊNCIA DE PROPRIEDADE DE ARMA DE FOGO - SIGMA/SINARM": "Transferir Propriedade de arma (do CAC-SIGMA para o SINARM) ANUÊNCIA",
    "CANCELAMENTO DE REGISTRO": "Cancelamento Registro para Pessoa Física",
    "APOSTILAMENTO CR PF - ATUALIZAÇÃO DE ENDEREÇO DO ACERVO": "Apostilamento CR PF - Atualização de Endereço do Acervo",
    "CONCESSÃO DE REGISTRO PARA PESSOA FÍSICA - CAC": "Concessão de Registro para Pessoa Física - CAC",
    "TRANSFERIR PROPRIEDADE DE ARMA-CAC (ENTRE FACS)": "Transferir Propriedade de arma-CAC (entre CACs)",
    "TRANSFERIR PROPRIEDADE DE ARMA (DO CAC-SIGMA PARA O SINARM) ANUÊNCIA": "Transferir Propriedade de arma (do CAC-SIGMA para o SINARM) ANUÊNCIA",
    "TRANSFERIR PROPRIEDADE DE ARMA PARA CAC ( DO SINARM PARA O SIGMA)": "Transferir Propriedade de arma para CAC ( do SINARM para o SIGMA)",
    "Informar ocorrência com arma (Perda/furto/Roubo/ sinistro)": "Informar ocorrência com arma (Perda/furto/Roubo/ sinistro)",
    "Registro e Apostilamento de Armas de CAC": "Registro e Apostilamento de Armas de CAC",
    "Emitir Guia de Tráfego Pessoa Física CAC": "Emitir Guia de Tráfego Pessoa Física CAC",
    "Apostilamento CR PF - Atualização Tipo Atividade e Tipo PCE": "Apostilamento CR PF - Atualização Tipo Atividade e Tipo PCE",
    "Transferir Propriedade de Equipamento de Recarga/acessórios entre CAC": "Transferir Propriedade de Equipamento de Recarga/acessórios entre CAC",
    "Autorizar Aquisição de Armas de Fogo - PF": "Autorizar Aquisição de Armas de Fogo - PF",
    "Autorizar Aquisição de PCE por Importação - CII": "Autorizar Aquisição de PCE por Importação - CII"
}

#Também precisei tratar os status dos processos, esse foi mais pra alinhar as cases, na planilha as vezes estava minúsculo e no sistema da diretoria começava com maiúsculo
STATUS_MAP = {
    'em análise': 'Em Análise',
    'deferido': 'Deferido',
    'indeferido': 'Indeferido',
    'restituido': 'Restituido',
    'cancelado': 'Cancelado'
}

# --- CONFIGURAÇÃO DO LOGGING ---
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(ARQUIVO_LOG, mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

# --- FUNÇÕES AUXILIARES ---
def normalizar_texto(texto):
    return str(texto).strip().lower()

def formatar_data_para_input(data_str):
    try:
        partes = str(data_str).split('/')
        if len(partes) == 3:
            return f"{partes[2]}-{partes[1]}-{partes[0]}"
    except Exception:
        pass
    return None

def preencher_campo_data_com_js(driver: webdriver.Edge, elemento: WebElement, data_formatada: str):
    driver.execute_script("arguments[0].value = arguments[1];", elemento, data_formatada)

# --- FUNÇÕES DE INTERAÇÃO COM A PÁGINA ---

def realizar_login(driver: webdriver.Edge, wait: WebDriverWait):
    """Navega para a página de login, insere credenciais e valida o resultado."""
    logging.info("Iniciando login...")
    driver.get(URL_BASE)
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "login"))).send_keys(USUARIO)
        wait.until(EC.visibility_of_element_located((By.ID, "senha"))).send_keys(SENHA)
        wait.until(EC.element_to_be_clickable((By.ID, "submit"))).click()
        try:
            # Espera até que a URL mude para a página correta após o login.
            wait.until(EC.url_contains("area_vip.php"))
            logging.info("Login realizado com sucesso!")
        except TimeoutException:
            try:
                erro_login = driver.find_element(By.XPATH, "//*[contains(text(), 'inválido') or contains(text(), 'incorretos') or contains(@class, 'alert-danger')]")
                logging.critical(f"FALHA NO LOGIN: Mensagem de erro encontrada na página: '{erro_login.text}'. Verifique as credenciais.")
            except NoSuchElementException:
                logging.critical("FALHA NO LOGIN: A página não redirecionou para 'area_vip.php' no tempo esperado. O sistema pode estar lento, offline ou as credenciais estão incorretas.")
            raise
    except Exception as e:
        logging.critical(f"Ocorreu um erro inesperado durante a tentativa de login: {e}")
        raise

def filtrar_por_cpf(driver: webdriver.Edge, wait: WebDriverWait, cpf: str) -> int:
    """Filtra os processos na página pelo CPF e retorna a contagem de resultados."""
    logging.info(f"Filtrando por CPF: {cpf}")
    wait.until(EC.visibility_of_element_located((By.ID, "cr"))).clear()
    wait.until(EC.visibility_of_element_located((By.ID, "cr"))).send_keys(cpf)
    header_antigo = wait.until(EC.presence_of_element_located((By.XPATH, "//h4[contains(text(), 'Resultados:')]")))
    driver.find_element(By.XPATH, "//button[text()='Filtrar']").click()
    wait.until(EC.staleness_of(header_antigo))
    header_novo = wait.until(EC.presence_of_element_located((By.XPATH, "//h4[contains(text(), 'Resultados:')]")))
    resultados_match = re.search(r'(\d+)', header_novo.text)
    num_resultados = int(resultados_match.group(0)) if resultados_match else 0
    logging.info(f"Encontrados {num_resultados} resultados para o CPF.")
    return num_resultados

def buscar_linha_por_protocolo(driver: webdriver.Edge, protocolo: str) -> WebElement | None:
    """Tenta encontrar a linha (tr) na tabela que corresponde a um protocolo específico."""
    try:
        xpath_linha = f"//tr[.//input[@name='COMENTARIO' and @value=\"{protocolo}\"]]"
        return WebDriverWait(driver, TEMPO_ESPERA_CURTO).until(
            EC.presence_of_element_located((By.XPATH, xpath_linha))
        )
    except TimeoutException:
        logging.info(f"Protocolo '{protocolo}' não encontrado. Será feito um novo cadastro.")
        return None

def cadastrar_novo_processo(driver: webdriver.Edge, wait: WebDriverWait, dados: dict) -> bool:
    """Preenche e submete o formulário de um novo processo."""
    # **CORREÇÃO:** Usando a chave 'PROTOCOLO' em maiúsculo
    logging.info(f"--> Iniciando CADASTRO para o protocolo {dados['PROTOCOLO']}...")
    try:
        form_xpath = "//form[contains(@action, 'salvar_inclusao.php')]"
        form_inclusao = wait.until(EC.visibility_of_element_located((By.XPATH, form_xpath)))
        Select(form_inclusao.find_element(By.NAME, "OM")).select_by_visible_text(dados['sigla'])
        data_entrada = formatar_data_para_input(dados['DATA ENTRADA'])
        if data_entrada:
            campo_data_entrada = form_inclusao.find_element(By.NAME, "DATA_ENTRADA")
            preencher_campo_data_com_js(driver, campo_data_entrada, data_entrada)
        form_inclusao.find_element(By.NAME, "CR").send_keys(dados['cpf_formatado'])
        atividade_mapeada = ATIVIDADE_MAP.get(dados['NOVA_ATIVIDADE'].strip(), dados['NOVA_ATIVIDADE'])
        Select(form_inclusao.find_element(By.NAME, "ATIVIDADE")).select_by_visible_text(atividade_mapeada)
        status_normalizado = STATUS_MAP.get(normalizar_texto(dados['novo_status']), dados['novo_status'])
        Select(form_inclusao.find_element(By.NAME, "STATUS")).select_by_visible_text(status_normalizado)
        # **CORREÇÃO:** Usando a chave 'PROTOCOLO' em maiúsculo
        form_inclusao.find_element(By.NAME, "COMENTARIO").send_keys(dados['PROTOCOLO'])
        data_final = formatar_data_para_input(dados.get('nova_data_finalizacao'))
        if status_normalizado in ["Deferido", "Indeferido"] and data_final:
            campo_data_final = form_inclusao.find_element(By.NAME, "DATA_FINALIZACAO")
            preencher_campo_data_com_js(driver, campo_data_final, data_final)
        time.sleep(PAUSA_ENTRE_ACOES)
        form_inclusao.find_element(By.XPATH, ".//button[text()='Salvar Novo']").click()
        wait.until(EC.url_contains("index.php"))
        if filtrar_por_cpf(driver, wait, dados['cpf_formatado']) > 0:
            if buscar_linha_por_protocolo(driver, dados['PROTOCOLO']):
                logging.info(f"--> SUCESSO NO CADASTRO: Processo {dados['PROTOCOLO']} verificado.")
                return True
        logging.error(f"--> FALHA NA VERIFICAÇÃO DO CADASTRO: Processo {dados['PROTOCOLO']} não encontrado após submissão.")
        return False
    except NoSuchElementException as e:
        logging.error(f"--> ERRO DE DADOS: A atividade '{dados['NOVA_ATIVIDADE']}' não foi encontrada no formulário. Verifique o mapeamento. Detalhe: {e}")
        return False
    except Exception as e:
        logging.error(f"--> ERRO INESPERADO no cadastro do protocolo {dados['PROTOCOLO']}. Causa: {e.__class__.__name__}")
        logging.error(traceback.format_exc())
        return False

def atualizar_processo_existente(driver: webdriver.Edge, wait: WebDriverWait, linha_web: WebElement, dados: dict) -> bool:
    """Atualiza as informações de um processo existente."""
    # **CORREÇÃO:** Usando a chave 'PROTOCOLO' em maiúsculo
    logging.info(f"--> Iniciando ATUALIZAÇÃO para o protocolo {dados['PROTOCOLO']}...")
    try:
        status_normalizado = STATUS_MAP.get(normalizar_texto(dados['novo_status']), dados['novo_status'])
        Select(linha_web.find_element(By.NAME, "STATUS")).select_by_visible_text(status_normalizado)
        campo_data_final = linha_web.find_element(By.NAME, "DATA_FINALIZACAO")
        data_final = formatar_data_para_input(dados.get('nova_data_finalizacao'))
        if status_normalizado in ["Deferido", "Indeferido"] and data_final:
            preencher_campo_data_com_js(driver, campo_data_final, data_final)
        else:
            preencher_campo_data_com_js(driver, campo_data_final, "")
        time.sleep(PAUSA_ENTRE_ACOES)
        linha_web.find_element(By.XPATH, ".//button[text()='Atualizar']").click()
        wait.until(EC.staleness_of(linha_web))
        logging.info(f"--> SUCESSO NA ATUALIZAÇÃO do protocolo {dados['PROTOCOLO']}!")
        return True
    except Exception as e:
        logging.error(f"--> ERRO INESPERADO na atualização do protocolo {dados['PROTOCOLO']}. Causa: {e.__class__.__name__}")
        logging.error(traceback.format_exc())
        return False

# --- FUNÇÃO PRINCIPAL ---
def main():
    """Função principal que orquestra todo o processo de automação."""
    setup_logging()
    logging.info("="*60)
    logging.info("INICIANDO ROBÔ DE PROCESSAMENTO SGI (VERSÃO FINAL)")
    logging.info("="*60)
    
    sucessos, falhas = 0, 0
    df = None 
    driver = None
    
    try:
        edge_options = EdgeOptions()
        edge_options.add_argument("--start-maximized")
        edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        service = EdgeService(executable_path="msedgedriver.exe")
        driver = webdriver.Edge(service=service, options=edge_options)
        wait = WebDriverWait(driver, TEMPO_ESPERA_MAXIMO)

        realizar_login(driver, wait)

        driver.get(URL_PROCESSOS)
        wait.until(EC.visibility_of_element_located((By.ID, "cr")))
        logging.info("Página de processos carregada.")
        
        df = pd.read_csv(ARQUIVO_CSV, delimiter=';', encoding='utf-8-sig', dtype=str).fillna('')
        df.columns = df.columns.str.strip()
        df['cpf_formatado'] = df['CPF SOLICITANTE'].apply(lambda x: ''.join(filter(str.isdigit, str(x))))
        logging.info(f"Arquivo CSV lido. Total de {len(df)} linhas para processar.")

        for index, row in df.iterrows():
            linha_planilha = index + 2
            dados_linha = row.to_dict()
            cpf = dados_linha['cpf_formatado']
            protocolo = dados_linha.get('PROTOCOLO', '').strip()

            if not cpf or not protocolo:
                logging.warning(f"Linha {linha_planilha}: Ignorando, pois o CPF ou Protocolo está em branco.")
                continue
                
            logging.info(f"--- Processando Linha {linha_planilha}: CPF {cpf}, Protocolo '{protocolo}' ---")
            
            operacao_bem_sucedida = False
            for tentativa in range(MAX_TENTATIVAS):
                try:
                    if URL_PROCESSOS not in driver.current_url:
                        driver.get(URL_PROCESSOS)
                        wait.until(EC.visibility_of_element_located((By.ID, "cr")))
                    
                    num_resultados = filtrar_por_cpf(driver, wait, cpf)
                    
                    linha_existente = buscar_linha_por_protocolo(driver, protocolo) if num_resultados > 0 else None

                    if linha_existente:
                        operacao_bem_sucedida = atualizar_processo_existente(driver, wait, linha_existente, dados_linha)
                    else:
                        operacao_bem_sucedida = cadastrar_novo_processo(driver, wait, dados_linha)

                    if operacao_bem_sucedida:
                        break
                
                except (TimeoutException, ElementClickInterceptedException) as e:
                    logging.warning(f"Tentativa {tentativa + 1}/{MAX_TENTATIVAS} falhou para o CPF {cpf}. Causa: {e.__class__.__name__}. Tentando novamente em {PAUSA_RETENTATIVA}s.")
                    time.sleep(PAUSA_RETENTATIVA)
                    driver.refresh()
                except Exception as e:
                    logging.error(f"Erro crítico na tentativa {tentativa + 1} para o CPF {cpf}: {e}")
                    logging.error(traceback.format_exc())
                    if tentativa < MAX_TENTATIVAS - 1:
                        logging.info("Tentando recuperar navegando para a página de processos...")
                        driver.get(URL_PROCESSOS)
                        time.sleep(PAUSA_RETENTATIVA)
            
            if operacao_bem_sucedida:
                sucessos += 1
            else:
                falhas += 1
                logging.error(f"FALHA FINAL para a linha {linha_planilha} (CPF {cpf}) após {MAX_TENTATIVAS} tentativas.")

    except FileNotFoundError:
        logging.critical(f"ERRO CRÍTICO: O arquivo '{ARQUIVO_CSV}' não foi encontrado.")
    except Exception as e_geral:
        logging.critical(f"ERRO CRÍTICO que encerrou a automação: {e_geral}")
        logging.critical(traceback.format_exc())
    finally:
        total_items = len(df) if df is not None else 0
        logging.info("="*60)
        logging.info("AUTOMAÇÃO FINALIZADA")
        logging.info(f"Total de Itens da Planilha: {total_items}")
        logging.info(f"Processos com Sucesso: {sucessos}")
        logging.info(f"Processos com Falha: {falhas}")
        logging.info(f"Relatório detalhado salvo em: '{ARQUIVO_LOG}'")
        logging.info("="*60)
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
