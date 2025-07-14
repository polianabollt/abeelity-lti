from sqlmodel import Session, select
from db import engine
from models import LMSPlatform

def deletar_lms_por_issuer(issuer: str, client_id: str = None):
    with Session(engine) as session:
        query = select(LMSPlatform).where(LMSPlatform.issuer == issuer)
        if client_id:
            query = query.where(LMSPlatform.client_id == client_id)
        
        plataformas = session.exec(query).all()

        if not plataformas:
            print("⚠️ Nenhuma plataforma encontrada com esse issuer/client_id.")
            return

        for lms in plataformas:
            print(f"🗑️ Deletando: id={lms.id}, issuer={lms.issuer}, client_id={lms.client_id}")
            session.delete(lms)
        session.commit()
        print("✅ Registros deletados com sucesso.")

if __name__ == "__main__":
    # Altere aqui com os dados do LMS que você quer apagar
    deletar_lms_por_issuer("teste", client_id="2")
