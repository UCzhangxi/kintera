"""Backend-independent plotted values, with a strict binary64 roundoff comparison.

Eight ULPs allow elementary arithmetic/serialization roundoff, not model error.
Integer/status values, strings, keys, array lengths and nonfinite classes are exact.
Every changed float is reported even when within tolerance; approval is separate.
"""
import math
import numbers
import numpy as np


def plain(value):
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return 'NaN' if math.isnan(value) else ('+Inf' if value > 0 else '-Inf')
    return value


def snapshot(fig):
    axes = []
    for ax in fig.axes:
        rows = {'lines': [], 'collections': [], 'images': [], 'patches': [], 'texts': []}
        for line in ax.lines:
            rows['lines'].append({'label': line.get_label(), 'xy': plain(line.get_xydata())})
        for collection in ax.collections:
            rows['collections'].append({'offsets': plain(collection.get_offsets()),
                'array': plain(collection.get_array()),
                'paths': [plain(p.vertices) for p in collection.get_paths()]})
        for image in ax.images:
            rows['images'].append({'array': plain(image.get_array()), 'extent': plain(image.get_extent())})
        for patch in ax.patches:
            # Local geometry and its own transform, not display pixels or SVG paths.
            path = patch.get_path().transformed(patch.get_patch_transform())
            rows['patches'].append({'vertices': plain(path.vertices), 'codes': plain(path.codes)})
        for text in ax.texts:
            row = {'text': text.get_text(), 'position': plain(text.get_position())}
            if hasattr(text, 'xy'):
                row['xy'] = plain(text.xy)
            rows['texts'].append(row)
        rows['limits'] = plain([ax.get_xlim(), ax.get_ylim()])
        rows['labels'] = [ax.get_xlabel(), ax.get_ylabel(), ax.get_title()]
        axes.append(rows)
    if not axes or not any(any(a[k] for k in ('lines', 'collections', 'images', 'patches', 'texts')) for a in axes):
        raise ValueError('figure has no captured data or schematic geometry')
    return {'axes': axes, 'texts': [{'text': t.get_text(), 'position': plain(t.get_position())}
                                  for t in fig.texts]}


def compare(old, new, path='', changes=None):
    """Return all changed leaves; missing or structurally different values fail."""
    if changes is None:
        changes = []
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(old.keys() | new.keys()):
            if key not in old or key not in new:
                changes.append({'path': path+'/'+key, 'old': old.get(key), 'new': new.get(key), 'pass': False,
                                'reason': 'missing or unexpected key'})
            else:
                compare(old[key], new[key], path+'/'+key, changes)
    elif isinstance(old, list) and isinstance(new, list):
        if len(old) != len(new):
            changes.append({'path': path, 'old_length': len(old), 'new_length': len(new), 'pass': False})
        else:
            for i, (a, b) in enumerate(zip(old, new)):
                compare(a, b, path+'/'+str(i), changes)
    elif isinstance(old, numbers.Real) and isinstance(new, numbers.Real) and not isinstance(old, bool) and not isinstance(new, bool):
        if old != new:
            discrete = any(k in path.split('/') for k in ('status', 'diag', 'iterations'))
            tol = 0. if discrete or isinstance(old, int) or isinstance(new, int) else 8*max(math.ulp(old), math.ulp(new))
            delta = abs(new-old)
            changes.append({'path': path, 'old': old, 'new': new, 'absolute': delta,
                            'tolerance': tol, 'pass': math.isfinite(delta) and delta <= tol})
    elif type(old) is not type(new) or old != new:
        changes.append({'path': path, 'old': old, 'new': new, 'pass': False})
    return changes
