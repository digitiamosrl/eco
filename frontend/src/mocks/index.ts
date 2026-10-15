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
  {
    id: "p3",
    role: "Amministratore",
    sector: "Commercio",
    company_size: "micro",
    region: "Puglia",
    profile: "Decide da solo, molto attento ai costi.",
  },
];

export const mockReport: Report = {
  test_id: "t1",
  simulated: true,
  summary: "La variante B convince per concretezza; la A è percepita come troppo generica.",
  items: [
    {
      stimulus_id: "B",
      rank: 1,
      mean_score: 3.7,
      score_distribution: { "1": 0, "2": 1, "3": 0, "4": 1, "5": 1 },
      objections: ["Non dice quanto costa"],
      said_summary: "Lo trovano utile e concreto, qualcuno lo girerebbe al team.",
      thought_summary: "Si fidano, ma pensano al costo senza dirlo.",
      responses: [
        {
          persona_id: "p1",
          stimulus_id: "B",
          thought: "Mi piace, ma se costa come l'ultimo consulente lascio stare.",
          said: "Esempio chiaro, complimenti.",
          score: 4,
          objections: ["Non dice quanto costa"],
        },
        {
          persona_id: "p2",
          stimulus_id: "B",
          thought: "Finalmente numeri veri. Lo giro al team.",
          said: "Lo giro al team.",
          score: 5,
          objections: [],
        },
        {
          persona_id: "p3",
          stimulus_id: "B",
          thought: "Roba per aziende più grandi della mia.",
          said: "",
          score: 2,
          objections: ["Non adatto a una micro impresa"],
        },
      ],
    },
    {
      stimulus_id: "A",
      rank: 2,
      mean_score: 2.3,
      score_distribution: { "1": 0, "2": 2, "3": 1, "4": 0, "5": 0 },
      objections: ["Troppo generico"],
      said_summary: "Apprezzano il tema e lo definiscono interessante.",
      thought_summary: "In privato lo trovano vago: manca un esempio concreto.",
      responses: [
        {
          persona_id: "p1",
          stimulus_id: "A",
          thought: "Bello, ma a me cosa cambia? Non ho tempo.",
          said: "Spunto interessante, grazie.",
          score: 2,
          objections: ["Non dice cosa ottengo"],
        },
        {
          persona_id: "p2",
          stimulus_id: "A",
          thought: "Il solito post sulla trasformazione digitale.",
          said: "Tema importante.",
          score: 3,
          objections: ["Troppo generico"],
        },
        {
          persona_id: "p3",
          stimulus_id: "A",
          thought: "Non ho capito cosa vendono.",
          said: "",
          score: 2,
          objections: ["Troppo generico"],
        },
      ],
    },
  ],
};
