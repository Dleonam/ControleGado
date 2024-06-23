import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
import sqlite3
from openpyxl import Workbook

# Conexão com o banco de dados SQLite
conn = sqlite3.connect('controle_gado.db')
cursor = conn.cursor()

# Criar a tabela se não existir (com o novo campo 'atualizacao_peso')
cursor.execute('''
CREATE TABLE IF NOT EXISTS ControleGado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_animal TEXT NOT NULL,
    lote TEXT NOT NULL,
    data_entrada TEXT NOT NULL,
    peso REAL NOT NULL,
    custo_inicial REAL DEFAULT 0,
    atualizacao_peso REAL DEFAULT 0
)
''')
conn.commit()

# Função para formatar a data conforme o usuário digita
def format_date(event):
    current_text = event.widget.get()
    numbers = ''.join([c for c in current_text if c.isdigit()])

    formatted_date = ''
    if len(numbers) >= 2:
        formatted_date = numbers[:2]
    if len(numbers) >= 4:
        formatted_date += '/' + numbers[2:4]
    if len(numbers) >= 6:
        formatted_date += '/' + numbers[4:8]

    event.widget.delete(0, tk.END)
    event.widget.insert(0, formatted_date)

# Função para inserir dados no banco de dados
def inserir_dados():
    codigo_animal = entry_codigo_animal.get().strip()
    lote = entry_lote.get().strip()
    data_entrada_str = entry_data_entrada.get().strip()
    peso_str = entry_peso.get().strip()
    custo_inicial_str = entry_custo_inicial.get().strip()
    atualizacao_peso_str = entry_atualizacao_peso.get().strip()

    if not codigo_animal or not lote or not data_entrada_str:
        messagebox.showerror("Erro", "Todos os campos são obrigatórios.")
        return

    try:
        # Validar e converter a data de entrada
        data_entrada = datetime.strptime(data_entrada_str, '%d/%m/%Y')
        
        # Validar e converter peso, custo inicial e atualizacao_peso (se necessário)
        peso = float(peso_str.replace(',', '.')) if peso_str else 0.0  
        custo_inicial = float(custo_inicial_str.replace(',', '.')) if custo_inicial_str else 0.0
        atualizacao_peso = float(atualizacao_peso_str.replace(',', '.')) if atualizacao_peso_str else None

        # Verificar se já existe um registro para o código de animal e lote
        cursor.execute("SELECT id FROM ControleGado WHERE codigo_animal = ? AND lote = ? AND data_entrada = ?", (codigo_animal, lote, data_entrada_str))
        registro_existente = cursor.fetchone()

        if registro_existente:
            # Registro existente, mostrar mensagem e não permitir a inserção
            messagebox.showerror("Erro", f"Já existe um registro para o animal {codigo_animal} no lote {lote} com a data {data_entrada}.")
            return

        # Inserir o novo registro
        cursor.execute("INSERT INTO ControleGado (codigo_animal, lote, data_entrada, peso, custo_inicial, atualizacao_peso) VALUES (?, ?, ?, ?, ?, ?)",
                       (codigo_animal, lote, data_entrada_str, peso, custo_inicial, atualizacao_peso))
        conn.commit()
        messagebox.showinfo("Sucesso", "Dados inseridos com sucesso!")
        limpar_campos()

    except ValueError:
        messagebox.showerror("Erro", "Formato de data inválido. Use o formato dd/mm/aaaa.")
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao inserir dados: {str(e)}")

# Função para buscar registros por código animal e/ou número de lote
def buscar_registros():
    codigo_animal = entry_busca_codigo.get().strip()
    lote = entry_busca_lote.get().strip()

    try:
        # Montar a consulta SQL baseada nos campos preenchidos
        if codigo_animal and lote:
            cursor.execute("SELECT codigo_animal, lote, data_entrada, peso, custo_inicial, atualizacao_peso FROM ControleGado WHERE codigo_animal = ? AND lote = ?", (codigo_animal, lote))
        elif codigo_animal:
            cursor.execute("SELECT codigo_animal, lote, data_entrada, peso, custo_inicial, atualizacao_peso FROM ControleGado WHERE codigo_animal = ?", (codigo_animal,))
        elif lote:
            cursor.execute("SELECT codigo_animal, lote, data_entrada, peso, custo_inicial, atualizacao_peso FROM ControleGado WHERE lote = ?", (lote,))
        else:
            messagebox.showerror("Erro", "Por favor, insira um código de animal ou número de lote.")
            return
        
        registros = cursor.fetchall()

        if registros:
            exibir_relatorio(registros, "Registros filtrados")
        else:
            messagebox.showinfo("Informação", "Nenhum registro encontrado com os critérios especificados.")

    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao buscar dados: {str(e)}")

