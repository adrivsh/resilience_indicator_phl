import warnings

def replace_with_warning(series_in,dico):
    out=series_in.replace(dico)
    bads = out[~ out.isin(dico)].unique()
    if bads !=[]:
        warnings.warn("bad country names:" +",".join(bads))
    return out