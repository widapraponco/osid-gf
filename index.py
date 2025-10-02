import requests, random, functools, json, os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, g, abort
from datetime import datetime

load_dotenv()

with open('desa.json', 'r') as f:
    data_desa = json.load(f)['data']

app = Flask(__name__)

app.config['ENV'] = os.getenv('ENV')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['TRUSTED_HOSTS'] = os.getenv('TRUSTED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []

def authorize(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get the host from the Host header
        g.host = request.headers.get('Host', '')
        # print(g.host)

        apiKey = request.headers.get('X-API-KEY', '')
        if apiKey != app.config['SECRET_KEY']:
            abort(400, description="Invalid API KEY")
        
        # Validate the host against the trusted list
        if not any(g.host.endswith(trusted) for trusted in app.config['TRUSTED_HOSTS']):
            abort(400, description="Invalid Host header")
        # Code before route handler
        print(f"authorize for {request.path}")
        result = func(*args, **kwargs)
        # Code after route handler
        print("authorize finished")
        return result
    return wrapper

@app.before_request
def serialize_request():
    r_kode_desa = request.args.get('d')
    r_include = request.args.get('t')
    kode_desa = []
    includes = []

    if r_kode_desa and r_kode_desa != '':

        if r_kode_desa[0] == '{' and r_kode_desa[-1] == '}':
            kode_desa = r_kode_desa[1:len(r_kode_desa) - 1].split(',')
        else:
            kode_desa = r_kode_desa.split(',')
    else:
        kode_desa = list(data_desa.keys())

    if r_include and r_include != '':
        includes = r_include.split(',')
    # Example external API (replace with the actual API you want to call)
    g.headers = {
        'Content': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-API-KEY': 'your-api-key-1',
        'Origin': 'https://trusted-host.com'
    }

    g.kode_desa = kode_desa
    g.includes = includes
    

# Sample route
@app.route('/api', methods=['GET'])
@authorize
def home():
    return 'API WORKS'

@app.route('/api/d', methods=['GET'])
@authorize
def desa():    
    try:
        data = {}
        for kode in g.kode_desa:
            response = requests.get(data_desa[kode]['url']+'/d', headers=g.headers, verify=True)  # Send GET request
            response.raise_for_status()   # Raise an HTTPError for bad responses (4xx and 5xx)
            data = response.json()['data']        # Parse the JSON response

        return jsonify({"status": "success", "data": data})
    except requests.exceptions.RequestException as e:
        print(str(e))
        return jsonify({"status": "error", "data": data})
    # return jsonify({"message": "Hello, API!"})

# endpoint for geojson map
@app.route('/api/g', methods=['GET'])
@authorize
def geojson():
    try:
        data = {}
        for kode in g.kode_desa:
            response = requests.get(data_desa[kode]['url']+'/g', headers=g.headers, verify=True)  # Send GET request
            response.raise_for_status()   # Raise an HTTPError for bad responses (4xx and 5xx)
            data = response.json()['data']        # Parse the JSON response

        return jsonify({"status": "success", "data": data})
    except requests.exceptions.RequestException as e:
        print(str(e))
        return jsonify({"status": "error", "data": data})

# endpoint for religion
@app.route('/api/st/<string:slug>', methods=['GET'])
@authorize
def statistik(slug):
    try:
        data = {}
        for kode in g.kode_desa:
            response = requests.get(f"{data_desa[kode]['url']}/st/{slug}", headers=g.headers, verify=True)  # Send GET request
            response.raise_for_status()   # Raise an HTTPError for bad responses (4xx and 5xx)
            result = response.json()['data']        # Parse the JSON response

            for key in result:
                value = result[key]
                id = value['id']

                if id not in data:
                    data[id] = {'nama': value['nama'], 'jumlah': int(value['jumlah']), 'laki': int(value['laki']), 'perempuan': int(value['perempuan'])}
                else:
                    data[id]['jumlah'] = data[id]['jumlah'] + int(value['jumlah'])
                    data[id]['laki'] = data[id]['laki'] + int(value['laki'])
                    data[id]['perempuan'] = data[id]['perempuan'] + int(value['perempuan'])

        str_data = {str(key): value for key, value in data.items()}

        # convert to list
        arr_data = list(str_data.values())   

        return jsonify({"status": "success", "data": arr_data})
    except requests.exceptions.RequestException as e:
        print(str(e))
        return jsonify({"status": "error", "data": arr_data})
    # return jsonify({"data": {
    #     'ISLAM': random.randint(1000, 5000),
    #     'KRISTEN': random.randint(500, 5000),
    #     'KATHOLIK': random.randint(200, 500),
    #     'HINDU': random.randint(100, 500),
    #     'BUDHA': random.randint(100, 500),
    #     'KHONGHUCU': random.randint(50, 500),
    #     'LAINNYA': random.randint(10, 500),
    # }})

# endpoint for idm
@app.route('/api/idm', methods=['GET'])
@authorize
def idm():
    req_tahun = request.args.get('tahun')

    if req_tahun and req_tahun != '':
        tahun = [int(req_tahun)]
        count = 1
    else:
        # make range tahun now = 2024, so count 5 start 2019
        count = 5
        tahun = []
        for i in range(count+1): tahun.append(datetime.now().year - count + i)

    try:
        values = []
        for i, thn in enumerate(tahun):

            values.append({'tahun': str(thn)})
            
            for kode in g.kode_desa:
                response = requests.get(f"{data_desa[kode]['url']}/idm/{thn}", headers=g.headers, verify=True)  # Send GET request
                response.raise_for_status()   # Raise an HTTPError for bad responses (4xx and 5xx)
                idm_data = response.json()['data']        # Parse the JSON response

                penambahan = skor_minimal = skor_saat_ini = 0
                status = target_status = 'Tidak ada status'
                identitas = data_desa[kode]['nama_desa']
                _tahun = thn

                if 'SUMMARIES' in idm_data['idm']:
                    identitas = idm_data['idm']['IDENTITAS'][0]['nama_desa']
                    skor_saat_ini, status, target_status, skor_minimal, penambahan, _tahun = idm_data['idm']['SUMMARIES'].values()

                
                values[i][identitas] = skor_saat_ini
                # if len(result) < i+1:
                # result.append({
                #     'tahun': _tahun,
                #     'desa': identitas, 
                #     'kode': kode,
                #     'status': status,
                #     'target_status': target_status,
                #     'skor_saat_ini': skor_saat_ini,
                #     'skor_minimal': skor_minimal,
                #     'penambahan': penambahan
                # })

                # result[i]['desa'] = identitas
                # result[i]['penambahan'].append(penambahan)
                # result[i]['skor_minimal'].append(skor_minimal)
                # result[i]['skor_saat_ini'].append(skor_saat_ini)
                # result[i]['status'].append(status)
                # result[i]['target_status'].append(target_status)

        return jsonify({"status": "success", "data": values})
    except requests.exceptions.RequestException as e:
        print(str(e))
        return jsonify({"status": "error", "data": values})
    
# endpoint for info
@app.route('/api/i', methods=['GET'])
@authorize
def info():
    try:
        data = []
        meta = []
        for kode in g.kode_desa:
            response = requests.get(f"{data_desa[kode]['url']}/info", headers=g.headers, verify=True)  # Send GET request
            response.raise_for_status()   # Raise an HTTPError for bad responses (4xx and 5xx)
            result = response.json()['data']

            meta.append({kode: result})

            for i, info in enumerate(result):
                if len(data) < i+1:
                    data.append({'title': info['title'], 'count': info['count']})
                else:
                    data[i]['count'] = data[i]['count'] + info['count']

        return jsonify({"status": "success", "data": data, 'meta': meta})
    except requests.exceptions.RequestException as e:
        print(str(e))
        return jsonify({"status": "error", "data": data})

# endpoint for kehadiran
@app.route('/api/k', methods=['GET'])
@authorize
def kehadiran():
    try:
        data = {}
        for kode in g.kode_desa:
            response = requests.get(data_desa[kode]['url']+'/k', headers=g.headers, verify=True)  # Send GET request
            response.raise_for_status()   # Raise an HTTPError for bad responses (4xx and 5xx)
            data = response.json()['data']        # Parse the JSON response

        return jsonify({"status": "success", "data": data})
    except requests.exceptions.RequestException as e:
        print(str(e))
        return jsonify({"status": "error", "data": data})

# endpoint for sex
@app.route('/api/s', methods=['GET'])
@authorize
def jenis_kelamin():
    return jsonify({"data": {"L": 100, "P": 250}})

# endpoint for study
@app.route('/api/std', methods=['GET'])
@authorize
def pendidikan():
    return jsonify({"data": {
        'TIDAK / BELUM SEKOLAH': 10,
        'BELUM TAMAT SD/SEDERAJAT': 10,
        'TAMAT SD / SEDERAJAT': 10,
        'SLTP/SEDERAJAT': 10,
        'SLTA / SEDERAJAT': 10,
        'DIPLOMA I / II': 10,
        'AKADEMI/ DIPLOMA III/S. MUDA': 10,
        'DIPLOMA IV/ STRATA I': 10,
        'STRATA II': 10,
        'STRATA III': 10,
    }})

if __name__ == '__main__':
    app.run(
        debug=os.getenv('DEBUG', 'False').lower() in ('true', '1', 't'),
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )