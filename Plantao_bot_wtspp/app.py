import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from modelos import Session, Plantao
import datetime

# carrega variáveis de ambiente
load_dotenv()
ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')

client = Client(ACCOUNT_SID, AUTH_TOKEN)
app = Flask(__name__)


def listar_plantoes():
    session = Session()
    hoje = datetime.datetime.now()
    p_list = session.query(Plantao).filter(
        Plantao.dia_hora >= hoje,
        Plantao.is_taken == False
    ).order_by(Plantao.dia_hora).all()
    session.close()
    if not p_list:
        return "Não há plantões disponíveis no momento."
    msg = "⏰ *Plantoes disponíveis:*\n"
    for p in p_list:
        dt_str = p.dia_hora.strftime("%d/%m %H:%M")
        msg += f"- Código: *{p.codigo}* em {dt_str}\n"
    msg += "\nPara reservar, envie: *reservar <código> <sua_matrícula>*"
    return msg


def reservar_plantoes(codigo, matricula):
    session = Session()
    plantao = session.query(Plantao).filter_by(
        codigo=codigo, is_taken=False).first()
    if not plantao:
        session.close()
        return f"❌ Plantão *{codigo}* não encontrado ou já reservado."
    plantao.is_taken = True
    plantao.matricula = matricula
    plantao.reservado_em = datetime.datetime.now()
    session.commit()
    session.close()
    return f"✅ Plantão *{codigo}* reservado com sucesso para matrícula *{matricula}*."


@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    incoming = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()

    if incoming == 'menu':
        resp.message(listar_plantoes())
    elif incoming.startswith('reservar'):
        parts = incoming.split()
        if len(parts) == 3:
            _, codigo, matricula = parts
            resp.message(reservar_plantoes(codigo.upper(), matricula))
        else:
            resp.message(
                "Formato inválido. Use: *reservar <código> <sua_matrícula>*")
    else:
        resp.message(
            "🤖 *Bot Plantão*\n"
            "Envie:\n"
            "- *menu* → listar plantões\n"
            "- *reservar <código> <matrícula>* → reservar um plantão\n"
        )
    return str(resp)


if __name__ == '__main__':
    # popula alguns plantões de exemplo (apenas na primeira execução)
    from modelos import engine, Base, Plantao, Session
    Base.metadata.create_all(engine)
    sess = Session()
    if sess.query(Plantao).count() == 0:
        exemplos = [
            Plantao(codigo='A1', dia_hora=datetime.datetime(2025, 5, 20, 8, 0)),
            Plantao(codigo='B2', dia_hora=datetime.datetime(2025, 5, 20, 14, 0)),
            Plantao(codigo='C3', dia_hora=datetime.datetime(2025, 5, 21, 20, 0)),
        ]
        sess.add_all(exemplos)
        sess.commit()
    sess.close()

    app.run(host='0.0.0.0', port=5000)
