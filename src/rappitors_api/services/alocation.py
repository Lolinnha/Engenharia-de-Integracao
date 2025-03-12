from firebase_admin import db
import geopy.distance
import time
from typing import List, Dict

def buscar_entregadores_por_raio(latitude: float, longitude: float, raio_metros: int) -> List[Dict]:
    """
    Busca entregadores disponíveis dentro do raio especificado, considerando a localização real.
    """
    ref = db.reference("entregadores")
    entregadores = ref.get()

    if not entregadores:
        return []

    ponto_central = (latitude, longitude)

    entregadores_filtrados = []
    for entregador_id, dados in entregadores.items():
        if dados.get("disponivel") and dados.get("saldo", 0) > 0:
            loc = dados.get("localizacao")
            if loc and "latitude" in loc and "longitude" in loc:
                ponto_entregador = (loc["latitude"], loc["longitude"])
                distancia = geopy.distance.geodesic(ponto_central, ponto_entregador).meters
                
                if distancia <= raio_metros:
                    entregadores_filtrados.append({"id": entregador_id, "saldo": dados["saldo"], "distancia": distancia})

    return entregadores_filtrados

def selecionar_entregadores(latitude: float, longitude: float) -> List[str]:
    """
    Seleciona os 3 melhores entregadores disponíveis dentro de um raio progressivo.
    """
    raio_metros = 500  # Raio inicial
    max_tentativas = 6  # Máximo de 6 tentativas (~6 min)

    for _ in range(max_tentativas):
        entregadores = buscar_entregadores_por_raio(latitude, longitude, raio_metros)

        if entregadores:
            # Ordena por saldo (decrescente) e distância (crescente)
            top_3 = sorted(entregadores, key=lambda x: (-x["saldo"], x["distancia"]))[:3]
            return [e["id"] for e in top_3]

        raio_metros += 500  # Expande o raio em 500m
        time.sleep(60)  # Aguarda 1 minuto antes de tentar novamente

    return []
