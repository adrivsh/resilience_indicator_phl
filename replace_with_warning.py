import warnings

def replace_with_warning(series_in,dico):
    out=series_in.replace(dico)
    bads = [c for c in out if c not in dico.tolist()]
    if bads !=[]:
        warnings.warn("bad country names:" +",".join(bads))
    return out