# Função para exibir o relatório em uma nova janela
def exibir_relatorio(registros, titulo):
    janela_relatorio = tk.Toplevel()
    janela_relatorio.title(titulo)

    # Criar Treeview para exibir resultados em formato tabular
    tree = ttk.Treeview(janela_relatorio, columns=("Código Animal", "Lote", "Data", "Peso", "Custo Inicial", "Atualização de Peso"), show="headings")
    tree.heading("Código Animal", text="Código Animal")
    tree.heading("Lote", text="Lote")
    tree.heading("Data", text="Data")
    tree.heading("Peso", text="Peso")
    tree.heading("Custo Inicial", text="Custo Inicial")
    tree.heading("Atualização de Peso", text="Atualização de Peso")

    # Inserir dados na Treeview
    for registro in registros:
        # Verifica se o valor de atualizacao_peso é None
        if registro[5] is None:
            registro_completo = registro[:5] + ("",)
        else:
            registro_completo = registro
        
        tree.insert("", tk.END, values=registro_completo)

    # Ajustar largura das colunas
    tree.column("Código Animal", width=100, anchor=tk.CENTER)
    tree.column("Lote", width=100, anchor=tk.CENTER)
    tree.column("Data", width=120, anchor=tk.CENTER)
    tree.column("Peso", width=80, anchor=tk.CENTER)
    tree.column("Custo Inicial", width=100, anchor=tk.CENTER)
    tree.column("Atualização de Peso", width=120, anchor=tk.CENTER)

    tree.pack(expand=True, fill=tk.BOTH)

    # Botão para exportar para Excel
    btn_exportar_excel = tk.Button(janela_relatorio, text="Exportar para Excel", command=lambda: exportar_para_excel(registros))
    btn_exportar_excel.pack(pady=10)

# Função para exportar relatório para Excel
def exportar_para_excel(registros):
    # Abrir janela de seleção de arquivo para salvar o relatório
    file_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[("Arquivo Excel", "*.xlsx")])

    if file_path:
        try:
            # Criar um novo Workbook e selecionar a planilha ativa
            wb = Workbook()
            ws = wb.active

            # Escrever cabeçalho
            ws.append(["Código Animal", "Lote", "Data", "Peso", "Custo Inicial", "Atualização de Peso"])

            # Escrever registros
            for registro in registros:
                # Verifica se o valor de atualizacao_peso é None
                if registro[5] is None:
                    registro_completo = registro[:5] + ("",)
                else:
                    registro_completo = registro
                
                ws.append(registro_completo)

            # Salvar o arquivo
            wb.save(file_path)
            messagebox.showinfo("Sucesso", f"Relatório exportado com sucesso para:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar relatório: {str(e)}")

# Função para limpar os campos após inserção
def limpar_campos():
    entry_codigo_animal.delete(0, tk.END)
    entry_lote.delete(0, tk.END)
    entry_data_entrada.delete(0, tk.END)
    entry_peso.delete(0, tk.END)
    entry_custo_inicial.delete(0, tk.END)
    entry_atualizacao_peso.delete(0, tk.END)

    # Habilitar edição de peso e custo inicial
    entry_peso.config(state=tk.NORMAL)
    entry_custo_inicial.config(state=tk.NORMAL)
    entry_atualizacao_peso.config(state=tk.DISABLED)

