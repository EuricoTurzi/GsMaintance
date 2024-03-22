from app import app
from app.functions import *
import os
from flask import render_template, request, send_file, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from datetime import datetime

MOTIVOS = {
    "manutencao": "Manutenção",
    "devolucao_estoque": "Devolução/Estoque"
}

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Função para carregar o usuário
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Classe User para o Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_login(username, password):
            user = User(username)
            login_user(user)
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('login'))

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    success_message = False
    if request.method == 'POST':
        # Verifica se o formulário de nova manutenção foi submetido
        if 'username' in request.form:
            # Se o campo 'username' está presente no formulário
            username = request.form['username']
            password = request.form['password']
            # Aqui você pode fazer o processamento do login
        
        protocolo = generate_maintenance_number()
        
        data = {
            "protocolo": protocolo,
            "dateTime": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "ids": request.form['ids'],
            "nomeCliente": request.form['nomeCliente'],
            "motivo": MOTIVOS.get(request.form['selected_option_text'], ""),  # Obtendo o texto completo
            "modelo": request.form['modelo'],
            "customizacao": request.form['customizacao'],
            "tipoProblema": request.form['tipoProblema'],
            "photos": request.files.getlist('photos'),
            "tratativa": request.form['tratativa'],
        }

        save_to_excel(data)
        
        if generate_maintenance_pdf(data):
            success_message = "Sua solicitação de manutenção foi enviada com sucesso."
        return render_template('index.html', success_message=success_message)
    else:
        return render_template('index.html', success_message=None)

@app.route('/visualizar_manutencoes', methods=['GET', 'POST'])
@login_required
def visualizar_manutencoes():
    if request.method == 'POST':
        protocolo = request.form['protocolo']
        status = request.form['status']
        update_manutencao(protocolo, status)
        return redirect(url_for('visualizar_manutencoes'))
    
    manutencoes = get_manutencoes()
    return render_template('visualizar_manutencoes.html', manutencoes=manutencoes)

@app.route('/aprovar_manutencao/<protocolo>', methods=['POST'])
@login_required
def aprovar_manutencao(protocolo):
    # Obter o endereço de e-mail associado à manutenção
    email = "dixil78713@fryshare.com"

    # Obter o nome do cliente do formulário (ou ajustar conforme necessário)
    cliente = request.form.get('cliente', 'Cliente Desconhecido')

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
    send_email_with_attachment(email, new_pdf_path)
    
    # Alterar o status da manutenção para "Aprovada"
    update_manutencao(protocolo, "Aprovada")
    
    # Verificar os valores de protocolo e cliente antes de chamar a função
    print("Protocolo:", protocolo)
    print("Cliente:", cliente)
    
    adicionar_data_aprovacao_excel(protocolo, cliente)

    manutencoes = get_manutencoes()
    return render_template('visualizar_manutencoes.html', manutencoes=manutencoes)

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
    
@app.errorhandler(401)
def unauthorized(error):
    return render_template('error.html'), 401