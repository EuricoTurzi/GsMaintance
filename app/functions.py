import os
from app import app
from io import BytesIO
from flask_mail import Mail, Message
from flask_login import current_user
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from flask import jsonify
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image, Table, TableStyle
from reportlab.pdfgen import canvas
from datetime import datetime
import pandas as pd

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configurações para o Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'sysggoldensat@gmail.com'
app.config['MAIL_PASSWORD'] = 'yzxs ieko subp xesu'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mail = Mail(app)

# Caminho para o arquivo Excel de banco de dados
excel_file = 'db/registros_manutencao.xlsx'
requisicao_file = 'db/registros_requisicoes.xlsx'

MOTIVOS = {
    "manutencao": "Manutenção",
    "devolucao_estoque": "Devolução/Estoque"
}

# Função para verificar o login
def check_login(username, password):
    logins_df = pd.read_excel('db/logins.xlsx')
    if username in logins_df['Username'].values:
        user_row = logins_df[logins_df['Username'] == username]
        if password == user_row.iloc[0]['Password']:
            access_level = user_row.iloc[0]['AccessLevel']
            return True, access_level  # Retorna True e o nível de acesso
    return False, None  # Retorna False se não encontrou o usuário ou a senha, e None para o nível de acesso

# Função para receber o acesso por ID
access_level_cache = {}

def get_access_level_by_id(user_id):
    if user_id in access_level_cache:
        return access_level_cache[user_id]
    
    logins_df = pd.read_excel('db/logins.xlsx')
    user_row = logins_df[logins_df['Username'] == user_id]
    if not user_row.empty:
        access_level = user_row.iloc[0]['AccessLevel']
        access_level_cache[user_id] = access_level
        return access_level
    else:
        return None


# Funções para o Flask-Mail
def send_email_with_attachment(emails, pdf_path):
        msg = Message('Protocolo de Manuteção',
                    sender='seu_email@gmail.com',
                    recipients=[emails[0]])
        msg.cc = emails[1:]
        
        msg.body = '''
        Prezados,
        Gostaria de informar que a manutenção referente ao equipamento foi concluída conforme agendado.
                    
        Anexei ao presente e-mail o protocolo de manutenção detalhando todas as atividades realizadas, as condições atuais do equipamento e quaisquer recomendações relevantes para garantir seu pleno funcionamento.
                    
        Caso venham a surgir dúvidas, estou à disposição para esclarecê-las.
                    
        Atenciosamente,
                    
        Guilherme Amarante
        Laboratório Técnico
        '''
        
        # Obter apenas o nome do arquivo a partir do caminho completo
        pdf_filename = os.path.basename(pdf_path)
        
        with app.open_resource(pdf_path) as pdf:
            msg.attach(pdf_filename, 'application/pdf', pdf.read())

        try:
            mail.send(msg)
            print("E-mail enviado com sucesso para:", emails)
        except Exception as e:
            print("Erro ao enviar e-mail para", str(e))
        
