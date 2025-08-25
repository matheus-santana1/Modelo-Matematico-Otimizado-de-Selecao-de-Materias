import pandas as pd
import re
import sys

# --- Funções de Leitura e Processamento (sem alterações) ---

def parse_cplex_matrix(text_block):
    """Interpreta um bloco de texto de matriz do CPLEX."""
    cleaned_text = re.sub(r'[\[\]]', '', text_block).strip()
    lines = cleaned_text.split('\n')
    matrix = []
    for line in lines:
        if not line.strip(): continue
        row = [float(num) for num in line.strip().split()]
        matrix.append(row)
    return matrix

def read_cplex_output_file(filepath):
    """Lê o arquivo de saída do CPLEX e o divide em blocos para cada variável."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"ERRO: O arquivo de entrada '{filepath}' não foi encontrado.")
        sys.exit(1)
    variable_blocks = re.findall(r'(\w+)\s*=\s*(.*?);', content, re.DOTALL)
    return {name: block for name, block in variable_blocks}

# --- Função Principal (com as novas funcionalidades) ---

def main():
    """Orquestra a leitura, processamento, cálculo e exportação."""
    # --- PARÂMETROS DE ENTRADA E DADOS ---
    input_filename = 'solucao.txt'
    output_filename = 'relatorio_completo_blendagem.xlsx'
    
    materias_primas = [
        "Areia", "Bauxita", "Braunita", "Brucita", "Calcita", "Corindon", 
        "Dolomita", "Goethita", "Hematita", "Itabirito", "Magnesita", 
        "Magnetita", "Pirolusita", "Quartzo", "Rhodocrosita"
    ]
    
    elementos = ["SiO2", "CaO", "MgO", "Fe", "Al2O3", "Mn"]

    # Tabela de Composição Química (do artigo)
    composicao_quimica = pd.DataFrame([
        [95, 1, 1, 1, 1, 0], [10, 0, 0, 5, 50, 0], [11, 0, 0, 0, 0, 60],
        [0, 0, 69, 0, 0, 0], [5, 50, 5, 0, 0, 0], [0, 0, 0, 0, 99, 0],
        [0, 0, 30, 0, 22, 0], [0, 0, 0, 63, 0, 0], [0, 0, 0, 70, 0, 0],
        [10, 0, 5, 60, 5, 0], [0, 0, 48, 0, 0, 0], [0, 0, 0, 72, 0, 0],
        [0, 0, 0, 0, 0, 63], [99, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 47]
    ], index=materias_primas, columns=elementos) / 100.0 # Converte para decimal

    # --- LEITURA E PROCESSAMENTO DA SOLUÇÃO 'x' ---
    print(f"Lendo o arquivo de solução '{input_filename}'...")
    cplex_data = read_cplex_output_file(input_filename)

    if 'x' not in cplex_data:
        print(f"ERRO: A variável 'x' não foi encontrada no arquivo '{input_filename}'.")
        sys.exit(1)

    x_matrix = parse_cplex_matrix(cplex_data['x'])
    
    num_pacotes = len(x_matrix[0]) if x_matrix else 0
    colunas_pacotes = [f'Pacote {i+1}' for i in range(num_pacotes)]

    # DataFrame com a "receita" de matérias-primas
    df_receita = pd.DataFrame(x_matrix, columns=colunas_pacotes, index=materias_primas)

    # --- CÁLCULO DA TABELA DE ANÁLISE DE QUALIDADE ---
    print("Calculando concentrações e desvio padrão...")
    
    pesos_pacotes = df_receita.sum(axis=0)
    
    # Matriz de quantidade de cada elemento (kg) em cada pacote
    qtde_elementos_kg = composicao_quimica.T.dot(df_receita)
    
    # Matriz de concentração percentual (%) de cada elemento em cada pacote
    conc_percentual = (qtde_elementos_kg / pesos_pacotes) * 100
    
    # Calcula as estatísticas (Média, Variância e Desvio Padrão)
    # ddof=0 para calcular a variância/desvio padrão populacional (como VAR.P/STDEV.P do Excel)
    media = conc_percentual.mean(axis=1)
    variancia = conc_percentual.var(axis=1, ddof=0)
    desvio_padrao = conc_percentual.std(axis=1, ddof=0)
    
    # Cria o DataFrame final da análise
    df_analise = pd.DataFrame({
        'Média (%)': media,
        'Variância (VAR.P)': variancia,
        'Desvio Padrão (DP %)': desvio_padrao
    })
    
    # Adiciona as concentrações de cada pacote para visualização completa
    df_analise = pd.concat([conc_percentual, df_analise], axis=1)

    # --- PREPARAÇÃO FINAL DOS DATAFRAMES ---
    df_receita.loc['Peso Total do Pacote'] = pesos_pacotes
    df_receita = df_receita.round(2)
    df_analise = df_analise.round(4) # Maior precisão para a análise

    # --- EXPORTAÇÃO PARA UM ÚNICO ARQUIVO EXCEL COM DUAS ABAS ---
    try:
        print(f"\nGerando relatório completo '{output_filename}'...")
        with pd.ExcelWriter(output_filename) as writer:
            df_receita.to_excel(writer, sheet_name='Receita por Pacote')
            df_analise.to_excel(writer, sheet_name='Análise de Qualidade')
        
        print("Relatório gerado com sucesso!")
        print("\nPré-visualização da Receita:")
        print(df_receita)
        print("\nPré-visualização da Análise de Qualidade:")
        print(df_analise)

    except Exception as e:
        print(f"\nERRO: Não foi possível salvar a planilha. Causa: {e}")

if __name__ == "__main__":
    main()
