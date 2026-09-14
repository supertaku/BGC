# Attribution and usage boundaries

## OpenStreetMap

The pilot geographic database and generated massing use OpenStreetMap data obtained through Overpass.

Required visible credit: **© OpenStreetMap contributors**  
Copyright/attribution link: <https://www.openstreetmap.org/copyright>  
Database license: [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/)  
Guidance: [OSMF Attribution Guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines)

The viewer displays the credit as a persistent link. Raw snapshots retain query, endpoint, retrieval time, bbox, attribution, and hashes. Before public distribution, review whether the processed geographic files constitute a Derivative Database and publish/share them as required by the ODbL.

## Wikimedia Commons

Only metadata was retrieved. No image was downloaded or bundled. Every candidate retains its page URL, creator/credit when exposed, per-file license and license URL, retrieval date, and identity-review status. A file's presence on Commons does not waive its credit, license, or modification-marking conditions.

## Mapillary

No request was made because no `MAPILLARY_ACCESS_TOKEN` was available. The integration stores no token and downloads no imagery. API terms, attribution, contributed-imagery licensing, and derivative/redistribution implications require per-use review before local storage or textures.

## Official and third-party sites

BCDA, ULI, Ayala/BGC, and property/developer pages are research evidence unless an explicit reuse license says otherwise. Their images are not approved for download, transformation, texture creation, or redistribution by default.

Machine-readable registry: `data/entities/source-registry.json`.

## M5 canonical source and rights records

The M5 source registry is `data/sources/sources.json`; the earlier `data/entities/source-registry.json` remains a compatibility record for the M1–M4 pipeline. File-level reference rights are stored in `data/references/references.json`, and the Central Square handoff has a release-oriented subset in `data/reconstruction_packages/bgc_building_0014/rights.json`.

The retained Commons files are remote metadata only. A `REUSE_CAPABLE` classification means the recorded explicit license was recognized and required creator metadata was present; it is not a substitute for release-time attribution assembly. Official property/developer pages are `RESEARCH_ONLY`, even when their photographs are viewable in a browser.

Detailed policy: `docs/REFERENCE_RIGHTS_POLICY.md`.

## M6 Central Square Commons records

The M6 package uses metadata for the following remote Commons files. No image file is bundled. Each is recorded as CC BY-SA 4.0; redistribution or adapted use must credit the named creator, link the source and license, indicate changes, and apply the license's share-alike terms where required.

| File | Creator | Source | License |
| --- | --- | --- | --- |
| View of Central Square from 30th St., BGC.jpg | Ralff Nestor Nacor | [Commons file page](https://commons.wikimedia.org/wiki/File:View_of_Central_Square_from_30th_St.,_BGC.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Central Square Building, Bonifacio Global City.jpg | Hans Olav Lien | [Commons file page](https://commons.wikimedia.org/wiki/File:Central_Square_Building,_Bonifacio_Global_City.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Mazda CX-90 PHEV Exclusive (Philippines) at the 2024 Mazda Fan Festa Philippines (4).jpg | Ethan Llamas | [Commons file page](https://commons.wikimedia.org/wiki/File:Mazda_CX-90_PHEV_Exclusive_(Philippines)_at_the_2024_Mazda_Fan_Festa_Philippines_(4).jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| BGC - BHS Central Jan 8 2025.jpg | PH 0447 | [Commons file page](https://commons.wikimedia.org/wiki/File:BGC_-_BHS_Central_Jan_8_2025.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| BGC - BHS Central Jan 22 2025.jpg | PH 0447 | [Commons file page](https://commons.wikimedia.org/wiki/File:BGC_-_BHS_Central_Jan_22_2025.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| 5th Avenue, BGC, Taguig City, Aug 2025 (1).jpg | Ralff Nestor Nacor | [Commons file page](https://commons.wikimedia.org/wiki/File:5th_Avenue,_BGC,_Taguig_City,_Aug_2025_(1).jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Bonifacio High Street from PSE Tower, BGC, Taguig City, Aug 2025.jpg | Ralff Nestor Nacor | [Commons file page](https://commons.wikimedia.org/wiki/File:Bonifacio_High_Street_from_PSE_Tower,_BGC,_Taguig_City,_Aug_2025.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |

Official, editorial, blog, and video imagery listed in the package remains `RESEARCH_ONLY`: it may inform observation notes but must not be copied into textures, bundled, or redistributed without separate permission.