# Funções auxiliares
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_maintenance_pdf(data):
    agora = datetime.now()
    
    pdf_filename = f"{data['protocolo']} - {data['nomeCliente']}.pdf"
    pdf_path = os.path.join(app.root_path, "static/protocolos", pdf_filename)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=2, bottomMargin=0, leftMargin=10, rightMargin=10)
    styles = getSampleStyleSheet()
    
    # Criando um novo estilo para um texto com tamanho de fonte menor
    styles.add(ParagraphStyle(name='SmallText', parent=styles['Normal'], fontSize=10))

    elements = []

    # Cabeçalho
    logo_path = os.path.join(app.root_path, "static", "img/logo-golden.png")
    logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
    logo.hAlign = 'CENTER'  # Centralizando o logo
    logo.vAlign = 'TOP'  # Ajustando o logo para o topo
    elements.append(logo)
    
    header_text = f"{data['nomeCliente']} - Protocolo: {data['protocolo']}"
    header_paragraph = Paragraph(header_text, styles['Heading1'])
    header_paragraph.alignment = 1  # Centralizando o texto do cabeçalho
    elements.append(header_paragraph)
    
    elements.append(Spacer(1, 12))

    # Corpo
    elements.append(Paragraph(f"<b>Data e Hora:</b> {data['dateTime']}", styles['BodyText']))
    
    elements.append(Paragraph(f"<b>Motivo:</b> {data['motivo']}", styles['BodyText']))
    
    modelo_customizacao = f"<b>Modelo:</b> {data['modelo']} | <b>Customização:</b> {data['customizacao']}"
    elements.append(Paragraph(modelo_customizacao, styles['BodyText']))
    
    elements.append(Paragraph(f"<b>ID:</b> {data['ids']}", styles['BodyText']))
    
    elements.append(Paragraph(f"<b>Faturamento:</b> {data['faturamento']}", styles['BodyText']))
    
    elements.append(Paragraph(f"<b>Tipo de Problema:</b> {data['tipoProblema']}", styles['BodyText']))
    
    elements.append(Spacer(1, 12))
    
    # Lendo o conteúdo dos arquivos txt de acordo com o tipo de problema
    tipo_problema = data['tipoProblema']
    tipo_problema_texts = {
        'Oxidação': "oxidação.txt",
        'Placa Danificada': "placa_danificada.txt",
        'Placa Danificada s/ Custo': "placa_danificada_sem_custo.txt",
        'USB Danificado': "usb_danificado.txt",
        'USB Danificado s/ Custo': "usb_danificado_sem_custo.txt",
        'Botão de Acionamento Danificado': "botao_acionamento.txt",
        'Botão de Acionamento Danificado s/ Custo': "botao_acionamento_sem_custo.txt",
        'Antena LoRA Danificada': "antena_lora.txt",
        'Sem problemas identificados': "sem_problema_identificado.txt",
    }
    
    if tipo_problema in tipo_problema_texts:
        file_path = os.path.join(app.root_path, "static/textos", tipo_problema_texts[tipo_problema])
        with open(file_path, 'r', encoding='utf-8') as file:
            text_content = file.read()
            elements.append(Paragraph(text_content, styles['SmallText']))
        
    if data['photos']:
        images = []
        for photo in data['photos']:
            photo_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], photo.filename)
            photo.save(photo_path)
            img = Image(photo_path, width=2.5*inch, height=1.25*inch)
            images.append(img)
        
        elements.append(Spacer(1, 12))
        img_table = create_image_table(images)
        elements.append(img_table)

    # Tratativa
    elements.append(Paragraph(f"<b>Tratativa:</b> {data['tratativa']}", styles['BodyText']))
    
    elements.append(Spacer(1, 12))
    
    # Adicionando a Tratativa
    tratativas = data['tratativa']
    tratativas_texts = {
        'Tratativa Oxidação': """
            <b>Sobre a Manutenção Realizada:</b><br/>
            Para resolver o problema do equipamento, foram realizados a tentativa de limpeza dos componentes e alguns testes posteriores, porém, sem sucesso, sendo assim será necessária a troca do dispositivo.<br/><br/>
            <i>Atenciosamente,</i><br/>
            Laboratório Técnico. 
        """,
        'Tratativa Placa Danificada': """
            <b>Sobre a Manutenção Realizada:</b><br/>
            Para resolver o problema do equipamento, foram realizadas as tratativas de conserto da placa e alguns testes posteriores, porém, sem sucesso, sendo assim será necessária a troca do dispositivo.<br/><br/>
            <i>Atenciosamente,</i><br/>
            Laboratório Técnico
        """,
        'Tratativa USB Danificado': """
            <b>Sobre a Manutenção Realizada:</b><br/>
            Para resolver o problema do equipamento, foram realizadas as tratativas de manutenção do conector e alguns testes posteriores, porém, sem sucesso, sendo assim será necessária a troca do dispositivo.<br/><br/>
            <i>Atenciosamente,</i><br/>
            Laboratório Técnico.
        """,
        'Tratativa Botão de Acionamento Danificado': """
            <b>Sobre a Manutenção Realizada:</b><br/>
            Diante deste diagnóstico e após as análises, afirmamos que será necessário a troca do dispositivo.<br/><br/>
            <i>Atenciosamente,</i><br/>
            Laboratório Técnico
        """,
        'Tratativa Antena LoRA Danificada': """
            <b>Sobre a Manutenção Realizada:</b><br/>
            Diante deste diagnóstico e após as tratativas, afirmamos que será necessário a troca do dispositivo.<br/><br/>
            <i>Atenciosamente,</i><br/>
            Laboratório Técnico
        """,
        'Tratativa Sem problemas identificados': """
            <b>Sobre a Manutenção Realizada:</b><br/>
            Gostaríamos de informar que concluímos com sucesso as manutenções necessárias no equipamento que nos foi confiado para reparo. Após uma análise cuidadosa, identificamos e corrigimos os problemas que estavam impactando o seu funcionamento adequado.<br/>
            <i>Atenciosamente,</i><br/>
            Laboratório Técnico. 
        """
    }
    
    if tratativas in tratativas_texts:
        tratativa_text = tratativas_texts[tratativas]
        tratativa_paragraph = Paragraph(tratativa_text, styles['SmallText'])
        elements.append(tratativa_paragraph)

    doc.build(elements)
    return pdf_filename

