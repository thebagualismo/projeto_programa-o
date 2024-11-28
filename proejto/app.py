import sys

from flask import Flask, render_template, request, redirect, url_for
from geopy.geocoders import Nominatim
import re
import webbrowser


app = Flask(__name__)

# Dicionário geral que armazena as ordens de manutenção
dicionario_geral = {}


# Função para obter coordenadas
def obter_coordenadas(endereco):
    geolocator = Nominatim(user_agent="ordem_manutencao")
    try:
        location = geolocator.geocode(endereco)
        if location:
            return {"latitude": location.latitude, "longitude": location.longitude}
        else:
            return {"latitude": None, "longitude": None}
    except Exception as e:
        print(f"Erro ao buscar coordenadas: {e}")
        return {"latitude": None, "longitude": None}


# Função para cadastrar uma ordem de manutenção (via formulário)
def ordem_manutencao(nome, cpf, telefone, cidade, bairro, rua, numero, complemento, problema):
    d_registro = {}

    # Processando os dados recebidos do formulário
    d_registro["nome"] = nome if nome else "N/A"
    d_registro["cpf"] = cpf if cpf else "N/A"
    d_registro["telefone"] = telefone if telefone else "N/A"

    # Endereço
    d_endereco = {
        "cidade": cidade,
        "bairro": bairro,
        "rua": rua,
        "numero": numero,
        "complemento": complemento if complemento else "N/A"
    }

    d_registro["endereco"] = d_endereco

    # Demanda
    demanda = {
        "problema": problema if problema else "N/A",
        "status": "Pendente",
        "servico": "Nenhum"
    }
    d_registro["solicitacao"] = demanda

    # Buscar coordenadas do endereço completo
    endereco_completo = f'{d_endereco["rua"]}, {d_endereco["numero"]}, {d_endereco["bairro"]}, {d_endereco["cidade"]}'
    d_endereco["coordenadas"] = obter_coordenadas(endereco_completo)

    # Adiciona a ordem no dicionário geral, com um identificador único
    id_ordem = len(dicionario_geral) + 1
    dicionario_geral[id_ordem] = d_registro

    return id_ordem, d_registro


@app.route('/')
def home():
    wallpaper_link = "https://wallpapercave.com/wp/wp12054731.jpg   "  # Link direto da imagem
    return render_template('home.html', wallpaper_link=wallpaper_link)



@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        # Coletando os dados do formulário com a chave correta
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        telefone = request.form.get('telefone')
        cidade = request.form.get('cidade')
        bairro = request.form.get('bairro')
        rua = request.form.get('rua')
        numero = request.form.get('numero')
        complemento = request.form.get('complemento')
        problema = request.form.get('problema')

        # Validação e formatação do CPF
        if not re.match(r'^\d{3}\s\d{3}\s\d{3}\s\d{2}$', cpf):
            return render_template(
                'cadastrar.html',
                message="CPF inválido! Formato esperado: xxx xxx xxx xx",
                request_form=request.form
            )
        else:
            # Transformar o CPF no formato com pontos e traço
            cpf_formatado = re.sub(r'(\d{3})\s(\d{3})\s(\d{3})\s(\d{2})', r'\1.\2.\3-\4', cpf)

        # Validação e formatação do telefone
        if not re.match(r'^\d{2}\s\d{1}\s\d{4}\s\d{4}$', telefone):
            return render_template(
                'cadastrar.html',
                message="Telefone inválido! Formato esperado: xx x xxxx xxxx",
                request_form=request.form
            )
        else:
            # Transformar o telefone no formato com parênteses e traço
            telefone_formatado = re.sub(r'(\d{2})\s(\d{1})\s(\d{4})\s(\d{4})', r'(\1) \2 \3-\4', telefone)

        # Cadastrando a ordem com os dados formatados
        id_ordem, d_registro = ordem_manutencao(
            nome, cpf_formatado, telefone_formatado, cidade, bairro, rua, numero, complemento, problema
        )

        # Cadastro bem-sucedido
        return render_template(
            'cadastrar.html',
            success_message="Cadastro realizado com sucesso!",
            request_form={}
        )

    return render_template('cadastrar.html')


@app.route('/mostrar_demandas')
def mostrar_demandas():
    # Passando as ordens para o template para exibição
    return render_template('mostrar_demandas.html', ordens=dicionario_geral)



