"""
Agent local — Scanner USB + eSCL réseau
========================================
Tourne sur un PC du réseau local (LAN).
Fait le pont entre les scanners locaux et le serveur Django en ligne.

Sources supportées :
  - Scanner USB via TWAIN (Windows) ou SANE (Linux/Mac)
  - Scanner réseau via eSCL/AirScan (HP, Canon, Epson, Ricoh, Brother...)

Installation :
  pip install flask requests Pillow
  pip install twain          # Windows TWAIN (scanner USB)
  pip install python-sane    # Linux SANE (scanner USB)

Démarrage :
  python agent.py --server https://votre-serveur.com --token VOTRE_JWT_TOKEN

Windows service (NSSM) :
  nssm install ScannerAgent python C:\\scanner_agent\\agent.py --server https://...
"""
import argparse
import io
import logging
import os
import sys
import tempfile
import threading
import time
import uuid
from datetime import date

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('scanner_agent')


def create_app(server_url, jwt_token):
    try:
        from flask import Flask, jsonify, request as flask_request
    except ImportError:
        logger.error("Flask non installé. Exécuter : pip install flask")
        sys.exit(1)

    app = Flask(__name__)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'agent': 'scanner-agent', 'version': '1.0'})

    @app.route('/scanners', methods=['GET'])
    def list_scanners():
        """Liste les scanners disponibles via TWAIN (Windows) ou SANE (Linux)."""
        scanners = _list_scanners()
        return jsonify({'scanners': scanners})

    @app.route('/scan', methods=['POST'])
    def scan():
        """
        Déclenche un scan, envoie le fichier au serveur Django pour pré-classification.
        Body JSON:
          { "scanner": "NomDuScanner", "resolution": 300, "color": "grayscale", "duplex": false }
        """
        data = flask_request.get_json(force=True)
        scanner_name = data.get('scanner')
        resolution   = int(data.get('resolution', 300))
        color_mode   = data.get('color', 'grayscale')   # color | grayscale | bw
        duplex       = bool(data.get('duplex', False))

        try:
            files = _scan(scanner_name, resolution, color_mode, duplex)
            logger.info(f"Scan terminé : {len(files)} fichier(s)")
        except Exception as e:
            logger.error(f"Erreur scan: {e}")
            return jsonify({'error': str(e)}), 500

        if not files:
            return jsonify({'error': 'Aucune page scannée'}), 400

        # Envoyer au serveur Django pour pré-classification
        try:
            results = _send_to_server(files, server_url, jwt_token)
            return jsonify({'documents': results, 'count': len(results)})
        except Exception as e:
            return jsonify({'error': f'Erreur envoi serveur: {e}'}), 500

    @app.route('/escl/discover', methods=['GET'])
    def escl_discover():
        """Découvre les scanners eSCL sur le LAN via mDNS et IPs configurées."""
        found = []

        # mDNS/Bonjour
        try:
            from zeroconf import Zeroconf, ServiceBrowser
            import time as _time

            discovered = []
            lock = threading.Lock()

            class Listener:
                def add_service(self, zc, type_, name):
                    info = zc.get_service_info(type_, name)
                    if info and info.addresses:
                        addr = '.'.join(str(b) for b in info.addresses[0])
                        port = info.port
                        with lock:
                            discovered.append({
                                'name': name.split('.')[0],
                                'ip': addr, 'port': port,
                                'url': f'http://{addr}:{port}',
                                'protocol': 'escl',
                            })
                def remove_service(self, *a): pass
                def update_service(self, *a): pass

            zc = Zeroconf()
            ServiceBrowser(zc, '_uscan._tcp.local.', Listener())
            _time.sleep(3)
            zc.close()
            found.extend(discovered)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"mDNS error: {e}")

        # IPs manuelles depuis --scanner-ips
        for ip in getattr(app, '_scanner_ips', []):
            for port in (80, 443, 8080, 8443):
                try:
                    import requests as _req
                    r = _req.get(f'http://{ip}:{port}/eSCL/ScannerCapabilities', timeout=3)
                    if r.status_code == 200:
                        found.append({'name': f'Scanner {ip}', 'ip': ip, 'port': port,
                                      'url': f'http://{ip}:{port}', 'protocol': 'escl'})
                        break
                except Exception:
                    continue

        return jsonify({'scanners': found, 'count': len(found)})

    @app.route('/escl/scan', methods=['POST'])
    def escl_scan():
        """
        Déclenche un scan sur un scanner eSCL du LAN et envoie le résultat
        au serveur Django pour pré-classification.
        Body JSON: { scanner_url, resolution, color_mode, source }
        """
        data = flask_request.get_json(force=True)
        scanner_url = data.get('scanner_url', '').rstrip('/')
        resolution  = int(data.get('resolution', 300))
        color_mode  = data.get('color_mode', 'Grayscale')
        source      = data.get('source', 'Platen')

        if not scanner_url:
            return jsonify({'error': 'scanner_url requis'}), 400

        try:
            file_paths = _escl_scan_local(scanner_url, resolution, color_mode, source)
            if not file_paths:
                return jsonify({'error': 'Aucune page scannée'}), 400
            results = _send_to_server(file_paths, server_url, jwt_token)
            return jsonify({'documents': results, 'count': len(results)})
        except Exception as e:
            logger.error(f"eSCL scan error: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/scan-local', methods=['POST'])
    def scan_local():
        """Scan + retourne les fichiers encodés en base64 (pour transfert sans serveur)."""
        data = flask_request.get_json(force=True)
        scanner_name = data.get('scanner')
        resolution   = int(data.get('resolution', 300))

        try:
            files = _scan(scanner_name, resolution, 'grayscale', False)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

        import base64
        result = []
        for path in files:
            with open(path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('ascii')
            result.append({'filename': os.path.basename(path), 'data': b64})
            os.unlink(path)

        return jsonify({'files': result})

    return app


# ─── TWAIN (Windows) ──────────────────────────────────────────────────────────

def _list_scanners():
    """Liste les scanners disponibles."""
    scanners = []
    # TWAIN (Windows)
    try:
        import twain
        sm = twain.SourceManager(0)
        sources = sm.GetSourceList()
        sm.destroy()
        scanners = [{'name': s, 'driver': 'twain'} for s in sources]
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"TWAIN error: {e}")

    # SANE (Linux/Mac)
    if not scanners:
        try:
            import sane
            sane.init()
            devices = sane.get_devices()
            sane.exit()
            scanners = [{'name': d[1], 'model': d[2], 'driver': 'sane'} for d in devices]
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"SANE error: {e}")

    return scanners


