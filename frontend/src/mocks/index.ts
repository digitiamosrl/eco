// Mocks based on shared schemas, used until the endpoints are ready.
import type { Persona } from "../types/persona";
import type { Report } from "../types/report";
import type { Stimulus } from "../types/stimulus";

export const mockStimuli: Stimulus[] = [
  {
    id: "variante-a",
    kind: "post",
    variant_label: "A",
    text: "La trasformazione digitale non è più una scelta: è il momento di ripensare come lavora la tua azienda.",
  },
  {
    id: "variante-b",
    kind: "post",
    variant_label: "B",
    text: "Un'azienda di 12 persone ha tagliato del 30% il tempo speso sui preventivi. Ecco cosa ha cambiato, passo per passo.",
  },
];

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
      stimulus_id: "variante-b",
      rank: 1,
      mean_score: 3.7,
      score_distribution: { "1": 0, "2": 1, "3": 0, "4": 1, "5": 1 },
      objections: ["Non dice quanto costa"],
      said_summary: "Lo trovano utile e concreto, qualcuno lo girerebbe al team.",
      thought_summary: "Si fidano, ma pensano al costo senza dirlo.",
      responses: [
        {
          persona_id: "p1",
          stimulus_id: "variante-b",
          thought: "Mi piace, ma se costa come l'ultimo consulente lascio stare.",
          said: "Esempio chiaro, complimenti.",
          score: 4,
          objections: ["Non dice quanto costa"],
          action: "react",
          reaction: "perspicace",
        },
        {
          persona_id: "p2",
          stimulus_id: "variante-b",
          thought: "Finalmente numeri veri. Lo giro al team.",
          said: "Lo giro al team.",
          score: 5,
          objections: [],
          action: "share",
        },
        {
          persona_id: "p3",
          stimulus_id: "variante-b",
          thought: "Roba per aziende più grandi della mia.",
          said: "",
          score: 2,
          objections: ["Non adatto a una micro impresa"],
          action: "scroll",
        },
      ],
    },
    {
      stimulus_id: "variante-a",
      rank: 2,
      mean_score: 2.3,
      score_distribution: { "1": 0, "2": 2, "3": 1, "4": 0, "5": 0 },
      objections: ["Troppo generico"],
      said_summary: "Apprezzano il tema e lo definiscono interessante.",
      thought_summary: "In privato lo trovano vago: manca un esempio concreto.",
      responses: [
        {
          persona_id: "p1",
          stimulus_id: "variante-a",
          thought: "Bello, ma a me cosa cambia? Non ho tempo.",
          said: "Spunto interessante, grazie.",
          score: 2,
          objections: ["Non dice cosa ottengo"],
          action: "react",
          reaction: "sostengo",
        },
        {
          persona_id: "p2",
          stimulus_id: "variante-a",
          thought: "Il solito post sulla trasformazione digitale.",
          said: "Tema importante.",
          score: 3,
          objections: ["Troppo generico"],
          action: "scroll",
        },
        {
          persona_id: "p3",
          stimulus_id: "variante-a",
          thought: "Non ho capito cosa vendono.",
          said: "",
          score: 2,
          objections: ["Troppo generico"],
          action: "scroll",
        },
      ],
    },
  ],
};

// Report of a test with one post: one item, every response has a feed action.
export const mockSingleItem = (stimulusId: string): Report["items"][number] => ({
  stimulus_id: stimulusId,
  rank: 1,
  mean_score: 3.7,
  score_distribution: { "1": 0, "2": 1, "3": 0, "4": 1, "5": 1 },
  objections: ["Non dice quanto costa", "Esempio lontano dal mio settore"],
  said_summary: "Lo trovano utile e concreto; chi commenta chiede dettagli su tempi e metodo.",
  thought_summary: "Si fidano dei numeri, ma pensano al costo e a quanto il caso valga per il loro settore.",
  responses: [
    {
      persona_id: "p1",
      stimulus_id: stimulusId,
      thought: "Interessante, ma se costa come l'ultimo consulente lascio stare.",
      said: "Bell'esempio di processo concreto.",
      score: 4,
      objections: ["Non dice quanto costa"],
      action: "react",
      reaction: "perspicace",
    },
    {
      persona_id: "p2",
      stimulus_id: stimulusId,
      thought: "Finalmente un caso vero. Lo giro al team.",
      said: "Come avete misurato il tempo risparmiato?",
      score: 5,
      objections: [],
      action: "comment",
    },
    {
      persona_id: "p3",
      stimulus_id: stimulusId,
      thought: "Roba per aziende più grandi della mia.",
      said: "",
      score: 2,
      objections: ["Esempio lontano dal mio settore", "Non dice quanto costa"],
      action: "scroll",
    },
  ],
});

export const mockSingleSummary =
  "Il post convince per concretezza, ma chi lavora in una micro impresa scorrerebbe oltre senza fermarsi.";

// Paths found by the prototype import (from the design's ECO_PROTO_IMPORT).
export const mockProtoImport = {
  figma: {
    name: "Onboarding cliente v3",
    url: "https://www.figma.com/proto/k2Q8xR/Onboarding-cliente-v3",
    starts: [
      { id: "s1", name: "Registrazione", screens: ["Home", "Scegli il piano", "Dati azienda", "Pagamento", "Conferma"] },
      { id: "s2", name: "Richiesta preventivo", screens: ["Home", "Servizi", "Modulo preventivo", "Grazie"] },
      { id: "s3", name: "Accesso cliente", screens: ["Login", "Dashboard", "Fatture"] },
    ],
  },
  artifact: {
    name: "Onboarding cliente",
    starts: [{ id: "a1", name: "Dalla prima schermata", screens: ["Benvenuto", "Profilo azienda", "Obiettivi", "Riepilogo"] }],
  },
};
