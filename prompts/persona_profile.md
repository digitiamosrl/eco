<!--
Genera la descrizione di una persona del panel a partire dagli attributi campionati dai dati.
Variabili: {role}, {sector}, {company_size}, {region}, {ai_attitude}, {linkedin_use}.
ai_attitude e linkedin_use sono ipotesi dichiarate (app/personas/audience.py), non dati.
Output: JSON con il solo campo profile.
La persona non conosce Digitiamo né il test: il profilo descrive solo la sua vita di lavoro.
-->

Descrivi una persona reale del pubblico di LinkedIn in Italia, a partire da questi dati:

- Ruolo: {role}
- Settore: {sector}
- Azienda: {company_size}
- Regione: {region}
- Rapporto con l'intelligenza artificiale: {ai_attitude}
- Uso di LinkedIn: {linkedin_use}

Scrivi in italiano, in terza persona, 2 o 3 frasi brevi. Racconta:
- com'è fatta la sua giornata di lavoro e di cosa si occupa davvero;
- come usa LinkedIn, coerentemente con l'uso indicato sopra, e quanta attenzione dà a ciò che ci trova;
- il suo rapporto con l'intelligenza artificiale, coerente con quello indicato sopra: non attenuarlo e non renderlo più "equilibrato".

Regole:
- Nessun nome, cognome, azienda o dato che permetta di riconoscere una persona reale.
- Non nominare Digitiamo, test o sondaggi.
- Evita frasi generiche: scegli dettagli concreti e plausibili per quel ruolo e quel settore.

Rispondi solo con un oggetto JSON: {{"profile": "..."}}
