<!--
Genera la descrizione di una persona del panel a partire dagli attributi campionati dai dati.
Variabili: {role}, {sector}, {company_size}, {region}.
Output: JSON con il solo campo profile.
La persona non conosce Digitiamo né il test: il profilo descrive solo la sua vita di lavoro.
-->

Descrivi una persona reale del pubblico di LinkedIn in Italia, a partire da questi dati:

- Ruolo: {role}
- Settore: {sector}
- Azienda: {company_size}
- Regione: {region}

Scrivi in italiano, in terza persona, 2 o 3 frasi brevi. Racconta:
- com'è fatta la sua giornata di lavoro e di cosa si occupa davvero;
- come usa LinkedIn (legge, commenta, quasi mai, solo per lavoro) e quanta attenzione dà a ciò che ci trova;
- che rapporto ha con l'intelligenza artificiale e il digitale, e che cosa la rende scettica o interessata.

Regole:
- Nessun nome, cognome, azienda o dato che permetta di riconoscere una persona reale.
- Non nominare Digitiamo, test o sondaggi.
- Evita frasi generiche: scegli dettagli concreti e plausibili per quel ruolo e quel settore.

Rispondi solo con un oggetto JSON: {{"profile": "..."}}