# Função para gerar o número de protocolo
def generate_maintenance_number():
    # Gerar número de protocolo baseado na data/hora atual
    now = datetime.now()
    protocolo = now.strftime("%Y%m%d%H%M")
    return protocolo

# Função para criar a grade de fotos
def create_image_table(images, max_col=3):
    table_data = []
    row = []
    for img in images:
        if len(row) == max_col:
            table_data.append(row)
            row = []
        row.append(img)
    if row:
        table_data.append(row)
    
    img_table = Table(table_data)
    img_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]))

    return img_table

# Função para salvar a nova manutenção no Excel
def save_to_excel(data):
    excel_file = 'db/registros_manutencao.xlsx'

    # Cria um DataFrame com os dados da nova manutenção
    df = pd.DataFrame({
        "Protocolo": [generate_maintenance_number()],
        "Nome do Cliente": [data["nomeCliente"]],
        "Motivo": [data["motivo"]],
        "Faturamento": [data["faturamento"]],
        "Modelo": [data["modelo"]],
        "Customização": [data["customizacao"]],
        "ID": [data["ids"]],
        "Tipo de Problema": [data["tipoProblema"]],
        "Tratativa": [data["tratativa"]],
        "Status": "Em Aberto"
    })

    # Se o arquivo já existe, lê o conteúdo e adiciona o novo registro
    if os.path.isfile(excel_file):
        existing_df = pd.read_excel(excel_file)
        df = pd.concat([existing_df, df], ignore_index=True)

    # Salva o DataFrame no arquivo Excel
    df.to_excel(excel_file, index=False)

# Função para obter as manutenções do arquivo Excel
def get_manutencoes():
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
        manutencoes = df.to_dict('records')
        return manutencoes
    return []

def update_manutencao(protocolo, status):
    df = pd.read_excel(excel_file)
    df.loc[df['Protocolo'] == int(protocolo), 'Status'] = status
    df.to_excel(excel_file, index=False)

def adicionar_data_aprovacao_excel(protocolo, cliente):
    arquivo_excel = 'db/registros_manutencao.xlsx'

    # Ler o arquivo Excel
    df = pd.read_excel(arquivo_excel)

    # Flag para indicar se o protocolo e cliente foram encontrados
    encontrado = False

    # Iterar pelo DataFrame para encontrar o protocolo e cliente
    for index, row in df.iterrows():
        if str(row['Protocolo']) == str(protocolo) and row['Nome do Cliente'] == cliente:
            # Obter a data e hora atual
            data_aprovacao = datetime.now()

            # Formatar a data como desejado
            data_formatada = data_aprovacao.strftime('%d-%m-%Y %H:%M')
            
            # Atualizar a coluna 'Data de Aprovação' na linha encontrada
            df.loc[index, 'Data de Aprovação'] = data_formatada
            
            encontrado = True
            break

    if not encontrado:
        return

    # Salvar de volta para o arquivo Excel
    df.to_excel(arquivo_excel, index=False)
    
def mover_para_diretoria(protocolo):
    # Ler a manutenção com o protocolo fornecido
    df_manutencao = pd.read_excel('db/registros_manutencao.xlsx')
    manutencao = df_manutencao[df_manutencao['Protocolo'] == int(protocolo)].to_dict('records')[0]

    # Adicionar a manutenção à planilha "diretoria.xlsx"
    df_diretoria = pd.read_excel('db/diretoria.xlsx')
    df_diretoria = df_diretoria.append(manutencao, ignore_index=True)

    # Salvar a planilha atualizada
    df_diretoria.to_excel('db/diretoria.xlsx', index=False)