@app.route('/gerar_relatorio')
def gerar_relatorio():
    # Inicializando variáveis de contagem
    total_ordens = len(dicionario_geral)
    pendentes = 0
    em_andamento = 0
    concluídas = 0
    ordens_por_lider = {}
    # Percorrendo as ordens e contando os status e as ordens por líder
    for ordem in dicionario_geral.values():
        # Contabilizando os status
        status = ordem['solicitacao']['status']
        if status == 'Pendente':
            pendentes += 1
        elif status == 'Em andamento':
            em_andamento += 1
        elif status == 'Concluída':
            concluídas += 1

        # Contabilizando ordens por líder de equipe (supondo que o líder esteja armazenado em 'lider' em 'solicitacao')
        lider = ordem['solicitacao'].get('lider_equipe', 'N/A')  # Se não houver líder, será 'N/A'
        if lider in ordens_por_lider:
            ordens_por_lider[lider] += 1
        else:
            ordens_por_lider[lider] = 1

    # Calculando as porcentagens
    porcentagem_pendentes = (pendentes / total_ordens * 100) if total_ordens else 0
    porcentagem_em_andamento = (em_andamento / total_ordens * 100) if total_ordens else 0
    porcentagem_concluidas = (concluídas / total_ordens * 100) if total_ordens else 0

    # Passando os dados para o template
    return render_template(
        'relatorio.html',
        total_ordens=total_ordens,
        pendentes=pendentes,
        em_andamento=em_andamento,
        concluídas=concluídas,
        porcentagem_pendentes=porcentagem_pendentes,
        porcentagem_em_andamento=porcentagem_em_andamento,
        porcentagem_concluidas=porcentagem_concluidas,
        ordens_por_lider=ordens_por_lider
    )



@app.route('/abrir_mapa', methods=['GET'])
def abrir_mapa():
    id_ordem = request.args.get('id_ordem', type=int)
    if id_ordem in dicionario_geral:
        ordem = dicionario_geral[id_ordem]
        coordenadas = ordem['endereco'].get('coordenadas', None)

        if coordenadas and coordenadas['latitude'] and coordenadas['longitude']:
            latitude = coordenadas['latitude']
            longitude = coordenadas['longitude']
            url = f"https://www.google.com/maps?q={latitude},{longitude}"
            webbrowser.open(url)  # Isso abre o Google Maps no navegador do usuário
            return redirect(url)  # Opcional: Redireciona para o link do Google Maps
        else:
            return "Coordenadas não encontradas para esta ordem.", 404
    else:
        return "Ordem não encontrada!", 404



@app.route('/alterar_demandas', methods=['GET', 'POST'])
def alterar_demandas():
    if request.method == 'POST':
        # Coleta os dados do formulário
        id_ordem = int(request.form['id_ordem'])
        novo_status = request.form['status']
        novo_servico = request.form['servico']
        lider_equipe = request.form['lider_equipe']
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)

        # Atualiza a demanda
        if id_ordem in dicionario_geral:

            dicionario_geral[id_ordem]['solicitacao']['status'] = novo_status
            dicionario_geral[id_ordem]['solicitacao']['servico'] = novo_servico
            dicionario_geral[id_ordem]['solicitacao']['lider_equipe'] = lider_equipe

            # Verifica se o GPS está presente e abre o link do Google Maps
            if latitude is not None and longitude is not None:
                url = f"https://www.google.com/maps?q={latitude},{longitude}"
                webbrowser.open(url)
                message = f"Demanda {id_ordem} alterada com sucesso! Localização no Google Maps."
            else:
                message = f"Demanda {id_ordem} alterada com sucesso!"
        else:
            message = "Ordem não encontrada!"

        # Retorna para o template com a mensagem
        return render_template('alterar_demandas.html', message=message, ordens=dicionario_geral)

    return render_template('alterar_demandas.html', ordens=dicionario_geral)


@app.route('/alterar_wallpaper', methods=['POST'])
def alterar_wallpaper():
    imagem_link = request.form.get('imagem_link')
    # Validar o link da imagem, se necessário
    if imagem_link:
        # Aqui você poderia salvar o link em uma variável global ou banco de dados
        app.config['WALLPAPER'] = imagem_link
        return render_template('menu.html', message="Wallpaper alterado com sucesso!")
    else:
        return render_template('menu.html', message="Por favor, insira um link válido.")


@app.route('/sair_programa')
def sair_programa():
    sys.exit()



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
