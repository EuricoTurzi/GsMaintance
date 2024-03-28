from app import app
from app.functions import *
import os
from flask import render_template, request, send_file, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

MOTIVOS = {
    "manutencao": "Manutenção",
    "devolucao_estoque": "Devolução/Estoque"
}

FATURAMENTO = {
    "com_custo": "Com custo",
    "sem_custo": "Sem custo",
}

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Função para carregar o usuário
@login_manager.user_loader
def load_user(user_id):
    # Aqui você precisa obter o access_level associado ao user_id
    access_level = get_access_level_by_id(user_id)
    return User(user_id, access_level)

# Classe User para o Flask-Login
class User(UserMixin):
    def __init__(self, id, access_level):
        self.id = id
        self.access_level = access_level

    def get_access_level(self):
        return self.access_level
        
# Rota de login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        success, access_level = check_login(username, password)
        if success:
            user = User(username, access_level)
            login_user(user)
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    return render_template('login.html')

# Rota de Logout
@app.route('/logout')
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('login'))

# Rota da página de requisição
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    user_access_level = current_user.get_access_level()
    success_message = False
    if request.method == 'POST':
        
        protocolo = generate_maintenance_number()
        
        data = {
            "protocolo": protocolo,
            "dateTime": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "ids": request.form['ids'],
            "nomeCliente": request.form['nomeCliente'],
            "motivo": MOTIVOS.get(request.form['selected_option_text'], ""),  # Obtendo o texto completo
            "faturamento": FATURAMENTO.get(request.form['faturamento_option_text'], ""),
            "modelo": request.form['modelo'],
            "customizacao": request.form['customizacao'],
            "tipoProblema": request.form['tipoProblema'],
            "photos": request.files.getlist('photos'),
            "tratativa": request.form['tratativa'],
        }

        save_to_excel(data)
        
        if generate_maintenance_pdf(data):
            success_message = "Sua solicitação de manutenção foi enviada com sucesso."
        return render_template('index.html', success_message=success_message, user_access_level=user_access_level)
    else:
        return render_template('index.html', success_message=None, user_access_level=user_access_level)

# Rota da página de visualização
@app.route('/visualizar_manutencoes', methods=['GET', 'POST'])
@login_required
def visualizar_manutencoes():
    user_access_level = current_user.get_access_level()
    
    if request.method == 'POST':
        protocolo = request.form['protocolo']
        status = request.form['status']
        update_manutencao(protocolo, status)
        return redirect(url_for('visualizar_manutencoes'))
    
    manutencoes = get_manutencoes()
    return render_template('visualizar_manutencoes.html', manutencoes=manutencoes, user_access_level=user_access_level)

# Rota para aprovar manutenção
@app.route('/aprovar_manutencao/<protocolo>', methods=['POST'])
@login_required
def aprovar_manutencao(protocolo):
    user_access_level = current_user.get_access_level()
        
    # Obter o nome do cliente do formulário (ou ajustar conforme necessário)
    cliente = request.form.get('cliente', 'Cliente Desconhecido')
    faturamento = faturamento = get_faturamento_from_protocolo(protocolo)
    
    # Verificar se a ação é Aprovar ou Enviar para a Diretoria
    acao = request.form.get('acao')

    if acao == 'aprovar':
        
        # Gerar o nome do arquivo PDF da manutenção aprovada
        pdf_filename = f"{protocolo} - {cliente}.pdf"
        pdf_path = os.path.join(app.root_path, "static", "protocolos", f"{protocolo} - {cliente}.pdf")

        # Verificar se o arquivo PDF existe
        if not os.path.isfile(pdf_path):
            return f"Erro: O arquivo PDF não foi encontrado no caminho: {pdf_path}", 404

        # Renomear o arquivo para o novo nome desejado
        new_pdf_path = os.path.join(app.root_path, "static", "protocolos", pdf_filename)
        os.rename(pdf_path, new_pdf_path)

        # Envio do e-mail com o PDF anexado
        email = "dixil78713@fryshare.com"
        enviar_email_aprovacao(email, new_pdf_path)
        
        # Alterar o status da manutenção para "Aprovada"
        update_manutencao(protocolo, "Aprovada")
        
        adicionar_data_aprovacao_excel(protocolo, cliente)
        
    elif acao == 'enviar_diretoria':
        # Adicionar a manutenção à planilha da Diretoria
        adicionar_manutencao_diretoria(protocolo, cliente, faturamento)

        # Alterar o status da manutenção para "Enviado à Diretoria"
        update_manutencao(protocolo, "Enviado à Diretoria")

    # Redirecionar de volta para a página de visualizar manutenções após o processamento
    return redirect(url_for('visualizar_manutencoes', user_access_level=user_access_level))
        
# Rota para download dos protocolos
@app.route('/download_protocolo', methods=['POST'])
@login_required
def download_protocolo():
    data = request.json
    protocolo = data.get('protocolo')
    cliente = data.get('cliente')
    
    pdf_filename = f"{protocolo} - {cliente}.pdf"
    pdf_path = os.path.join(app.root_path, "static", "protocolos", pdf_filename)

    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
    else:
        return jsonify({'error': 'Arquivo não encontrado'}), 404
    
