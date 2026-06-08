# Blueprint: Sales-outreach e-mail genereren

## Doel
Voor elke lead in het dashboard een persoonlijk, kant-en-klaar sales-bericht
voorstellen gericht op onderhoud van de bedrijfstuin/openbare ruimte, en de
gebruiker met één klik naar zijn eigen mailclient sturen (`mailto:`) om te
versturen — geen automatische verzending, de mens blijft in de lead.

## Benodigde input
Een lead-record (dict) met minimaal: `company_name`, optioneel `contact_name`,
`email`.

## System
`systems/generate_email.py` → `build_message(lead)`

Genereert:
- `subject`: gepersonaliseerd onderwerp met bedrijfsnaam
- `body`: bericht in Antwan's tone-of-voice ("ontzorgen met behoud van inspraak"),
  gericht op zakelijk groenonderhoud
- `mailto_url`: kant-en-klare `mailto:` link met gecodeerde subject/body

## Verwachte output
Het dashboard toont het bericht in een tekstveld (door gebruiker nog aan te passen)
en een knop "✉️ Open in mail-app" die de mailto-link opent in de standaard mailclient
van de gebruiker, met afzendergegevens van Antwan Tuinprojecten (info@antwan.nl,
010-5011150) al ingevuld in de ondertekening.

## Edge cases
- Geen e-mailadres bekend → knop is uitgeschakeld en toont een waarschuwing; de
  gebruiker kan dan handmatig bellen via het getoonde telefoonnummer.
- Geen contactpersoon bekend → aanhef valt automatisch terug op "Beste," zonder naam.

## Geleerde lessen
*(nog leeg — vul aan met feedback over welke bewoordingen het beste converteren)*
