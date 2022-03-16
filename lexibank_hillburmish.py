from pathlib import Path

import attr
import pylexibank
from clldutils.misc import slug
from collections import defaultdict
import re
import lingpy

@attr.s
class CustomLanguage(pylexibank.Language):
    SubGroup = attr.ib(default="Burmish")
    Family = attr.ib(default="Sino-Tibetan")
    NameInSource = attr.ib(default=None)


@attr.s
class CustomConcept(pylexibank.Concept):
    Chinese_Gloss = attr.ib(default=None)
    Number = attr.ib(default=None)


@attr.s
class CustomLexeme(pylexibank.Lexeme):
    Partial_Cognacy = attr.ib(default=None)
    


class Dataset(pylexibank.Dataset):
    dir = Path(__file__).parent
    id = "hillburmish"
    language_class = CustomLanguage
    concept_class = CustomConcept
    lexeme_class = CustomLexeme
    form_spec = pylexibank.FormSpec(
        separators=";,/",
        missing_data=("*", "---", "-", "--"),
        replacements=[(" ", "_")],
        brackets={"[": "]", "(": ")"},
    )

    def cmd_makecldf(self, args):
        args.writer.add_sources()

        wl = lingpy.Wordlist(str(self.raw_dir / "burmish.tsv"))
        language_lookup = args.writer.add_languages(lookup_factory="NameInSource")

        concept_lookup = {}
        for concept in self.conceptlists[0].concepts.values():
            idx = concept.id.split("-")[-1] + "_" + slug(concept.english)
            concept_lookup[concept.english] = idx
            concept_lookup[concept.number] = idx
            concept_lookup[concept.attributes["tbl_english"]] = idx
            args.writer.add_concept(
                ID=idx,
                Concepticon_ID=concept.concepticon_id,
                Concepticon_Gloss=concept.concepticon_gloss,
                Name=concept.english,
                Chinese_Gloss=concept.attributes["chinese"],
            )
        errors = set()
        for idx in pylexibank.progressbar(wl):
            if wl[idx, "concept"] in concept_lookup:
                lex = args.writer.add_form_with_segments(
                    Language_ID=language_lookup[wl[idx, "doculect"]],
                    Parameter_ID=concept_lookup.get(wl[idx, "concept"], ""),
                    Value=wl[idx, "value"],
                    Form=wl[idx, "form"],
                    Segments=wl[idx, "tokens"],
                    Source=["Huang1992"],
                    Partial_Cognacy=" ".join([str(cogid) for cogid in wl[idx, "cogids"]])
                )
                for i, cogid in enumerate(wl[idx, "cogids"]):
                    pass
            else:
                errors.add(wl[idx, "concept"])
        for e in errors:
                print(e)
                
