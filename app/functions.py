import os
from app import app
import os
from flask_mail import Mail, Message
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image, Table, TableStyle
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

MOTIVOS = {
    "manutencao": "Manutenção",
    "devolucao_estoque": "Devolução/Estoque"
}

# Função para verificar o login
def check_login(username, password):
    df = pd.read_excel('db/logins.xlsx')
    if username in df['Username'].values:
        index = df[df['Username'] == username].index[0]
        if password == df.loc[index, 'Password']:
            return True
    return False

# Funções para o Flask-Mail
def send_email_with_attachment(email, pdf_path):
    msg = Message('Protocolo de Manuteção',
                  sender='seu_email@gmail.com',
                  recipients=[email])
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
        print("E-mail enviado com sucesso para:", email)
    except Exception as e:
        print("Erro ao enviar e-mail:", str(e))
# Funções auxiliares
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_maintenance_pdf(data):
    # Gerando o nome do arquivo PDF com base no protocolo, cliente e data
    agora = datetime.now()
    datinha = agora.strftime("%d-%m-%Y")
    
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
    
    # Adicionando o Tipo de Problema
    elements.append(Paragraph(f"<b>Tipo de Problema:</b> {data['tipoProblema']}", styles['BodyText']))
    
    elements.append(Spacer(1, 12))
    
    # Adicionando o Tipo de Problema
    tipo_problema = data['tipoProblema']
    tipo_problema_texts = {
        'Oxidação': """
            Prezado Cliente,<br/>
            Gostaríamos de informar sobre a manutenção realizada em seu equipamento eletrônico, no qual constatamos a presença de oxidação na placa eletrônica.<br/><br/>
            <b>Motivo da Manutenção:</b><br/>
            Durante nossa análise minuciosa, identificamos que a presença de oxidação na placa eletrônica foi o motivo principal das falhas e problemas que o equipamento vinha apresentando. A oxidação é um processo natural, mas, neste caso, observamos que ela foi acelerada devido a condições que indicam um uso inadequado ou exposição a ambientes não recomendados.<br/><br/>
            <b>Causa: Mal Uso ou Ambiente Inadequado:</b><br/>
            A oxidação pode ser resultado de ambientes úmidos, contato com líquidos ou substâncias corrosivas. Com base em nossa análise, parece que o equipamento pode ter sido exposto a condições que favoreceram esse processo. Entendemos que isso pode não ter sido intencional, mas é importante destacar que ambientes não adequados ou manuseio impróprio podem acelerar a oxidação e causar danos aos componentes eletrônicos.<br/><br/>
            <b>Consequências da Oxidação:</b><br/>
            A presença de oxidação na placa eletrônica pode levar a problemas como mau contato, falhas intermitentes e até mesmo danos irreversíveis em componentes vitais. Isso pode resultar em mau funcionamento do equipamento, perda de desempenho e, em casos mais graves, a necessidade de substituição de peças ou do próprio equipamento.
        """,
        'Placa Danificada': """
            Prezado Cliente,<br/>
            Gostaríamos de informar sobre a manutenção realizada em seu equipamento eletrônico, no qual constatamos dano físico ao equipamento.<br/><br/>
            <b>Motivo da Manutenção:</b><br/>
            Durante a inspeção cuidadosa do equipamento, identificamos que ele apresenta danos físicos significativos. Após uma análise minuciosa, constatamos que o dano foi ocasionado devido ao excesso de peso ou manuseio incorreto do equipamento.<br/><br/>
            <b>Causa: Mal uso ou excesso de peso.</b><br/>
            Com base em nossa análise, parece que o equipamento pode ter sido exposto a condições que favoreceram esse processo. Entendemos que isso pode não ter sido intencional, mas é importante destacar que ambientes não adequados ou manuseio impróprio do equipamento pode ocasionar tais problemas.<br/><br/>
            <b>Consequências da danificação da placa do equipamento:</b><br/>
            A presença do dano na placa eletrônica pode levar a problemas como mau contato, falhas intermitentes e até mesmo danos irreversíveis em componentes vitais. Isso pode resultar em mau funcionamento do equipamento, perda de desempenho e, em casos mais graves, a necessidade de substituição de peças ou do próprio equipamento.
        """,
        'USB Danificado': """
            Prezado Cliente,<br/>
            Gostaríamos de informar sobre a manutenção realizada em seu equipamento eletrônico, no qual constatamos a falha na conexão do usb.<br/><br/>
            <b>Motivo da Manutenção:</b><br/>
            Durante nossa inspeção, identificamos que a porta USB do equipamento está danificada. Isso pode ser observado pela foto anexada gerando falha na leitura do equipamento. É importante compreendermos as razões pelas quais essa falha ocorreu, a fim de evitar problemas futuros semelhantes.<br/><br/>
            <b>Causa:</b><br/>
            Com base em nossa análise, as razões pelas quais a porta USB foi danificada incluem Inserção Incorreta, Força Excessiva, Conexão e Desconexão Frequentes, Curto-Circuito, Sujeira e Poeira e Falhas de Energia.<br/><br/>
            <b>Consequências:</b><br/>
            O dano no conector USB resulta em Incapacidade de Conexão, Transferência de Dados Interrompida e Carregamento Ineficaz.
        """,
        'Botão de Acionamento Danificado': """
            Prezado Cliente,<br/>
            Gostaríamos de informar sobre a manutenção realizada em seu equipamento eletrônico, no qual constatamos que o botão de liga/desliga está aparentemente danificado.<br/><br/>
            <b>Motivo da Manutenção:</b><br/>
            Durante nossa análise, identificamos que o botão de acionamento do equipamento está danificado devido a sinais de mau uso. Este botão desempenha um papel essencial no uso cotidiano do equipamento, sendo responsável pela operação de ligar e desligar.<br/><br/>
            <b>Causa:</b><br/>
            As causas para o dano no botão de acionamento podem incluir: Pressão Excessiva, Uso Incorreto, Desgaste por mal uso.<br/><br/>
            <b>Consequências sobre o dano no botão do equipamento:</b><br/>
            Os danos no botão de acionamento resultam em várias dificuldades para o uso adequado do equipamento, tais como: Dificuldade de Ligação, Problemas de Desligamento, Operação Intermitente.
        """,
        'Antena LoRA Danificada': """
            Prezado Cliente,<br/>
            Gostaríamos de informar sobre a manutenção realizada em seu equipamento eletrônico, no qual constatamos dano físico na Antena LORA.<br/><br/>
            <b>Motivo da Manutenção:</b><br/>
            Durante nossa análise, identificamos que a Antena LoRa do equipamento está danificada. Esta antena desempenha um papel crucial na comunicação do equipamento, sendo responsável pela transmissão e recepção de dados através da tecnologia LoRa (Long Range).<br/><br/>
            <b>Causa: Mal uso ou impacto.</b><br/>
            As causas para o dano da antena LORA do equipamento podem incluir: Impactos Físicos, Instalação Incorreta e Excesso de peso sobre a antena.<br/><br/>
            <b>Consequências sobre o dano na Antena LORA:</b><br/>
            Os danos na Antena LORA resultam em uma variedade de problemas, tais como: Perda de Conexão, Alcance Reduzido e Falhas na Transmissão de Dados.
        """,
        'Sem problemas identificados': """
            Prezado Cliente,<br/>
            Gostaríamos de informar sobre a manutenção realizada em seu equipamento eletrônico, no qual não constatamos a presença de problemas.<br/><br/>
            <b>Motivo da Manutenção:</b><br/>
            Durante nossa análise minuciosa, realizamos atualizações essenciais de firmware, visando garantir o desempenho otimizado e a estabilidade operacional do equipamento.<br/>
            É com grande satisfação que comunicamos que o equipamento agora está plenamente funcional, atendendo aos padrões de qualidade e desempenho esperados.<br/>
        """
    }
    
    if tipo_problema in tipo_problema_texts:
        elements.append(Paragraph(tipo_problema_texts[tipo_problema], styles['SmallText']))
        
    if data['photos']:
        images = []
        for photo in data['photos']:
            photo_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], photo.filename)
            photo.save(photo_path)
            img = Image(photo_path, width=2*inch, height=1.5*inch)
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

