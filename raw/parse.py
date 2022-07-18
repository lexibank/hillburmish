import re
from collections import defaultdict
from lingpy import *


def split_form(form):
    tones = "<¹²³⁴⁵⁰>"
    in_tone = False
    out = [""]
    for char in form:
        if char in tones:
            in_tone = True

        if in_tone and char not in tones:
            out += [char]
            in_tone = False
        else:
            out[-1] += char
    out = [x for x in out if x.replace("<", "").strip()]
    idxs = []
    for i, x in enumerate(out):
        if x.startswith('<') and x.endswith(">"):
            out[i] = x[1:-1]
            idxs += [1]
        elif x.endswith('>'):
            out[i] = x[:-1]
            idxs += [1]
        elif x.endswith("<"):
            out[i] = x[:-1]
            idxs += [0]
        elif x.startswith('<'):
            out[i] = x[1:]
            idxs += [1]
        else:
            idxs += [0]
                
    return out, idxs

def parse_line(line):

    concept = re.findall('"([^"]*?)"', line)
    concept = concept[0] if concept else ""
    if concept:
        line = line.split('"')[2]
    language = re.findall(r'\(([^\)]*?)\)', line)[0]
    
    protos = eval(line[line.index("[")-1:])

    form = re.findall(r"\) ([^\s]*?)\s", line)[0]
    word, idxs = split_form(form)
    m = ""
    for j, (w, i) in enumerate(zip(word, idxs)):
        if i != 0:
            m = w
            break

    return concept, language, protos, form, word, idxs, m, j


with open("output.txt") as f:
    lines = [line for line in f]

data = defaultdict(list)
protod = defaultdict(lambda : defaultdict(list))
cset = 0
idx = 1
for line in lines:
    skip = False
    if line.startswith("CROSSID:"):
        cset += 1
        proto = re.findall("< \['([^']*)'", line)[0]
        skip = True
    elif '"' in line:
        concept = re.findall('"([^"]*?)"', line)[0]
    if not skip:
        new_concept, language, protos, form, word, idxs, morpheme, midx = parse_line(line)
        if new_concept:
            concept = new_concept
        data[concept, language, "_".join(word)] += [[protos, form, idxs,
            morpheme, midx, {}]]
        for protox in protos:
            protod[protox][language] += [(
                concept, word, form, idxs, morpheme, midx)]
        if not protos:
            protod[proto][language] += [(
                concept, word, form, idxs, morpheme, midx)]

for k, v in protod.items():
    for language, vals in v.items():
        morphemes = [row[-1] for row in vals]
        my_morpheme = sorted(morphemes, key=lambda x: morphemes.count(x),
                reverse=True)[0]
        for c, w, f, idxs, morpheme, midx in vals:
            for row in data[c, language, "_".join(w)]:
                if row[4] == my_morpheme:
                    row[-1][k] = len(vals)
D = {0: ["doculect", "concept", 
    "value", "form", "proto", "proto_forms", "cogids"]}
idx = 1

p2idx = {p: i+1 for i, p in enumerate(protod)}

st = [
        ("ʔts", "ˀts"),
        ("ʔtʃ", "ˀtʃ"),
        ("ay", "ai"),
        ("aj", "ai"), ("ij", "iː"), ("ʔŋ", "ˀŋ"),
        ("ua", "wa"), ("o₁", "U"), ("uiw", "ui̯"),
        ("uo", "wo"), ("ʔɲ", "ˀɲ"),
        ("_", "+"), ("o₂", "O"), ("ʔl", "ˀl"),
        ("ʔj", "ˀj"), ("y", "j"),
        ("ʔm", "ˀm"), 
        ("ʔk", "ˀk"), ("ʔr", "ˀr"), ("ʔp", "ˀp"),
        ("ʔt", "ˀt"), ("ʔn", "ˀn"), ("ʔs", "ˀs"),
        ("<", ""),
        ]

T = {}
for c, l, w in data:
    word = w.split("_")
    wn = w
    for s, t in st:
        wn = wn.replace(s, t)
    D[idx] = [l, c, w.replace("_", " "), wn, ["" for x in word], ["" for x in
        word],
        [0 for x in word]]
    T[l, c, w] = idx
    idx += 1