def _scan(scanner_name=None, resolution=300, color_mode='grayscale', duplex=False):
    """Lance un scan et retourne la liste des chemins de fichiers temporaires."""
    # Tentative TWAIN
    try:
        return _scan_twain(scanner_name, resolution, color_mode, duplex)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"TWAIN scan failed: {e}")

    # Tentative SANE
    try:
        return _scan_sane(scanner_name, resolution, color_mode, duplex)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"SANE scan failed: {e}")

    raise RuntimeError("Aucun driver scanner disponible (twain / sane)")


def _scan_twain(scanner_name=None, resolution=300, color_mode='grayscale', duplex=False):
    import twain
    from PIL import Image

    sm = twain.SourceManager(0)

    if scanner_name:
        src = sm.OpenSource(scanner_name)
    else:
        src = sm.OpenSource()

    src.SetCapability(twain.ICAP_XRESOLUTION, twain.TWTY_FIX32, float(resolution))
    src.SetCapability(twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, float(resolution))

    pixel_type = {
        'color':     twain.TWPT_RGB,
        'grayscale': twain.TWPT_GRAY,
        'bw':        twain.TWPT_BW,
    }.get(color_mode, twain.TWPT_GRAY)
    src.SetCapability(twain.ICAP_PIXELTYPE, twain.TWTY_UINT16, pixel_type)

    files = []
    src.RequestAcquire(0, 0)
    rv = src.XferImageNatively()

    while rv:
        handle, count = rv
        img = twain.DIBToBMFile(handle)
        twain.GlobalHandleFree(handle)

        pil = Image.open(io.BytesIO(img))
        tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        pil.save(tmp.name, format='PDF', resolution=float(resolution))
        tmp.close()
        files.append(tmp.name)

        if count == 0:
            break
        rv = src.XferImageNatively()

    src.destroy()
    sm.destroy()
    return files


