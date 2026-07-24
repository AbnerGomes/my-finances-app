# Lista padrão de categorias oferecidas ao usuário nos formulários de
# cadastro/edição de despesas e gastos. A coluna "categoria" nas tabelas
# Gastos/despesas é texto livre (sem tabela/FK própria), então esta lista
# não é uma restrição — é só o conjunto sugerido; o usuário pode digitar
# qualquer outra categoria própria, que passa a "existir" no sistema assim
# que usada (ver get_categorias_disponiveis em gasto_service/despesa_service).
CATEGORIAS_PADRAO = [
    'Alimentação',
    'Ifood',
    'Saúde e Beleza',
    'Mobilidade',
    'Entretenimento e Lazer',
    'Moradia',
    'Outros',
    'Dívidas',
    'Educação',
    'Pets',
    'Investimentos',
    'Telefonia',
]


def combinar_categorias(categorias_usuario):
    """Junta a lista padrão com as categorias próprias que o usuário já usou
    (ex.: categorias criadas por ele), sem duplicar e mantendo a ordem
    (padrão primeiro, depois as customizadas por ordem alfabética)."""
    customizadas = sorted(
        {c for c in (categorias_usuario or []) if c and c not in CATEGORIAS_PADRAO}
    )
    return CATEGORIAS_PADRAO + customizadas
