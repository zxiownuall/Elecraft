# Asset attribution

Elecraft is a legally separate fork of the MIT OR Apache-2.0 CADCraft source. The
upstream authors retain credit in `NOTICE` and the original source-history notes
in `docs/provenance/`. This file lists assets present in this fork, not assets
historically listed by upstream but excluded from the source snapshot.

The Elecraft icon is original artwork, generated solely from rectangles by
`scripts/make_elecraft_icon.py` using Python's standard library. It does not use
upstream iconography or proprietary brand assets. No CADMATIC assets are included.

| Asset | Author | Source | Licence | Notes |
|---|---|---|---|---|
| `assets/app-icon/elecraft-256.png` | Elecraft fork contributors | `scripts/make_elecraft_icon.py` | MIT OR Apache-2.0 | 256×256 geometric E PNG |
| `assets/app-icon/elecraft.ico` | Elecraft fork contributors | `scripts/make_elecraft_icon.py` | MIT OR Apache-2.0 | Windows ICO embeds the same PNG |

Generated-in-code assets from upstream remain attributed to their original
contributors under MIT OR Apache-2.0: UI glyphs (`crates/ui-egui/src/icons.rs`),
the single-stroke drafting font (`crates/fonts/src/stroke.rs`, now displayed as
“Elecraft Stroke”), linetypes and hatch patterns (`crates/doc/src/library.rs`),
the colour palette (`crates/color/src/lib.rs`), and sample drawings
(`crates/engine/src/sample.rs`). The renamed font is based on the original
CADCraft Stroke work, not authored anew by the fork. Historical drawings using
that original built-in style name are accepted only at the DXF read boundary;
the loaded style and subsequent DXF saves use “Elecraft Stroke”. The original
stroke geometry and its upstream attribution remain unchanged; this is name
compatibility, not a newly authored font or an imported font asset.

## Interface translations

These translations were written for the upstream English catalog by the
credited contributors under MIT OR Apache-2.0; the fork only updates product
names and removes obsolete upstream community/marketing strings. No new
translation authorship is claimed.

| Asset | Upstream author | Licence |
|---|---|---|
| `crates/ui-egui/src/i18n/uk.tsv` | @dmatviichuk | MIT OR Apache-2.0 |
| `crates/ui-egui/src/i18n/de.tsv` | CADCraft contributors | MIT OR Apache-2.0 |
| `crates/ui-egui/src/i18n/es.tsv` | @PedroGuille | MIT OR Apache-2.0 |
| `crates/ui-egui/src/i18n/pt_br.tsv` | @WladmirJunior | MIT OR Apache-2.0 |
| `crates/ui-egui/src/i18n/cs.tsv` | @Losminek (AI-assisted) | MIT OR Apache-2.0 |
| `crates/ui-egui/src/i18n/ru.tsv` | @pechnikov2026-star | MIT OR Apache-2.0 |
| `crates/ui-egui/src/i18n/fr.tsv` | @pechnikov2026-star | MIT OR Apache-2.0 |
| `crates/ui-egui/src/i18n/zh.tsv` | @mayloglog | MIT OR Apache-2.0 |
| `crates/ui-egui/src/i18n/sv.tsv` | Erik Holmbom (@holmbom) with Claude Code (AI-assisted) | MIT OR Apache-2.0 |
| `crates/ui-egui/src/i18n/it.tsv` | Emanuele Bottelli (AI-assisted) | MIT OR Apache-2.0 |
| `crates/ui-egui/src/i18n/ko.tsv` | @huk082 (AI-assisted) | MIT OR Apache-2.0 |
| `crates/ui-egui/src/i18n/ar.tsv` | @hasan-sdaif | MIT OR Apache-2.0 |