def adicionar_manutencao_diretoria(protocolo, cliente, faturamento):
    arquivo_excel_diretoria = 'db/diretoria.xlsx'

    # Criar um DataFrame com os dados da nova manutenção
    nova_manutencao = {
        'Protocolo': [protocolo],
        'Nome do Cliente': [cliente],
        'Faturamento': [faturamento],
        'Status': ['Pendente'],  # Status inicial ao enviar para a diretoria
        'Data de Recebimento': [datetime.now().strftime('%d-%m-%Y %H:%M')]  # Data atual como data de recebimento
    }

    # Verificar se o arquivo da Diretoria existe
    if not os.path.isfile(arquivo_excel_diretoria):
        # Se não existe, criar um novo arquivo com os dados da nova manutenção
        df_nova_manutencao = pd.DataFrame(nova_manutencao)
        df_nova_manutencao.to_excel(arquivo_excel_diretoria, index=False)
    else:
        # Se o arquivo já existe, ler o arquivo e adicionar a nova linha
        df_diretoria = pd.read_excel(arquivo_excel_diretoria)
        df_nova_manutencao = pd.DataFrame(nova_manutencao)
        df_diretoria = pd.concat([df_diretoria, df_nova_manutencao], ignore_index=True)
        df_diretoria.to_excel(arquivo_excel_diretoria, index=False)
        
def adicionar_data_aprovacao_diretoria(protocolo):
    arquivo_excel = 'db/diretoria.xlsx'

    # Ler o arquivo Excel
    df = pd.read_excel(arquivo_excel)

    # Flag para indicar se o protocolo foi encontrado
    encontrado = False

    # Iterar pelo DataFrame para encontrar o protocolo
    for index, row in df.iterrows():
        if str(row['Protocolo']) == str(protocolo):
            # Obter a data e hora atual
            data_aprovacao = datetime.now()

            # Formatar a data como desejado
            data_formatada = data_aprovacao.strftime('%d-%m-%Y %H:%M')
            
            # Atualizar a coluna 'Data de Aprovação' na linha encontrada
            df.loc[index, 'Data de Aprovação'] = data_formatada
            
            encontrado = True
            break

    if not encontrado:
        return

    # Salvar de volta para o arquivo Excel
    df.to_excel(arquivo_excel, index=False)
        
def get_faturamento_from_protocolo(protocolo):
    # Caminho para o arquivo Excel
    arquivo_excel = 'db/registros_manutencao.xlsx'

    # Ler o arquivo Excel para obter as informações da manutenção
    df_manutencao = pd.read_excel(arquivo_excel)

    # Filtrar o faturamento com base no protocolo
    faturamento = df_manutencao[df_manutencao['Protocolo'] == int(protocolo)]['Faturamento'].values

    # Verificar se foi encontrado algum faturamento
    if len(faturamento) > 0:
        faturamento_obtido = faturamento[0]
        return faturamento_obtido
    else:
        return "Faturamento Desconhecido"
             
# Função separada para enviar e-mail de aprovação
def enviar_email_aprovacao(email, pdf_path):
    send_email_with_attachment(email, pdf_path)
    
def get_next_protocol_number():
    protocolo_file = 'db/protocolo_counter.txt'
    next_number = 1

    if os.path.exists(protocolo_file):
        with open(protocolo_file, 'r') as f:
            next_number = int(f.read())
            next_number += 1

    with open(protocolo_file, 'w') as f:
        f.write(str(next_number))

    return next_number
    
# Função para gerar o número da requisição
def generate_requisicao_number():
    now = datetime.now()
    protocolo = now.strftime("%Y%m%d%H%M")
    return protocolo

