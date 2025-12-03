# Developer Inconsistencies Reference
This file lists all intentionally added inconsistencies (GAP, CLONE, REDUNDANCY, CONTRADICTION) across the dataset.

---

## 1. artists.csv
### GAP
- A003: missing birth_date and nationality  
- A011: missing birth_date and nationality  

### CLONE
- A002 duplicated row (exact clone)

### REDUNDANCY
- A001 Claude Monet (full) + A013 Claude Monet (missing nationality)  
- A005 Frida Kahlo (full) + A015 Frida K. (missing nationality)

### CONTRADICTION
- A012 appears twice with conflicting nationality: Argentinian vs Spanish  
- A014 Leonardo da Vinci: nationality “Italy” vs standard “Italian” usage

---

## 2. artworks.csv
### GAP
- AW009, AW010, AW014, AW023: missing artist_id

### CLONE
- AW020 duplicated exactly  
- AW022 duplicated exactly

### REDUNDANCY
- AW002 vs AW014: Water Lilies (second row missing artist_id)  
- AW015 vs AW023: Morning Field (second row missing artist_id)

### CONTRADICTION
- AW013 mapped once to A012 and once to A002  
- AW018 Mona Lisa attributed to A014 contradicts AW004 attribution to A004

---

## 3. locations.csv
### GAP
- L009 missing room

### REDUNDANCY
- L005 and L009 both represent Dali Museum (one missing room)

(No clones or contradictions added)

---

## 4. medium.csv
(No intentional inconsistencies)

---

## 5. artwork_artist.csv
### GAP
- AW009, AW010, AW014, AW023 missing artist_id

### CLONE
- AW025,A002 appears twice

### REDUNDANCY
- Duplicate mapping for AW025 (same mapping repeated)

### CONTRADICTION
- AW013 → A012 and A002  
- AW026 → A012 and A002

---

## 6. artwork_location.csv
### GAP
- AW010, AW023, AW029, AW030 missing location_id

### CLONE
- AW025,L002 appears twice

### REDUNDANCY
- Duplicate mapping for AW025

### CONTRADICTION
- AW026 mapped to L003 and L004

---

## 7. artist_bios.md
### GAP
- “Unknown Artist” bio missing birth_date and nationality

### REDUNDANCY
- Repeated sentence: “Picasso’s early sketches were displayed briefly in European salons.”

### CONTRADICTION
- Contemporary Artist bio claims authorship of *Guernica* (conflicts with artworks.csv)

---

## 8. exhibition_histories.md
### GAP
- Guernica listed without artist attribution

### CLONE
- Entire “Modern Impressionism Showcase – 2018” section duplicated

### REDUNDANCY
- Repeated note: “Exhibition dates subject to final confirmation by curatorial staff.”

(No contradictions added)

---

## 9. provenance_notes.md
### GAP
- Previous owner missing for *Landscape Study* (AW011)

### REDUNDANCY
- Repeated internal note: “Item verified by curatorial team during summer audit.”

### CONTRADICTION
- Two conflicting provenance entries for *Starry Night* (AW001)  
- AW009 ownership: “A. Murphy” vs “E. Murphy”

(No clones added)

---

## 10. location_descriptions.md
### GAP
- L009 Storage Depot missing room designation

(No clones, redundancies, or contradictions added)

---

## 11. misc_notes.md
### GAP
- AW030 accession log missing all metadata fields

### CLONE
- Duplicate memo line: “Pending final review by documentation team.”

### REDUNDANCY
- Repeated administrative line: “Reviewed and noted by curatorial assistant on 14 June.”

(No contradictions added)

---

## End of File