# Rota para filtro de manutenções    
@app.route('/search_maintenance', methods=['GET'])
def search_maintenance():
    search_query = request.args.get('search')
    
    if search_query:
        df = pd.read_excel('db/registros_manutencao.xlsx')
        results = df[df.apply(lambda row: search_query.lower() in row['Nome do Cliente'].lower() or 
                                         search_query.lower() in str(row['Protocolo']).lower(), axis=1)]
        maintenances = results.to_dict('records')
        
        return render_template('visualizar_manutencoes.html', maintenances=maintenances)
    
    df = pd.read_excel('db/registros_manutencao.xlsx')
    maintenances = df.to_dict('records')
    return render_template('visualizar_manutencoes.html', maintenances=maintenances)

# Rota para envio à diretoria
@app.route('/enviar_diretoria/<protocolo>', methods=['POST'])
@login_required
def enviar_diretoria(protocolo):
    user_access_level = current_user.get_access_level()
    # Obter o nome do cliente do formulário (ou ajustar conforme necessário)
    cliente = request.form.get('cliente', 'Cliente Desconhecido')

    # Obter o faturamento do protocolo
    faturamento = get_faturamento_from_protocolo(protocolo)

    # Alterar o status da manutenção para "Enviado à Diretoria"
    update_manutencao(protocolo, "Enviado à Diretoria")

    # Adicionar a nova linha ao arquivo da Diretoria
    adicionar_manutencao_diretoria(protocolo, cliente, faturamento)

    return redirect(url_for('visualizar_manutencoes', user_access_level=user_access_level))

# Rota para enviar à diretoria
@app.route('/aprovar_enviar_diretoria/<protocolo>', methods=['POST'])
@login_required
def aprovar_enviar_diretoria(protocolo):
    user_access_level = current_user.get_access_level()
    acao = request.form['acao']
    faturamento = request.form.get('faturamento')

    if acao == "Aprovar":
        # Chamar a função para aprovar a manutenção
        aprovar_manutencao(protocolo)
    elif acao == "EnviarDiretoria":
        # Chamar a função para enviar a manutenção à Diretoria
        enviar_diretoria(protocolo, faturamento)

    return redirect(url_for('visualizar_manutencoes', user_access_level=user_access_level))

# Rota para visualizar as manutenções da Diretoria
@app.route('/visualizar_diretoria', methods=['GET'])
@login_required
def visualizar_diretoria():
    user_access_level = current_user.get_access_level()
    
    if user_access_level < 2:
    # Redireciona o usuário para outra página ou mostra uma mensagem de erro
        return redirect(url_for('home'))
    
    df_diretoria = pd.read_excel('db/diretoria.xlsx')
    manutencoes_diretoria = df_diretoria.to_dict('records')
    return render_template('visualizar_diretoria.html', manutencoes_diretoria=manutencoes_diretoria, user_access_level=user_access_level)

# Rota para aprovar ou rejeitar uma manutenção na Diretoria
@app.route('/aprovar_diretoria/<protocolo>', methods=['POST'])
@login_required
def aprovar_diretoria(protocolo):
    user_access_level = current_user.get_access_level()
    acao = request.form.get('acao')

    if acao == 'aprovar':
        # Chama a função para registrar a aprovação antes de atualizar o status
        adicionar_data_aprovacao_diretoria(protocolo)

        # Ler o arquivo da Diretoria
        arquivo_excel_diretoria = 'db/diretoria.xlsx'
        df_diretoria = pd.read_excel(arquivo_excel_diretoria)

        # Encontrar a linha com o protocolo correspondente
        df_manutencao = df_diretoria[df_diretoria['Protocolo'] == int(protocolo)]

        if not df_manutencao.empty:
            # Atualizar o status para "Aprovada"
            df_diretoria.loc[df_diretoria['Protocolo'] == int(protocolo), 'Status'] = 'Aprovada'

            # Salvar de volta para o arquivo Excel
            df_diretoria.to_excel(arquivo_excel_diretoria, index=False)

        return redirect(url_for('visualizar_diretoria', user_access_level=user_access_level))
    
    elif acao == 'rejeitar':
        # Chama a função para registrar a aprovação antes de atualizar o status
        adicionar_data_aprovacao_diretoria(protocolo)

        # Ler o arquivo da Diretoria
        arquivo_excel_diretoria = 'db/diretoria.xlsx'
        df_diretoria = pd.read_excel(arquivo_excel_diretoria)

        # Encontrar a linha com o protocolo correspondente
        df_manutencao = df_diretoria[df_diretoria['Protocolo'] == int(protocolo)]

        if not df_manutencao.empty:
            # Atualizar o status para "Rejeitada"
            df_diretoria.loc[df_diretoria['Protocolo'] == int(protocolo), 'Status'] = 'Rejeitada'

            # Salvar de volta para o arquivo Excel
            df_diretoria.to_excel(arquivo_excel_diretoria, index=False)

        return redirect(url_for('visualizar_diretoria', user_access_level=user_access_level))

