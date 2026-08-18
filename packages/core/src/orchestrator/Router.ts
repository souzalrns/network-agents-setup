export class Router {
  private domainKeywords: Record<string, string[]> = {
    business: ['venda', 'lead', 'proposta', 'financeiro', 'rh', 'operação', 'comercial'],
    software: ['aplicativo', 'site', 'app', 'frontend', 'backend', 'game', 'jogo', 'código'],
    medical: ['médico', 'hospital', 'saúde', 'paciente', 'cirurgia', 'enfermagem', 'clínico'],
    marketing: ['campanha', 'conteúdo', 'instagram', 'tiktok', 'seo', 'influencer', 'anúncio'],
    construction: ['obra', 'reforma', 'construção', 'engenheiro', 'arquiteto', 'alvenaria'],
    legal: ['direito', 'jurídico', 'contrato', 'lei', 'tribunal', 'processo', 'advogado'],
  };
  route(input: string): string {
    const lowerInput = input.toLowerCase();
    for (const [domain, keywords] of Object.entries(this.domainKeywords)) {
      if (keywords.some((kw) => lowerInput.includes(kw))) {
        return domain;
      }
    }
    return 'business';
  }
  routeWithConfidence(input: string): { domain: string; confidence: number } {
    const lowerInput = input.toLowerCase();
    let bestMatch = { domain: 'business', confidence: 0 };
    for (const [domain, keywords] of Object.entries(this.domainKeywords)) {
      let matches = 0;
      for (const kw of keywords) {
        if (lowerInput.includes(kw)) matches++;
      }
      const confidence = matches / keywords.length;
      if (confidence > bestMatch.confidence) {
        bestMatch = { domain, confidence };
      }
    }
    return bestMatch;
  }
}
