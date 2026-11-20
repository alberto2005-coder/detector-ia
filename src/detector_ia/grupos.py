"""Grupos de copia: si A≈B y B≈C, los tres forman un grupo (idea de los clústeres de Dolos)."""


def formar_grupos(nombres, pares_copia):
    """`pares_copia`: iterable de (a, b, ngramas, coseno) ya filtrado como copia.

    Devuelve [{"id": "G1", "miembros": [...], "pares": [...]}] con los grupos de 2 o más
    entregas, del más grande al más pequeño.
    """
    padre = {n: n for n in nombres}

    def raiz(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    pares_copia = list(pares_copia)
    for a, b, *_ in pares_copia:
        padre[raiz(a)] = raiz(b)

    miembros = {}
    for n in nombres:
        miembros.setdefault(raiz(n), []).append(n)
    grupos = []
    for lista in miembros.values():
        if len(lista) < 2:
            continue
        en_grupo = set(lista)
        grupos.append(
            {
                "miembros": sorted(lista),
                "pares": [
                    {"a": a, "b": b, "ngramas": ng, "coseno": cos}
                    for a, b, ng, cos in pares_copia
                    if a in en_grupo and b in en_grupo
                ],
            }
        )
    grupos.sort(key=lambda g: (-len(g["miembros"]), g["miembros"][0]))
    for i, grupo in enumerate(grupos, 1):
        grupo["id"] = f"G{i}"
    return grupos
