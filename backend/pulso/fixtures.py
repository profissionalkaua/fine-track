"""Explicit, synthetic development dataset. Never imported by application startup."""
from datetime import timedelta

from .db import now

EXAMPLES = [
    ('O segredo de um almoço pronto em 15 minutos', 'cozinha.da.lia', 'Culinária', ['receitas', 'comidacaseira']),
    ('Uma rotina pequena que muda o seu dia', 'rotina.com.clara', 'Bem-estar', ['rotina', 'bemestar']),
    ('3 ajustes para fotografar melhor com o celular', 'olhar.do.rafa', 'Fotografia', ['fotografia', 'dicas']),
    ('O jeito mais simples de começar sua horta', 'verde.em.casa', 'Casa e jardim', ['plantas', 'facavocemesmo']),
    ('Seu café da manhã pode ser assim', 'cozinha.da.lia', 'Culinária', ['receitas', 'cafedamanha']),
    ('Antes e depois: um canto para desacelerar', 'casa.da.ana', 'Casa e jardim', ['decoracao', 'antesedepois']),
    ('Um treino curto para quem está começando', 'movimento.com.bia', 'Fitness', ['fitness', 'rotina']),
    ('Como organizar uma semana de criação', 'estudio.mar', 'Criatividade', ['criatividade', 'bastidores']),
]


def seed(settings):
    if settings.environment != 'development':
        raise ValueError('Amostra permitida somente em desenvolvimento.')
    from .admin import load_observations

    time = now().replace(microsecond=0)
    records = []
    for i in range(28):
        title, handle, category, hashtags = EXAMPLES[i % len(EXAMPLES)]
        records.append({'id': str(9000000000000000000+i), 'creator_id': f'demo-{i % 8}', 'handle': handle,
                        'description': title, 'url': None, 'thumbnail': None,
                        'published_at': (time-timedelta(days=35)).isoformat(), 'country': 'BR',
                        'geo_evidence': {'kind': 'observed', 'reason': 'Exemplo fictício de evidência',
                                         'confidence': 1},
                        'categories': [{'text': category, 'confidence': 1, 'reviewed': True,
                                        'version': 'demo-v1'}], 'hashtags': hashtags,
                        'duration': 25 + i, 'synthetic': True,
                        'snapshots': [
                            {'observed_at': (time-timedelta(hours=h)).isoformat(),
                             'views': 120000 + (i+1)*7100*(721-h),
                             'likes': None if i % 4 == 0 else 8000+i*970,
                             'comments': 140+i*28, 'shares': 950+i*84, 'source': 'synthetic-v1'}
                            for h in [720, 168, 24, 0]]})
    load_observations(settings, records, as_of=time)
