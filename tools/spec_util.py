"""helpers to build trans/images.json entries"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import images


def save(entry):
    sp = images.load_spec()
    sp = [e for e in sp if e['md5'] != entry['md5']] + [entry]
    json.dump(sp, open(images.SPEC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def preview(md5, ops, name, scale=2):
    d = open(os.path.join(images.ROOT, 'work/texsrc', md5 + '.tm2'), 'rb').read()
    images.preview(d, ops, os.path.join(os.environ['TMP'], 'kb', name), scale)