## Função para verificar e desabilitar campos se existir registro prévio para o animal e lote
def verificar_registro_anterior(event=None):
    codigo_animal = entry_codigo_animal.get().strip()
    lote = entry_lote.get().strip()

    if codigo_animal and lote:
        cursor.execute("SELECT id FROM ControleGado WHERE codigo_animal = ? AND lote = ?", (codigo_animal, lote))
        registro_existente = cursor.fetchone()

        if registro_existente:
            # Desabilitar edição de peso e custo inicial
            entry_peso.delete(0, tk.END)
            entry_custo_inicial.delete(0, tk.END)
            entry_peso.config(state=tk.DISABLED)
            entry_custo_inicial.config(state=tk.DISABLED)
            entry_atualizacao_peso.config(state=tk.NORMAL)
        else:
            # Habilitar edição de peso e custo inicial
            entry_peso.config(state=tk.NORMAL)
            entry_custo_inicial.config(state=tk.NORMAL)
            entry_atualizacao_peso.config(state=tk.DISABLED)
    else:
        # Caso algum dos campos esteja vazio, manter todos os campos editáveis
        entry_peso.config(state=tk.NORMAL)
        entry_custo_inicial.config(state=tk.NORMAL)
        entry_atualizacao_peso.config(state=tk.DISABLED)
        
# Configuração da interface gráfica
root = tk.Tk()
root.title("Controle de Gado")

# Labels e Entradas para cada campo de inserção
tk.Label(root, text="Código Animal:").grid(row=0, column=0)
entry_codigo_animal = tk.Entry(root)
entry_codigo_animal.grid(row=0, column=1, padx=10)
entry_codigo_animal.bind('<FocusOut>', verificar_registro_anterior)  # Chama a função ao sair do campo

tk.Label(root, text="Lote:").grid(row=1, column=0)
entry_lote = tk.Entry(root)
entry_lote.grid(row=1, column=1, padx=10)
entry_lote.bind('<FocusOut>', verificar_registro_anterior)  # Chama a função ao sair do campo

tk.Label(root, text="Data(dd/mm/aaaa):").grid(row=2, column=0)
entry_data_entrada = tk.Entry(root)
entry_data_entrada.grid(row=2, column=1, padx=10)
entry_data_entrada.bind('<KeyRelease>', format_date)

tk.Label(root, text="Atualização de Peso (kg):").grid(row=3, column=0)
entry_atualizacao_peso = tk.Entry(root)
entry_atualizacao_peso.grid(row=3, column=1, padx=10)

tk.Label(root, text="Peso (kg):").grid(row=4, column=0)
entry_peso = tk.Entry(root)
entry_peso.grid(row=4, column=1, padx=10)

tk.Label(root, text="Custo Inicial:").grid(row=5, column=0)
entry_custo_inicial = tk.Entry(root)
entry_custo_inicial.grid(row=5, column=1, padx=10)

# Botão para inserir dados
btn_inserir = tk.Button(root, text="Inserir Dados", command=inserir_dados)
btn_inserir.grid(row=6, column=0, columnspan=2, pady=10)

# Separador
ttk.Separator(root, orient=tk.HORIZONTAL).grid(row=7, columnspan=2, sticky='ew', pady=10)

# Frame para a busca por código de animal e lote
frame_busca = tk.LabelFrame(root, text="Buscar por Código de Animal e Lote")
frame_busca.grid(row=8, column=0, columnspan=2, padx=10, pady=5, sticky='ew')

tk.Label(frame_busca, text="Código Animal:").grid(row=0, column=0)
entry_busca_codigo = tk.Entry(frame_busca)
entry_busca_codigo.grid(row=0, column=1, padx=10)

tk.Label(frame_busca, text="Lote:").grid(row=0, column=2)
entry_busca_lote = tk.Entry(frame_busca)
entry_busca_lote.grid(row=0, column=3, padx=10)

btn_buscar = tk.Button(frame_busca, text="Buscar", command=buscar_registros)
btn_buscar.grid(row=0, column=4, padx=10)

# Configuração da largura das colunas na interface principal
root.grid_columnconfigure(1, weight=1)

# Função principal para iniciar a aplicação
def main():
    root.mainloop()

if __name__ == "__main__":
    main()