# Função para salvar os dados da requisição no arquivo Excel
def save_requisicao_to_excel(data):
    requisicao_file = 'db/registros_requisicoes.xlsx'

    # Cria um DataFrame com os dados da nova requisição
    df = pd.DataFrame({
        "Protocolo": [generate_requisicao_number()],
        "Data": [data["dateTime"]],
        "CNPJ": [data["cnpj"]],
        "Início de Contrato": [data["inicio_contrato"]],
        "Vigência": [data["vigencia"]],
        "Motivo": [data["motivo"]],
        "Cliente": [data["cliente"]],
        "Comercial": [data["comercial"]],
        "Contrato": [data["contrato"]],
        "Envio": [data["envio"]],
        "Endereço": [data["endereco"]],
        "A/C": [data["ac"]],
        "E-mail": [data["email"]],
        "Quantidade": [data["quantidade"]],
        "Modelo": [data["modelo"]],
        "Customização": [data["customizacao"]],
        "TP": [data["tp"]],
        "Carregador": [data["carregador"]],
        "Cabo": [data["cabo"]],
        "Fatura": [data["fatura"]],
        "Valor": [data["valor"]],
        "Forma de Pagamento": [data["forma_pagamento"]],
        "Observações": [data["observacoes"]],
        "Validação": [data["validacao"]],
        "Status": "Em Aberto"
    })

    # Se o arquivo já existe, lê o conteúdo e adiciona o novo registro
    if os.path.isfile(requisicao_file):
        existing_df = pd.read_excel(requisicao_file)
        df = pd.concat([existing_df, df], ignore_index=True)

    # Salva o DataFrame no arquivo Excel
    df.to_excel(requisicao_file, index=False)

# Função para obter todas as requisições do arquivo Excel
def get_requisicoes():
    if os.path.exists(requisicao_file):
        df = pd.read_excel(requisicao_file)
        requisicoes = df.to_dict('records')
        return requisicoes
    return []
    
# Função para gerar o PDF da requisição
def generate_requisicao_pdf(data):
    # Caminho e nome do arquivo PDF
    pdf_filename = f"{data['protocolo']} - {data['cliente']}.pdf"
    pdf_path = os.path.join(app.root_path, "static/requisicoes", pdf_filename)

    # Criação do PDF com reportlab
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "Protocolo de Requisição")
    c.drawString(100, 730, f"Protocolo: {data['protocolo']}")
    c.drawString(100, 690, f"Data: {data['dateTime']}")
    c.drawString(100, 670, f"CNPJ: {data['cnpj']}")
    c.drawString(100, 650, f"Início de Contrato: {data['inicio_contrato']}")
    c.drawString(100, 630, f"Vigência: {data['vigencia']}")
    c.drawString(100, 610, f"Motivo: {data['motivo']}")
    c.drawString(100, 590, f"Cliente: {data['cliente']}")
    c.drawString(100, 570, f"Comercial: {data['comercial']}")
    c.drawString(100, 550, f"Contrato: {data['contrato']}")
    c.drawString(100, 530, f"Envio: {data['envio']}")
    c.drawString(100, 510, f"Endereço: {data['endereco']}")
    c.drawString(100, 490, f"A/C: {data['ac']}")
    c.drawString(100, 470, f"E-mail: {data['email']}")
    c.drawString(100, 450, f"Quantidade: {data['quantidade']}")
    c.drawString(100, 430, f"Modelo: {data['modelo']}")
    c.drawString(100, 410, f"Customização: {data['customizacao']}")
    c.drawString(100, 390, f"TP: {data['tp']}")
    c.drawString(100, 370, f"Carregador: {data['carregador']}")
    c.drawString(100, 350, f"Cabo: {data['cabo']}")
    c.drawString(100, 330, f"Fatura: {data['fatura']}")
    c.drawString(100, 310, f"Valor: {data['valor']}")
    c.drawString(100, 290, f"Forma de Pagamento: {data['forma_pagamento']}")
    c.drawString(100, 270, f"Observações: {data['observacoes']}")
    c.drawString(100, 250, f"Validação: {data['validacao']}")
    c.save()

    # Salvar o PDF no caminho especificado
    with open(pdf_path, 'wb') as f:
        f.write(buffer.getvalue())

    return True

# Função para atualizar o status da requisição no arquivo Excel
def update_requisicao(protocolo, status):
    df = pd.read_excel(requisicao_file)
    df.loc[df['Protocolo'] == protocolo, 'Status'] = status
    df.to_excel(requisicao_file, index=False)
    
# Função para ler opções de um arquivo de texto
def read_options_from_file(file_name):
    file_path = os.path.join(app.root_path, 'static', 'textos', 'dropdown', f'{file_name}.txt')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            options = [line.strip() for line in file if line.strip()]
            return options
    else:
        return []

# Função para carregar opções de todos os campos
def load_all_options():
    campos = {
        "comercial": read_options_from_file("comercial"),
        "contrato": read_options_from_file("contrato"),
        "envio": read_options_from_file("envio"),
        "modelo": read_options_from_file("modelo"),
        "customizacao": read_options_from_file("customizacao")
    }
    return campos
