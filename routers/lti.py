from fastapi import FastAPI, Request, HTTPException, Depends, Form, APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlmodel import Session, select
from db import get_session
from models import LMSPlatform, LTIUserLaunch
import jwt
import time
import json
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from jose.utils import base64url_decode
import requests

router = APIRouter()
 

TOOL_CONFIG = {
    "tool_key_id": "chave-123"
}
NGROK_DOMAIN = "https://6002a723ad45.ngrok-free.app"

# --- Carregar chave privada ---
private_key_path = Path("private_key.pem")
if private_key_path.exists():
    private_key = serialization.load_pem_private_key(
        private_key_path.read_bytes(),
        password=None
    )
else:
    private_key = None
    print("⚠️ Chave privada não encontrada. Gere-a com generate_keys.py")

# --- Carregar JWKS ---
jwks_path = Path("jwks.json")
if jwks_path.exists():
    jwks_data = json.loads(jwks_path.read_text())
else:
    jwks_data = {"keys": []}
    print("⚠️ jwks.json não encontrado. Gere-o com generate_keys.py")

@router.get("/.well-known/jwks.json")
def jwks():
    return JSONResponse(jwks_data)

@router.get("/.well-known/lti-tool-config.json")
def lti_tool_config():
    return JSONResponse({
        "title": "Minha Ferramenta LTI",
        "scopes": [
            "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
        ],
        "public_jwk_url": f"{NGROK_DOMAIN}/.well-known/jwks.json",
        "target_link_uri": f"{NGROK_DOMAIN}/lti/launch",
        "oidc_initiation_url": f"{NGROK_DOMAIN}/lti/oidc-init"
    })

@router.api_route("/oidc-init", methods=["GET", "POST"])
def oidc_init(
    iss: str = Form(None),
    login_hint: str = Form(None),
    target_link_uri: str = Form(None),
    lti_message_hint: str = Form(None),
    session: Session = Depends(get_session)
):
    if not iss or not login_hint:
        return HTMLResponse("❌ Parâmetros ausentes", status_code=400)

    lms = session.exec(select(LMSPlatform).where(LMSPlatform.issuer == iss)).first()
    if not lms:
        raise HTTPException(status_code=400, detail="LMS não registrado")

    redirect_url = (
        f"{lms.auth_login_url}?"
        f"client_id={lms.client_id}"
        f"&response_type=id_token"
        f"&scope=openid"
        f"&response_mode=form_post"
        f"&prompt=none"
        f"&redirect_uri={NGROK_DOMAIN}/lti/launch"
        f"&state=1234"
        f"&nonce={int(time.time())}"
        f"&login_hint={login_hint}"
        f"&lti_message_hint={lti_message_hint}"
    )
    return RedirectResponse(url=redirect_url)

@router.get("/launch")
def launch_placeholder():
    return HTMLResponse("<h2>⚠️ Esse endpoint espera um POST LTI Launch com id_token.</h2>")

