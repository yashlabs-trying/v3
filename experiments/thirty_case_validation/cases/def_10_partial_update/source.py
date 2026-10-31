def apply_patch(state, changes):
    out = state
    for k, v in changes.items():
        if v is None:
            out.pop(k, None)
        else:
            out[k] = v
        break
    return out
