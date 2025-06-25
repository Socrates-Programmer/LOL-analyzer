from flask import Blueprint, render_template, request, redirect, flash, current_app, jsonify
import os
import requests

bp = Blueprint('match_analyzer', __name__, static_folder='static')

API_KEY = 'RGAPI-5323a6d4-ebe9-4d12-9180-ae635dc407ca'  # Pon aquí tu API key de Riot
REGION = 'americas'  # Cambia a la región correcta

rank_values = {
    'IRON': 1,
    'BRONZE': 2,
    'SILVER': 3,
    'GOLD': 4,
    'PLATINUM': 5,
    'DIAMOND': 6,
    'MASTER': 7,
    'GRANDMASTER': 8,
    'CHALLENGER': 9
}

role_impact = {
    "TOP": 0.17,
    "JUNGLE": 0.22,
    "MID": 0.25,
    "ADC": 0.21,
    "SUPPORT": 0.15
}


@bp.route('/')
def home():

    return render_template('pages/home.html')

@bp.route('/Analyzer')
def match_analyzer():
    db = current_app.db
    invocadores_raw = list(db.invocadores.find())
    
    # Convertir _id a string para evitar problemas en plantilla
    invocadores = []
    for i in invocadores_raw:
        i['_id'] = str(i['_id'])
        invocadores.append(i)
    
    print("Jugadores desde DB:", invocadores)
    return render_template('pages/analyzer.html',
                        invocadores=invocadores,
                        equipo1_prob=55,
                        equipo2_prob=45)




@bp.route('/summoner', methods=["GET", "POST"])
def summoner():
    if request.method == "POST":
        summoner_name = request.form.get("summonerName")
        tagline = request.form.get("tagline")
        password = request.form.get("password")
        rank = request.form.get("rank")

        if password != os.getenv("PASS"):
            flash("❌ Contraseña incorrecta", "danger")
            return redirect("/summoner")

        db = current_app.db
        invocadores = db.invocadores

        invocadores.insert_one({
            "summoner_name": summoner_name,
            "tagline": tagline,
            "rank": rank
        })

        flash(f"✅ {summoner_name}#{tagline} y rank: {rank}, se han guardado correctamente", "success")
        return redirect("/summoner")

    return render_template('pages/summoner.html')

@bp.route('/summoner/list')
def summoner_list():
    db = current_app.db
    invocadores = db.invocadores.find()

    return render_template('pages/all_summoners.html', invocadores=invocadores)

def obtener_datos_jugador(summonerName):
    print(f"Obteniendo datos para: {summonerName}")
    try:
        url_summoner = f'https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summonerName}'
        headers = {"X-Riot-Token": API_KEY}
        r = requests.get(url_summoner, headers=headers)
        if r.status_code != 200:
            print(f"Error al obtener summonerId para {summonerName}: {r.status_code}")
            return None
        summoner_data = r.json()
        puuid = summoner_data['puuid']
        summonerId = summoner_data['id']

        match_url = f'https://{AMERICAS_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count=1'
        r = requests.get(match_url, headers=headers)
        if r.status_code != 200 or not r.json():
            print(f"No hay partidas para {summonerName} o error {r.status_code}")
            return None
        match_id = r.json()[0]

        match_detail_url = f'https://{AMERICAS_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}'
        r = requests.get(match_detail_url, headers=headers)
        if r.status_code != 200:
            print(f"Error al obtener detalles de partida para {summonerName}: {r.status_code}")
            return None

        match_data = r.json()
        player_data = next((p for p in match_data['info']['participants'] if p['puuid'] == puuid), None)
        if not player_data:
            print(f"No se encontró data del jugador en la partida para {summonerName}")
            return None

        kills = player_data['kills']
        deaths = player_data['deaths']
        assists = player_data['assists']
        role = player_data['teamPosition']

        url_rank = f'https://{REGION}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summonerId}'
        r = requests.get(url_rank, headers=headers)
        ranks = r.json() if r.status_code == 200 else []

        solo_rank = next((entry for entry in ranks if entry['queueType'] == 'RANKED_SOLO_5x5'), None)
        tier = solo_rank['tier'] if solo_rank else 'IRON'

        print(f"Datos obtenidos para {summonerName}: kills={kills}, deaths={deaths}, assists={assists}, tier={tier}, role={role}")
        return {
            'kills': kills,
            'deaths': deaths,
            'assists': assists,
            'rank': tier,
            'role': role.upper()
        }
    except Exception as e:
        print(f"Excepción al obtener datos para {summonerName}: {e}")
        return None


@bp.route('/comparar', methods=['POST'])
def comparar():
    data = request.get_json()
    print("Datos recibidos:", data)
    team1 = data.get('team1')
    team2 = data.get('team2')
    print("Team1:", team1)
    print("Team2:", team2)

    if not team1 or not team2 or len(team1) != 5 or len(team2) != 5:
        print("Error: equipos incompletos o inválidos")
        return jsonify({'error': 'Se requieren dos equipos de 5 jugadores cada uno'}), 400

    errores = []

    def calcular_contribucion(k, d, a, tier, role):
        deaths = max(d, 1)
        kda = (k + a) / deaths
        rank_score = rank_values.get(tier.upper(), 0)
        role_weight = role_impact.get(role.upper(), 0)
        return kda * rank_score * role_weight

    def obtener_score_equipo(team):
        total = 0
        for player in team:
            datos = obtener_datos_jugador(player)
            if not datos:
                errores.append(player)
                continue
            total += calcular_contribucion(datos['kills'], datos['deaths'], datos['assists'], datos['rank'], datos['role'])
        return total

    score_team1 = obtener_score_equipo(team1)
    score_team2 = obtener_score_equipo(team2)
    total = score_team1 + score_team2

    if errores:
        return jsonify({
            'error': 'No se pudo obtener información para los siguientes jugadores:',
            'jugadores': errores
        }), 400

    if total == 0:
        prob1 = prob2 = 50.0
    else:
        prob1 = round((score_team1 / total) * 100, 2)
        prob2 = round((score_team2 / total) * 100, 2)

    return jsonify({'equipo1_prob': prob1, 'equipo2_prob': prob2})