MOTIVOS1 = {
    "manutencao": "Manutenção",
    "devolucao_estoque": "Devolução/Estoque"
}

FATURAMENTO1 = {
    "com_custo": "Com custo",
    "sem_custo": "Sem custo",
}

# Rota da página de requisição
@app.route('/requisicoes', methods=['GET', 'POST'])
@login_required
def requisicoes():
    user_access_level = current_user.get_access_level()
    if request.method == 'POST':
        
        protocolo = generate_requisicao_number()
        
        data = {
            "protocolo": protocolo,
            "dateTime": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "nomeCliente": request.form['nomeCliente'],
            "motivo": MOTIVOS1.get(request.form['motivo'], ""),
            "faturamento": FATURAMENTO1.get(request.form['faturamento'], ""),
            "modelo": request.form['modelo'],
            "customizacao": request.form['customizacao'],
            "tipoProblema": request.form['tipoProblema'],
            "photos": request.files.getlist('photos'),
            "tratativa": request.form['tratativa'],
        }

        save_requisicao_to_excel(data)
        
        if generate_requisicao_pdf(data):
            success_message = "Sua requisição foi enviada com sucesso."
            return render_template('requisicoes.html', success_message=success_message, user_access_level=user_access_level)
        else:
            error_message = "Erro ao gerar o PDF da requisição."
            return render_template('requisicoes.html', error_message=error_message, user_access_level=user_access_level)
    else:
        return render_template('requisicoes.html', success_message=None, user_access_level=user_access_level)

# Rota da página de visualização das requisições
@app.route('/visualizar_requisicoes', methods=['GET', 'POST'])
@login_required
def visualizar_requisicoes():
    user_access_level = current_user.get_access_level()
    
    if request.method == 'POST':
        protocolo = request.form['protocolo']
        status = request.form['status']
        update_requisicao(protocolo, status)
        return redirect(url_for('visualizar_requisicoes', user_access_level=user_access_level))
    
    requisicoes = get_requisicoes()
    return render_template('visualizar_requisicoes.html', requisicoes=requisicoes, user_access_level=user_access_level)

# Rota para aprovar ou rejeitar uma requisição
@app.route('/aprovar_requisicao/<protocolo>', methods=['POST'])
@login_required
def aprovar_requisicao(protocolo):
    user_access_level = current_user.get_access_level()
    
    acao = request.form['acao']

    if acao == 'aprovar':
        update_requisicao(protocolo, "Aprovada")
    elif acao == 'rejeitar':
        update_requisicao(protocolo, "Rejeitada")

    return redirect(url_for('visualizar_requisicoes', user_access_level=user_access_level))

# Rota para download do PDF da requisição
@app.route('/download_requisicao', methods=['POST'])
@login_required
def download_requisicao():
    data = request.json
    protocolo = data.get('protocolo')
    cliente = data.get('cliente')
    
    pdf_filename = f"{protocolo} - {cliente}.pdf"
    pdf_path = os.path.join(app.root_path, "static", "requisicoes", pdf_filename)

    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
    else:
        return jsonify({'error': 'Arquivo não encontrado'}), 404

# Rota para filtro de requisições
@app.route('/search_requisicoes', methods=['GET'])
def search_requisicoes():
    search_query = request.args.get('search')
    
    if search_query:
        df = pd.read_excel('db/registros_requisicoes.xlsx')
        results = df[df.apply(lambda row: search_query.lower() in row['Nome do Cliente'].lower() or 
                                         search_query.lower() in str(row['Protocolo']).lower(), axis=1)]
        requisicoes = results.to_dict('records')
        
        return render_template('visualizar_requisicoes.html', requisicoes=requisicoes)
    
    df = pd.read_excel('db/registros_requisicoes.xlsx')
    requisicoes = df.to_dict('records')
    return render_template('visualizar_requisicoes.html', requisicoes=requisicoes)

# Rota para verificar a atualização do Excel
@app.route('/verificar_atualizacao_excel', methods=['GET'])
def verificar_atualizacao_excel():
    try:
        # Caminho para o arquivo Excel
        excel_file = 'db/registros_manutencao.xlsx'
        
        # Verificar se o arquivo ainda não existe ou está vazio
        if not os.path.exists(excel_file):
            return "0"  # Retornar 0 se o arquivo não existe
        
        # Ler o arquivo Excel
        registros = pd.read_excel(excel_file)
        
        # Obter o número de linhas no arquivo Excel
        num_linhas = len(registros)
        
        # Retornar o número de linhas como uma string
        return str(num_linhas)
    
    except Exception as e:
        return str(e)

# Rota para erro de login    
@app.errorhandler(401)
def unauthorized(error):
    return render_template('error.html'), 401