import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';

// P-036/037/038: Interface Adaptativa — configuração de UI por usuário,
// níveis de divulgação progressiva ("progressive disclosure") e
// verificações/correções básicas de acessibilidade.

export interface UserInterfaceConfig {
  userId: string;
  disclosureLevel: 1 | 2 | 3 | 4 | 5; // 1 = iniciante, 5 = expert
  theme: 'light' | 'dark' | 'auto';
  density: 'comfortable' | 'compact';
  accessibility: {
    highContrast: boolean;
    reducedMotion: boolean;
    screenReaderOptimized: boolean;
    fontScale: number;
  };
  updatedAt: Date;
}

export class AdaptiveInterface extends EventEmitter {
  private configs: Map<string, UserInterfaceConfig> = new Map();
  private logger = getGlobalLogger();

  private defaultConfig(userId: string): UserInterfaceConfig {
    return {
      userId,
      disclosureLevel: 1,
      theme: 'auto',
      density: 'comfortable',
      accessibility: {
        highContrast: false,
        reducedMotion: false,
        screenReaderOptimized: false,
        fontScale: 1,
      },
      updatedAt: new Date(),
    };
  }

  getConfig(userId: string): UserInterfaceConfig {
    return this.configs.get(userId) || this.defaultConfig(userId);
  }

  updateConfig(userId: string, patch: Partial<Omit<UserInterfaceConfig, 'userId' | 'updatedAt'>>): UserInterfaceConfig {
    const current = this.getConfig(userId);
    const updated: UserInterfaceConfig = {
      ...current,
      ...patch,
      accessibility: { ...current.accessibility, ...(patch.accessibility || {}) },
      updatedAt: new Date(),
    };
    this.configs.set(userId, updated);
    this.emit('config:updated', updated);
    return updated;
  }

  /**
   * Aumenta gradualmente o nível de divulgação com base na quantidade de
   * interações bem-sucedidas do usuário (progressive disclosure).
   */
  progressDisclosure(userId: string, successfulInteractions: number): UserInterfaceConfig {
    const current = this.getConfig(userId);
    const thresholds = [0, 10, 30, 75, 150];
    let level: UserInterfaceConfig['disclosureLevel'] = 1;
    for (let i = thresholds.length - 1; i >= 0; i--) {
      if (successfulInteractions >= thresholds[i]) {
        level = (i + 1) as UserInterfaceConfig['disclosureLevel'];
        break;
      }
    }
    if (level !== current.disclosureLevel) {
      this.logger.info(`[AdaptiveInterface] Usuário ${userId} avançou para nível de divulgação ${level}`);
      this.emit('disclosure:advanced', { userId, level });
    }
    return this.updateConfig(userId, { disclosureLevel: level });
  }

  /**
   * Verifica problemas de acessibilidade em um elemento/tela descrito.
   */
  checkAccessibility(element: {
    hasAltText?: boolean;
    contrastRatio?: number;
    hasAriaLabel?: boolean;
    isKeyboardNavigable?: boolean;
  }): { compliant: boolean; issues: string[] } {
    const issues: string[] = [];
    if (element.hasAltText === false) issues.push('Elemento sem texto alternativo');
    if (element.contrastRatio !== undefined && element.contrastRatio < 4.5) {
      issues.push(`Contraste insuficiente: ${element.contrastRatio.toFixed(1)} (mínimo 4.5)`);
    }
    if (element.hasAriaLabel === false) issues.push('Elemento sem rótulo ARIA');
    if (element.isKeyboardNavigable === false) issues.push('Elemento não navegável por teclado');
    return { compliant: issues.length === 0, issues };
  }

  /**
   * Sugere correções automáticas para os problemas de acessibilidade encontrados.
   */
  suggestAccessibilityFixes(issues: string[]): string[] {
    return issues.map((issue) => {
      if (issue.includes('texto alternativo')) return 'Adicionar atributo alt descritivo';
      if (issue.includes('Contraste')) return 'Ajustar cores para atingir contraste mínimo WCAG AA (4.5:1)';
      if (issue.includes('ARIA')) return 'Adicionar aria-label apropriado';
      if (issue.includes('teclado')) return 'Garantir foco e navegação via tabindex';
      return 'Revisar manualmente';
    });
  }
}
