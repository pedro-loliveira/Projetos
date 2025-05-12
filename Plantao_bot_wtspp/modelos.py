from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()


class Plantao(Base):
    __tablename__ = 'plantoes'
    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True, nullable=False)
    dia_hora = Column(DateTime, nullable=False)
    is_taken = Column(Boolean, default=False)
    matricula = Column(String, nullable=True)
    reservado_em = Column(DateTime, nullable=True)


# cria ou abre o banco
engine = create_engine('sqlite:///plantao.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