def _scan_sane(scanner_name=None, resolution=300, color_mode='grayscale', duplex=False):
    import sane
    from PIL import Image

    sane.init()
    devices = sane.get_devices()
    if not devices:
        raise RuntimeError("Aucun scanner SANE détecté")

    dev_name = scanner_name or devices[0][0]
    dev = sane.open(dev_name)

    dev.resolution = resolution
    dev.mode = {'color': 'color', 'grayscale': 'gray', 'bw': 'lineart'}.get(color_mode, 'gray')

    files = []
    dev.start()
    img = dev.snap()
    tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    img.save(tmp.name, format='PDF')
    tmp.close()
    files.append(tmp.name)

    dev.close()
    sane.exit()
    return files


ESCL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<scan:ScanSettings
    xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03"
    xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
  <pwg:Version>2.6</pwg:Version>
  <scan:Intent>TextAndGraphic</scan:Intent>
  <pwg:ScanRegions><pwg:ScanRegion>
    <pwg:ContentRegionUnits>escl:ThreeHundredthsOfInches</pwg:ContentRegionUnits>
    <pwg:Height>3507</pwg:Height><pwg:Width>2481</pwg:Width>
    <pwg:XOffset>0</pwg:XOffset><pwg:YOffset>0</pwg:YOffset>
  </pwg:ScanRegion></pwg:ScanRegions>
  <scan:InputSource>{source}</scan:InputSource>
  <scan:ColorMode>{color_mode}</scan:ColorMode>
  <scan:XResolution>{resolution}</scan:XResolution>
  <scan:YResolution>{resolution}</scan:YResolution>
  <pwg:DocumentFormat>application/pdf</pwg:DocumentFormat>
</scan:ScanSettings>"""


def _escl_scan_local(scanner_url, resolution=300, color_mode='Grayscale', source='Platen'):
    """Scan eSCL depuis l'agent local (LAN → LAN, pas besoin du serveur Django)."""
    import requests as _req

    xml = ESCL_XML.format(source=source, color_mode=color_mode, resolution=resolution)
    resp = _req.post(
        f"{scanner_url}/eSCL/ScanJobs",
        data=xml.encode('utf-8'),
        headers={'Content-Type': 'text/xml; charset=utf-8'},
        timeout=30,
        verify=False,
    )
    resp.raise_for_status()
    job_url = resp.headers.get('Location', f"{scanner_url}/eSCL/ScanJobs/1").rstrip('/')

    files = []
    page = 1
    while True:
        try:
            pr = _req.get(f"{job_url}/NextDocument", timeout=60, stream=True, verify=False)
            if pr.status_code in (404, 409):
                break
            pr.raise_for_status()
            tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            for chunk in pr.iter_content(8192):
                tmp.write(chunk)
            tmp.close()
            files.append(tmp.name)
            page += 1
        except Exception:
            if page == 1:
                raise
            break

    return files


def _send_to_server(file_paths, server_url, jwt_token):
    """Envoie les fichiers au serveur Django pour pré-classification."""
    import requests

    url = f"{server_url.rstrip('/')}/api/scan/pre-classify/"
    headers = {'Authorization': f'Bearer {jwt_token}'}

    files_payload = []
    opened = []
    try:
        for path in file_paths:
            f = open(path, 'rb')
            opened.append(f)
            files_payload.append(('files', (os.path.basename(path), f, 'application/pdf')))

        resp = requests.post(url, files=files_payload, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json().get('documents', [])
    finally:
        for f in opened:
            f.close()
        for path in file_paths:
            try:
                os.unlink(path)
            except Exception:
                pass


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scanner Agent — Ediligence')
    parser.add_argument('--server',      default='http://localhost:8000', help='URL du serveur Django')
    parser.add_argument('--token',       default='',                      help='JWT token')
    parser.add_argument('--port',        default=9191,  type=int,         help='Port local (défaut: 9191)')
    parser.add_argument('--host',        default='127.0.0.1',             help='Hôte (défaut: 127.0.0.1)')
    parser.add_argument('--scanner-ips', default='',                      help='IPs scanners réseau, séparées par virgule. Ex: 192.168.1.50,192.168.1.51')
    args = parser.parse_args()

    app = create_app(args.server, args.token)
    app._scanner_ips = [ip.strip() for ip in args.scanner_ips.split(',') if ip.strip()]

    logger.info(f"Scanner Agent démarré sur http://{args.host}:{args.port}")
    logger.info(f"Serveur cible : {args.server}")
    if app._scanner_ips:
        logger.info(f"Scanners réseau configurés : {app._scanner_ips}")
    app.run(host=args.host, port=args.port, debug=False)
