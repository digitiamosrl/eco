"""Etichette italiane per le categorie di LinkedIn. Quelle non elencate restano in inglese."""

SENIORITY_IT = {
    "Entry": "Professionista junior",
    "Senior": "Professionista senior",
    "Training": "Tirocinante",
    "Unpaid": "Collaboratore volontario",
    "Manager": "Responsabile",
    "Director": "Direttore",
    "VP": "Vice presidente",
    "CXO": "C-level",
    "Owner": "Titolare",
    "Partner": "Socio",
}

FUNCTION_IT = {
    "Engineering": "Ingegneria",
    "Business Development": "Sviluppo commerciale",
    "Information Technology": "IT",
    "Sales": "Vendite",
    "Marketing": "Marketing",
    "Human Resources": "Risorse umane",
    "Arts and Design": "Design e creatività",
    "Operations": "Operations",
    "Program and Project Management": "Project management",
    "Education": "Formazione",
    "Product Management": "Prodotto",
    "Consulting": "Consulenza",
    "Research": "Ricerca",
    "Finance": "Finanza",
    "Entrepreneurship": "Imprenditoria",
    "Media and Communication": "Comunicazione",
    "Community and Social Services": "Servizi sociali",
    "Customer Success and Support": "Assistenza clienti",
    "Administrative": "Amministrazione",
    "Accounting": "Contabilità",
    "Legal": "Legale",
    "Real Estate": "Immobiliare",
    "Healthcare Services": "Sanità",
    "Quality Assurance": "Qualità",
    "Purchasing": "Acquisti",
    "Military and Protective Services": "Sicurezza",
}

INDUSTRY_IT = {
    "IT Services and IT Consulting": "Servizi e consulenza IT",
    "Software Development": "Sviluppo software",
    "Business Consulting and Services": "Consulenza e servizi alle imprese",
    "Technology, Information and Internet": "Tecnologia e internet",
    "Advertising Services": "Pubblicità",
    "Human Resources Services": "Servizi per le risorse umane",
    "Financial Services": "Servizi finanziari",
    "Higher Education": "Istruzione superiore",
    "Staffing and Recruiting": "Selezione del personale",
    "Marketing Services": "Servizi di marketing",
    "Computer and Network Security": "Sicurezza informatica",
    "Design Services": "Servizi di design",
    "IT System Custom Software Development": "Software su misura",
    "Research Services": "Servizi di ricerca",
    "Telecommunications": "Telecomunicazioni",
    "Strategic Management Services": "Consulenza strategica",
    "Banking": "Banche",
    "Pharmaceutical Manufacturing": "Industria farmaceutica",
    "Information Services": "Servizi informativi",
    "Industrial Machinery Manufacturing": "Macchinari industriali",
    "Professional Training and Coaching": "Formazione professionale",
    "Engineering Services": "Servizi di ingegneria",
    "Government Administration": "Pubblica amministrazione",
    "Data Infrastructure and Analytics": "Infrastrutture dati e analytics",
    "Credit Intermediation": "Intermediazione creditizia",
    "Legal Services": "Servizi legali",
    "Education Administration Programs": "Amministrazione scolastica",
    "Graphic Design": "Grafica",
    "Appliances, Electrical, and Electronics Manufacturing": "Elettrodomestici ed elettronica",
    "Retail": "Commercio al dettaglio",
    "Transportation, Logistics, Supply Chain and Storage": "Trasporti e logistica",
    "Manufacturing": "Manifattura",
    "Venture Capital and Private Equity Principals": "Venture capital e private equity",
    "Real Estate": "Immobiliare",
    "Insurance": "Assicurazioni",
    "E-Learning Providers": "E-learning",
    "Education": "Istruzione",
    "Oil and Gas": "Petrolio e gas",
    "Hospitals and Health Care": "Sanità",
    "Non-profit Organizations": "Organizzazioni non profit",
    "Automation Machinery Manufacturing": "Macchine per l'automazione",
    "Technology, Information and Media": "Tecnologia e media",
    "Internet Publishing": "Editoria online",
    "Accounting": "Contabilità e revisione",
    "International Trade and Development": "Commercio internazionale",
}


def role_of(seniority: str, job_function: str) -> str:
    return (
        f"{SENIORITY_IT.get(seniority, seniority)}, {FUNCTION_IT.get(job_function, job_function)}"
    )


def sector_of(industry: str) -> str:
    return INDUSTRY_IT.get(industry, industry)
