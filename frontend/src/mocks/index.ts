// Mocks based on shared schemas, used until the endpoints are ready.
import type { Persona } from "../types/persona";
import type { Report } from "../types/report";

export const mockPersonas: Persona[] = [
  {
    id: "p1",
    role: "Titolare",
    sector: "Manifattura",
    company_size: "piccola",
    region: "Lombardia",
    profile: "Guida l'azienda di famiglia, poco tempo per LinkedIn.",
  },
  {
    id: "p2",
    role: "Direttrice commerciale",
    sector: "Servizi B2B",
    company_size: "media",
    region: "Emilia-Romagna",
    profile: "Valuta fornitori digitali, diffidente verso le promesse generiche.",
  },
];

export const mockReport: Report = {
  test_id: "t1",
  simulated: true,
  summary: "Esempio di report.",
  items: [
    {
      stimulus_id: "variante-a",
      rank: 1,
      mean_score: 3.8,
      score_distribution: { "1": 0, "2": 1, "3": 3, "4": 4, "5": 2 },
      objections: ["Troppo generico"],
      said_summary: "Apprezzano il tema e lo trovano interessante.",
      thought_summary: "In privato lo trovano vago: manca un esempio concreto e un'idea di costo.",
      responses: [
        {
          persona_id: "p1",
          stimulus_id: "variante-a",
          thought: "Bello, ma a me cosa cambia? Non ho tempo per queste cose.",
          said: "Spunto interessante, grazie per la condivisione.",
          score: 2,
          objections: ["Non dice cosa ottengo"],
        },
        {
          persona_id: "p2",
          stimulus_id: "variante-a",
          thought: "Finalmente qualcuno che parla di numeri. Lo giro al mio socio.",
          said: "Finalmente qualcuno che parla di numeri.",
          score: 5,
          objections: [],
        },
      ],
    },
  ],
};