def generate_maintenance_number():
    # Gerar número de protocolo baseado na data/hora atual
    now = datetime.now()
    protocolo = now.strftime("%d%m%y%H%M")
    return protocolo

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
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    return img_table

def save_to_excel(data):
    excel_file = 'db/registros_manutencao.xlsx'

    # Cria um DataFrame com os dados da nova manutenção
    df = pd.DataFrame({
        "Protocolo": [generate_maintenance_number()],
        "Nome do Cliente": [data["nomeCliente"]],
        "Motivo": [data["motivo"]],
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
    print("Adicionando data de aprovação no Excel...")
    arquivo_excel = 'db/registros_manutencao.xlsx'

    # Ler o arquivo Excel
    df = pd.read_excel(arquivo_excel)

    # Imprimir o DataFrame para debug
    print("DataFrame lido do Excel:")
    print(df)

    # Verificar os protocolos e clientes disponíveis no DataFrame
    print("Protocolos disponíveis:")
    print(df['Protocolo'].unique())

    print("Clientes disponíveis:")
    print(df['Nome do Cliente'].unique())

    # Imprimir protocolo e cliente para debug
    print("Protocolo:", protocolo)
    print("Cliente:", cliente)

    # Flag para indicar se o protocolo e cliente foram encontrados
    encontrado = False

    # Iterar pelo DataFrame para encontrar o protocolo e cliente
    for index, row in df.iterrows():
        if str(row['Protocolo']) == str(protocolo) and row['Nome do Cliente'] == cliente:
            # Obter a data e hora atual
            data_aprovacao = datetime.now()

            # Formatar a data como desejado
            data_formatada = data_aprovacao.strftime('%d-%m-%Y %H:%M')

            print("Protocolo encontrado:", protocolo)
            print("Cliente encontrado:", cliente)
            
            # Atualizar a coluna 'Data de Aprovação' na linha encontrada
            df.loc[index, 'Data de Aprovação'] = data_formatada
            
            encontrado = True
            break

    if not encontrado:
        print("Protocolo ou cliente não encontrado na planilha.")
        return

    # Imprimir o DataFrame após a atualização para debug
    print("DataFrame após atualização:")
    print(df)

    # Salvar de volta para o arquivo Excel
    df.to_excel(arquivo_excel, index=False)
    print("Data de aprovação adicionada com sucesso!")

    # Verificar se o valor foi realmente salvo na célula correta
    print("Verificando valor na célula após salvar:")
    print(pd.read_excel(arquivo_excel)['Data de Aprovação'].loc[index])