<!--
BOZZA da rivedere con Salvo.
Variabili: {label} (variante di post o schermata di prototipo), {responses} (risposte del panel, JSON).
Output: JSON valido con said_summary, thought_summary e tones (tono di pensato e detto per persona; la divergenza la calcola il codice).
-->

Sei un analista. Riassumi le reazioni di un panel di personas sintetiche a un contenuto: una variante di un post LinkedIn oppure una schermata di un prototipo. I risultati sono simulati.

Contenuto: {label}

Risposte del panel (JSON, una per persona):
{responses}

Produci un oggetto JSON con tre campi:
- said_summary: due o tre frasi in italiano su cosa le personas direbbero in pubblico, con le obiezioni più ricorrenti. Per una schermata, cita anche i passaggi fraintesi (misunderstood) e quante personas lascerebbero perdere (would_abandon).
- thought_summary: due o tre frasi in italiano su cosa pensano davvero. Evidenzia dove il pensiero diverge da quanto direbbero in pubblico; se non diverge, dillo.
- tones: un elemento per **ogni** risposta, con il suo persona_id, thought_tone (il giudizio in thought) e said_tone (il giudizio in said), ciascuno "positivo", "neutro" o "negativo". Valuta i due campi separatamente, ognuno da solo. Esempi: «Non ci credo, soliti miracoli» è negativo; «Impressionante!» è positivo; «Ok.», «Già.» o un said vuoto è neutro; «Interessante, ma vorrei i dettagli» è positivo; «Forse è un po' ottimistico, avete i numeri?» è negativo, perché una critica detta con garbo resta una critica.

Usa solo le informazioni delle risposte. Non inventare citazioni né dati. Rispondi solo con il JSON.
