from flask import Blueprint, render_template, request, redirect, flash, current_app, jsonify, session, url_for
import os
import requests
import time
import uuid
import threading

bp = Blueprint('match_analyzer', __name__, static_folder='static')

<<<<<<< HEAD
API_KEY = os.getenv("API_KEY")  # ✅ Usa la clave desde el .env
=======
API_KEY = ''  # Pon aquí tu API key de Riot
>>>>>>> fb02715306b1dd955b3d07cb24fe1b406b3a09f6
REGION = 'americas'  # Cambia a la región correcta

rank_values = {
    'IRON': 1,
    'BRONZE': 2,
    'SILVER': 3,
    'GOLD': 4,
    'PLATINUM': 5,
    'EMERALD': 6,
    'DIAMOND': 7,
    'MASTER': 8,
    'GRANDMASTER': 9,
    'CHALLENGER': 10
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

@bp.route('/summoner', methods=["GET", "POST"])
def summoner():
    if request.method == "POST":
        summoner_name = request.form.get("summonerName")
        tagline = request.form.get("tagline")
        password = request.form.get("password")
        rank = request.form.get("rank")

        if password != os.getenv("PASS"):
            flash(" Contraseña incorrecta", "danger")
            return redirect("/summoner")

        db = current_app.db
        invocadores = db.invocadores

        invocadores.insert_one({
            "summoner_name": summoner_name,
            "tagline": tagline,
            "rank": rank
        })

        flash(f" {summoner_name}#{tagline} y rank: {rank}, se han guardado correctamente", "success")
        return redirect("/summoner")

    return render_template('pages/summoner.html')

@bp.route('/summoner/list')
def summoner_list():
    db = current_app.db
    invocadores = list(db.invocadores.find())
    kda = list(db.kda_stats.find())

    return render_template('pages/all_summoners.html', datos=zip(invocadores, kda))

@bp.route('/Analyzer')
def match_analyzer():
    db = current_app.db
    invocadores_raw = list(db.invocadores.find())

    invocadores = []
    for i in invocadores_raw:
        i['_id'] = str(i['_id'])
        invocadores.append(i)

    equipo1_prob = session.pop('equipo1_prob', None)
    equipo2_prob = session.pop('equipo2_prob', None)

    return render_template('pages/analyzer.html',
                        invocadores=invocadores,
                        equipo1_prob=session.get('equipo1_prob'),
                        equipo2_prob=session.get('equipo2_prob'))


def obtener_kda_promedio_80porc(game_name, tag_line, api_key):
    headers = {"X-Riot-Token": api_key}
    region = "americas"

    # Paso 1: Obtener PUUID desde Riot ID
    url_account = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    resp = requests.get(url_account, headers=headers)
    if resp.status_code != 200:
        print(f" Error al obtener cuenta: {resp.status_code}")
        return None
    puuid = resp.json().get("puuid")
    print(f" PUUID obtenido: {puuid}")

    # Paso 2: Obtener todas las partidas para sacar total
    # Riot no tiene endpoint directo para total partidas, pero podemos obtener partidas hasta que no haya más

    # Para no pedir infinitas partidas, vamos a pedir de a 100 en 100 hasta que no hayan más
    partidas_ids = []
    start = 0
    count = 100  # max permitido
    while True:
        url_matches = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
        resp = requests.get(url_matches, headers=headers)
        if resp.status_code != 200:
            print(f" Error al obtener partidas desde {start}: {resp.status_code}")
            break
        batch = resp.json()
        if not batch:
            break
        partidas_ids.extend(batch)
        if len(batch) < count:
            # ya no hay más partidas
            break
        start += count
        time.sleep(1.5)  # prevenir rate limit

    total_partidas = len(partidas_ids)
    print(f"Total partidas encontradas: {total_partidas}")

    if total_partidas == 0:
        print("No se encontraron partidas.")
        return None

    # Calcular el 80% de las partidas
    partidas_a_consultar = max(1, round(total_partidas * 0.80))
    print(f"Calculando KDA promedio en {partidas_a_consultar} partidas (75%)")

    partidas_ids_80 = partidas_ids[:partidas_a_consultar]

    total_k, total_d, total_a = 0, 0, 0
    partidas_validas = 0

    for match_id in partidas_ids_80:
        match_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        r = requests.get(match_url, headers=headers)
        if r.status_code == 429:
            print(" Rate limit excedido. Esperando 2 segundos...")
            time.sleep(2)
            r = requests.get(match_url, headers=headers)
        if r.status_code != 200:
            print(f" No se pudo obtener la partida {match_id}: {r.status_code}")
            continue

        match_data = r.json()
        jugador = next((p for p in match_data['info']['participants'] if p['puuid'] == puuid), None)
        if not jugador:
            print(f" Jugador no encontrado en partida {match_id}")
            continue

        total_k += jugador.get("kills", 0)
        total_d += jugador.get("deaths", 0)
        total_a += jugador.get("assists", 0)
        partidas_validas += 1
        time.sleep(1.5)  # prevenir rate limit

    if partidas_validas == 0:
        print("No se encontraron partidas válidas.")
        return None

    avg_kda = {
        "kills": total_k / partidas_validas,
        "deaths": total_d / partidas_validas,
        "assists": total_a / partidas_validas
    }

    print(f"KDA promedio en {partidas_validas} partidas: "
        f"{avg_kda['kills']:.2f} / {avg_kda['deaths']:.2f} / {avg_kda['assists']:.2f}")
    return avg_kda


@bp.route('/match-saver', methods=['GET', 'POST'])
def match_saver():
    db = current_app.db
    invocadores_raw = list(db.invocadores.find())
    invocadores = []
    for i in invocadores_raw:
        i['_id'] = str(i['_id'])
        invocadores.append(i)

    kda = None
    seleccionado = None

    if request.method == 'POST':
        form_type = request.form.get("form_type")

        if form_type == "auto":
            seleccionado = request.form.get('invocador')
            if not seleccionado or '#' not in seleccionado:
                flash("Selecciona un invocador válido", "danger")
                return redirect(url_for('match_analyzer.match_saver'))

            name, tag = seleccionado.split('#')
            kda = obtener_kda_promedio_80porc(name.strip(), tag.strip(), API_KEY)
            if not kda:
                flash("No se pudo obtener el KDA del jugador", "danger")
                return redirect(url_for('match_analyzer.match_saver'))

            try:
                db.kda_stats.insert_one({
                    "summoner_name": name.strip(),
                    "tagline": tag.strip(),
                    "kills": round(kda["kills"], 2),
                    "deaths": round(kda["deaths"], 2),
                    "assists": round(kda["assists"], 2),
                    "timestamp": time.time()
                })
                flash(f"KDA guardado correctamente para {name}#{tag}", "success")
            except Exception as e:
                print(f"Error al insertar en DB: {e}")
                flash("Error al guardar KDA en la base de datos", "danger")

        elif form_type == "manual":
            invocador = request.form.get("invocador")
            kills = request.form.get("kills", type=float)
            deaths = request.form.get("deaths", type=float)
            assists = request.form.get("assists", type=float)

            if not invocador or '#' not in invocador or kills is None or deaths is None or assists is None:
                flash("Todos los campos del formulario manual son obligatorios.", "danger")
                return redirect(url_for('match_analyzer.match_saver'))

            name, tag = invocador.split("#")

            db.kda_stats.insert_one({
                "summoner_name": name.strip(),
                "tagline": tag.strip(),
                "kills": round(kills, 2),
                "deaths": round(deaths, 2),
                "assists": round(assists, 2),
                "timestamp": time.time()
            })
            flash(f"KDA guardado manualmente para {name}#{tag}", "success")

    return render_template('pages/kda-saver.html',
                        invocadores=invocadores,
                        seleccionado=seleccionado,
                        kda=kda)

@bp.route('/calcular_kda', methods=['POST'])
def calcular_kda():
    data = request.get_json()
    team1_ids = data.get('team1')  # lista de strings "nombre#tag"
    team2_ids = data.get('team2')
    team1_roles = data.get('team1_roles')  # lista de roles (TOP, MID, etc)
    team2_roles = data.get('team2_roles')

    if (not team1_ids or not team2_ids or len(team1_ids) != 5 or len(team2_ids) != 5 or
        not team1_roles or not team2_roles or len(team1_roles) != 5 or len(team2_roles) != 5):
        return jsonify({'error': 'Se requieren dos equipos de 5 jugadores y roles correspondientes'}), 400

    db = current_app.db

    def sumar_kda_equipo(equipo_ids, equipo_roles):
        total = 0
        jugadores_con_error = []
        for player_id, rol in zip(equipo_ids, equipo_roles):
            if '#' not in player_id:
                jugadores_con_error.append(player_id)
                continue
            name, tag = player_id.split('#')
            player_doc = db.kda_stats.find_one({"summoner_name": name.strip(), "tagline": tag.strip()})
            invocador_doc = db.invocadores.find_one({"summoner_name": name.strip(), "tagline": tag.strip()})
            if not player_doc or not invocador_doc:
                jugadores_con_error.append(player_id)
                continue

            # Obtener rank y calcular factor
            rank = invocador_doc.get("rank", "IRON").upper()
            rank_factor = rank_values.get(rank, 1)

            # Obtener impacto del rol
            rol = rol.upper()
            rol_factor = role_impact.get(rol, 0.15)  # default soporte si no existe

            deaths = player_doc["deaths"] if player_doc["deaths"] > 0 else 1
            kda = (player_doc["kills"] + player_doc["assists"]) / deaths

            # Factor ponderado
            contribucion = kda * rank_factor * rol_factor
            total += contribucion

        return total, jugadores_con_error

    score1, errores1 = sumar_kda_equipo(team1_ids, team1_roles)
    score2, errores2 = sumar_kda_equipo(team2_ids, team2_roles)

    errores = errores1 + errores2
    if errores:
        return jsonify({
            'error': 'No se pudo calcular el KDA de algunos jugadores.',
            'jugadores': errores
        }), 400

    total_score = score1 + score2
    prob1 = round((score1 / total_score) * 100, 2)
    prob2 = round((score2 / total_score) * 100, 2)

    return jsonify({
        'equipo1_prob': prob1,
        'equipo2_prob': prob2
    })
