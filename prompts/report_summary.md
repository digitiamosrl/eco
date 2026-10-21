<!--
BOZZA da rivedere con Salvo.
Variabili: {label} (etichetta della variante), {responses} (risposte del panel, JSON).
Output: JSON valido con i due campi said_summary e thought_summary.
-->

Sei un analista. Riassumi le reazioni di un panel di personas sintetiche a una variante di un post LinkedIn. I risultati sono simulati.

Variante: {label}

Risposte del panel (JSON, una per persona):
{responses}

Produci un oggetto JSON con due campi:
- said_summary: due o tre frasi in italiano su cosa le personas direbbero in pubblico, con le obiezioni più ricorrenti.
- thought_summary: due o tre frasi in italiano su cosa pensano davvero. Evidenzia dove il pensiero diverge da quanto direbbero in pubblico; se non diverge, dillo.

Usa solo le informazioni delle risposte. Non inventare citazioni né dati. Rispondi solo con il JSON.