cogid2concept = defaultdict(list)
maxidx = max(p2idx.values())+1
for (c, l, w), vals in data.items():
    for pforms, form, idxs, morpheme, midx, protos in vals:
        widx = T[l, c, w]
        proto = sorted(protos, key=lambda x: protos[x], reverse=True)
        if proto:
            proto = proto[0]
        else:
            proto = ""
        pforms = " / ".join(pforms)
        cogid = p2idx.get(proto, maxidx)
        if cogid == maxidx:
            maxidx += 1
        D[widx][5][midx] = pforms
        D[widx][6][midx] = cogid
        cogid2concept[cogid] += [c]


def add_tone(form):
    if not form.endswith("H") and not form.endswith("X"):
        if not form[-1] in "ptk":
            form = form + "¹"
        else:
            form = form + "⁴"
    elif form.endswith("H"):
        form = form.replace("H", "²")
    elif form.endswith("X"):
        form = form.replace("X", "³")
    for s, t in st:
        form = form.replace(s, t)
    return form[1:]



for p, cogid in p2idx.items():
    concept = sorted(
            cogid2concept.get(cogid, ["?"]),
            key=lambda x: cogid2concept.get(cogid, ["?"]).count(x),
            reverse=True)[0]
    D[idx] = ["ProtoBurmish", concept, 
            p, add_tone(p), p, p, [cogid]]
    idx += 1

wl = Wordlist(D)
for idx in wl:
    if 0 in wl[idx, "cogids"]:
        for i, cogid in enumerate(wl[idx, 'cogids']):
            if cogid == 0:
                wl[idx, 'cogids'][i] = maxidx
                maxidx += 1


wl.add_entries("tokens", "form", ipa2tokens, semi_diacritics="hɦzsʃɕʂʐʑʒ")

reps = {
        "ṅ": "ṅ/ŋ", "U": "o₁/ʊ",
        "ḥ": "ḥ/⁵", "ṅh": "ṅh/ŋʰ",
        "O": "o₂/ɔ", "rh": "rʰ",
        "tʂ": "ʈʂ", "nh": "nʰ", 
        "tʂh": "ʈʂʰ", "kʐ": "k ʐ",
        "ch": "ch/tʃʰ", "tʐ": "t ʐ",
        "tsh": "tsʰ", "m̥ʐ": "m̥ ʐ",
        "dzh": "dzʰ", "pʐ": "p ʐ",
        "tʃh": "tʃʰ", "ñ": "ñ/ɲ", "khʐ": "kʰ ʐ",
        "kh": "kʰ", "phʐ": "pʰ ʐ", "xʐ": "x ʐ",
        "ph": "pʰ", "rh": "rʰ", "sh": "sʰ", "m̥ʑ": "m̥ ʑ",
        "th": "tʰ", "tɕh": "tɕʰ", "mʐ": "m ʐ", "iau": "i/j au", "khʒ": "kʰ ʒ",
        "lh": "lʰ", "mh": "mʰ", "ñh": "ñh/ɲʰ", 
        }
for idx in wl:
    wl[idx, 'tokens'] = " ".join([reps.get(h, h) for h in wl[idx,
        "tokens"]]).split()

for idx in wl:
    if wl[idx, "doculect"] == "OldBurmese":
        new_tok = []
        for tok in wl[idx, "tokens"].n:
            if tok[-1] in "ptkc":
                tok = " ".join(tok)+" ⁴"
                new_tok += [tok]
            elif tok[-1] in ["ʔ"]:
                new_tok += [" ".join(tok)+" ³"]
            elif tok[-1] in ["ḥ/⁵"]:
                new_tok += [" ".join(tok)]
            else:
                new_tok += [" ".join(tok)]
        wl[idx, "tokens"] = " + ".join(new_tok)
wl.output("tsv", filename="burmish", prettify=False)

alms = Alignments(wl, ref="cogids", transcription="form")
for cogid, msa in alms.msa["cogids"].items():
    m = Multiple(msa["seqs"])
    m.prog_align()
    print(m)
    print(cogid)
    #input()