@router.post("/launch")
async def lti_launch(request: Request):
    print("🔁 Recebido lançamento LTI")

    form = await request.form()
    id_token = form.get("id_token")

    if not id_token:
        print("❌ id_token ausente")
        raise HTTPException(status_code=400, detail="id_token ausente")

    try:
        print("🔒 JWT recebido, verificando assinatura...")
        jwt_headers = jwt.get_unverified_header(id_token)
        kid = jwt_headers["kid"]

        unverified_payload = jwt.decode(id_token, options={"verify_signature": False})
        issuer = unverified_payload.get("iss")

        with get_session() as session:
            lms = session.exec(select(LMSPlatform).where(LMSPlatform.issuer == issuer)).first()
            if not lms:
                raise HTTPException(status_code=400, detail="Plataforma não cadastrada")

        try:
            print("🌐 Buscando JWKS em:", lms.jwks_url)
            headers = {
                "Accept": "application/json",
                "User-Agent": "LTI-Tool/1.0 (+https://radschool.com.br)"
            }           
            response = requests.get(lms.jwks_url, headers=headers, timeout=5)
            print("🔍 Status:", response.status_code)
           

            if response.status_code != 200:
                raise Exception(f"Status {response.status_code}")

            jwks_remote = response.json()
            print("✅ JWKS recebido com sucesso")
        except Exception as e:
            msg = f"{type(e).__name__}: {str(e)}"
            raise HTTPException(status_code=400, detail=f"Erro ao buscar JWKS da plataforma: {msg}")

        public_key_entry = next((k for k in jwks_remote["keys"] if k["kid"] == kid), None)
        if not public_key_entry:
            raise HTTPException(status_code=400, detail="Chave pública não encontrada no JWKS do LMS")
        
        
        try:
            n_raw = public_key_entry["n"]
            e_raw = public_key_entry["e"]

            

            if not isinstance(n_raw, str) or not isinstance(e_raw, str):
                raise HTTPException(status_code=400, detail="Campos 'n' ou 'e' não são strings.")

            n_bytes = base64url_decode(n_raw.encode("utf-8"))
            e_bytes = base64url_decode(e_raw.encode("utf-8"))

            n = int.from_bytes(n_bytes, byteorder="big")
            e = int.from_bytes(e_bytes, byteorder="big")

            pub_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
            pem = pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

        except Exception as err:
            raise HTTPException(status_code=400, detail=f"Erro ao decodificar ou gerar chave pública: {err}")

    

        payload = jwt.decode(
            id_token,
            pem,
            algorithms=["RS256"],
            audience=lms.client_id
        ) 

        name = payload.get("name", "usuário")
        course = payload.get("https://purl.imsglobal.org/spec/lti/claim/context", {}).get("title", "")
        roles = payload.get("https://purl.imsglobal.org/spec/lti/claim/roles", [])
        raw_payload = json.dumps(payload)

        with get_session() as session:
            launch = LTIUserLaunch(
                name=name,
                course=course,
                roles=",".join(roles),
                issuer=issuer,
                raw_payload=raw_payload
            )
            session.add(launch)
            session.commit()

        return HTMLResponse(f'''
            <html>
                <head><title>Minha Ferramenta LTI</title></head>
                <body style="font-family: sans-serif; padding: 2rem;">
                    <h2>👋 Bem-vindo, {name}!</h2>
                    <p><strong>Curso:</strong> {course}</p>
                    <p><strong>Função:</strong> {", ".join(roles)}</p>
                    <hr>
                    <h3>✅ Lançamento LTI bem-sucedido</h3>
                    <p>Aqui você pode mostrar gráficos, dashboards ou qualquer funcionalidade.</p>
                </body>
            </html>
        ''')

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro no LTI Launch: {str(e)}")

@router.get("/")
def home():
    return HTMLResponse("<h1>LTI 1.3 FastAPI Tool</h1><p>Use /lti/oidc-init para iniciar.</p>")

@router.get("/admin/lms")
def listar_lms(session: Session = Depends(get_session)):
    plataformas = session.exec(select(LMSPlatform)).all()
    return plataformas

@router.post("/admin/lms")
def criar_lms(lms: LMSPlatform, session: Session = Depends(get_session)):
    existente = session.exec(select(LMSPlatform).where(LMSPlatform.issuer == lms.issuer)).first()
    if existente:
        raise HTTPException(status_code=400, detail="Plataforma com esse issuer já cadastrada.")
    session.add(lms)
    session.commit()
    session.refresh(lms)
    return lms

@router.get("/admin/launches")
def listar_lancamentos(session: Session = Depends(get_session)):
    launches = session.exec(select(LTIUserLaunch).order_by(LTIUserLaunch.created_at.desc())).all()
    return [
        {
            "id": l.id,
            "name": l.name,
            "course": l.course,
            "roles": l.roles,
            "issuer": l.issuer,
            "created_at": l.created_at.isoformat()
        }
        for l in launches
    ]
