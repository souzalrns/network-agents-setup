import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { SelfAwareness } from '../observability/SelfAwareness';

export interface UserProfile {
  id: string;
  name: string;
  role: 'admin' | 'manager' | 'operator' | 'viewer';
  preferences: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    complexity: 'simple' | 'medium' | 'advanced';
    notifications: 'all' | 'important' | 'none';
    defaultDomain?: string;
  };
  permissions: string[];
  lastAccess: Date;
  usagePatterns: {
    frequentActions: string[];
    preferredDomains: string[];
    averageSessionDuration: number;
  };
}

export interface InterfaceConfig {
  userId: string;
  layout: 'compact' | 'comfortable' | 'spacious';
  visibleModules: string[];
  hiddenModules: string[];
  shortcuts: Record<string, string>;
  theme: {
    primary: string;
    secondary: string;
    accent: string;
  };
  accessibility: {
    fontSize: number;
    highContrast: boolean;
    reducedMotion: boolean;
    screenReader: boolean;
  };
}

export class AdaptiveInterface extends EventEmitter {
  private logger = getGlobalLogger();
  private profiles: Map<string, UserProfile> = new Map();
  private configs: Map<string, InterfaceConfig> = new Map();

  constructor(_selfAwareness: SelfAwareness) {
    super();
    this.logger.info('[AdaptiveInterface] Initialized');
  }

  // ===== P-036: Interfaces Adaptativas =====

  /**
   * Cria perfil de usuário adaptativo
   */
  createUserProfile(userId: string, name: string, role: UserProfile['role']): UserProfile {
    const profile: UserProfile = {
      id: userId,
      name,
      role,
      preferences: {
        theme: 'system',
        language: 'pt-BR',
        complexity: 'medium',
        notifications: 'important',
      },
      permissions: this.getDefaultPermissions(role),
      lastAccess: new Date(),
      usagePatterns: {
        frequentActions: [],
        preferredDomains: [],
        averageSessionDuration: 0,
      },
    };

    this.profiles.set(userId, profile);
    this.logger.info(`[AdaptiveInterface] User profile created: ${userId}`);
    this.emit('profile:created', profile);

    // Cria configuração de interface
    this.createInterfaceConfig(userId);

    return profile;
  }

  /**
   * Obtém configuração adaptativa para o usuário
   */
  getAdaptiveConfig(userId: string): InterfaceConfig {
    let config = this.configs.get(userId);
    if (!config) {
      config = this.createInterfaceConfig(userId);
    }

    // Adapta baseado no perfil e padrões de uso
    const profile = this.profiles.get(userId);
    if (profile) {
      config = this.adaptToProfile(config, profile);
      this.configs.set(userId, config);
    }

    return config;
  }

  /**
   * Adapta interface baseado no perfil
   */
  private adaptToProfile(config: InterfaceConfig, profile: UserProfile): InterfaceConfig {
    const adapted = { ...config };

    // Ajusta complexidade
    if (profile.preferences.complexity === 'simple') {
      adapted.visibleModules = adapted.visibleModules.slice(0, 3);
    } else if (profile.preferences.complexity === 'advanced') {
      adapted.visibleModules = ['all'];
    }

    // Ajusta tema
    if (profile.preferences.theme !== 'system') {
      adapted.theme = {
        primary: profile.preferences.theme === 'dark' ? '#1a1a2e' : '#ffffff',
        secondary: profile.preferences.theme === 'dark' ? '#16213e' : '#f0f0f0',
        accent: '#4CAF50',
      };
    }

    // Ajusta acessibilidade baseado no perfil
    if (profile.role === 'viewer') {
      adapted.accessibility.fontSize = 14;
      adapted.layout = 'comfortable';
    }

    return adapted;
  }

  /**
   * Cria configuração de interface
   */
  private createInterfaceConfig(userId: string): InterfaceConfig {
    const config: InterfaceConfig = {
      userId,
      layout: 'comfortable',
      visibleModules: ['dashboard', 'agents', 'executions', 'hitl', 'metrics'],
      hiddenModules: [],
      shortcuts: {
        'dashboard': 'alt+d',
        'agents': 'alt+a',
        'executions': 'alt+e',
        'hitl': 'alt+h',
        'metrics': 'alt+m',
      },
      theme: {
        primary: '#ffffff',
        secondary: '#f0f0f0',
        accent: '#4CAF50',
      },
      accessibility: {
        fontSize: 14,
        highContrast: false,
        reducedMotion: false,
        screenReader: false,
      },
    };

    this.configs.set(userId, config);
    return config;
  }

  /**
   * Obtém permissões padrão por role
   */
  private getDefaultPermissions(role: UserProfile['role']): string[] {
    const base = ['read'];
    if (role === 'viewer') return base;

    const writer = [...base, 'write'];
    if (role === 'operator') return writer;

    const manager = [...writer, 'manage'];
    if (role === 'manager') return manager;

    return [...manager, 'admin']; // admin
  }

  // ===== P-037: Progressividade da Interface =====

  /**
   * Obtém nível de progressividade para o usuário
   */
  getProgressiveLevel(userId: string, action: string): {
    level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
    showHelp: boolean;
    advancedOptions: boolean;
    confirmationRequired: boolean;
  } {
    const profile = this.profiles.get(userId);
    if (!profile) {
      return { level: 'beginner', showHelp: true, advancedOptions: false, confirmationRequired: true };
    }

    // Determina nível baseado em uso
    const frequentActions = profile.usagePatterns.frequentActions || [];
    const isFrequent = frequentActions.includes(action);

    if (!isFrequent && profile.preferences.complexity === 'simple') {
      return { level: 'beginner', showHelp: true, advancedOptions: false, confirmationRequired: true };
    }

    if (isFrequent && profile.preferences.complexity === 'advanced') {
      return { level: 'expert', showHelp: false, advancedOptions: true, confirmationRequired: false };
    }

    return {
      level: 'intermediate',
      showHelp: true,
      advancedOptions: false,
      confirmationRequired: true,
    };
  }

  /**
   * Registra ação do usuário para aprendizado
   */
  recordUserAction(userId: string, action: string, duration: number): void {
    const profile = this.profiles.get(userId);
    if (!profile) return;

    // Atualiza padrões de uso
    const actions = profile.usagePatterns.frequentActions || [];
    if (!actions.includes(action)) {
      actions.push(action);
      if (actions.length > 20) actions.shift();
      profile.usagePatterns.frequentActions = actions;
    }

    // Atualiza duração média
    const avg = profile.usagePatterns.averageSessionDuration || 0;
    profile.usagePatterns.averageSessionDuration = (avg + duration) / 2;

    profile.lastAccess = new Date();
    this.profiles.set(userId, profile);
  }

  // ===== P-038: Acessibilidade =====

  /**
   * Verifica acessibilidade da interface
   */
  checkAccessibility(config: InterfaceConfig): {
    passed: boolean;
    issues: string[];
    recommendations: string[];
  } {
    const issues: string[] = [];
    const recommendations: string[] = [];

    // Verifica contraste
    if (config.theme.primary === config.theme.secondary) {
      issues.push('Contraste insuficiente entre cores primárias e secundárias');
      recommendations.push('Aumentar contraste entre cores');
    }

    // Verifica tamanho da fonte
    if (config.accessibility.fontSize < 12) {
      issues.push('Tamanho da fonte abaixo do recomendado (12px mínimo)');
      recommendations.push('Aumentar tamanho da fonte para pelo menos 14px');
    }

    // Verifica modo de alto contraste
    if (!config.accessibility.highContrast) {
      issues.push('Modo de alto contraste não ativado');
      recommendations.push('Ativar modo de alto contraste para melhor visibilidade');
    }

    // Verifica redução de movimento
    if (!config.accessibility.reducedMotion) {
      recommendations.push('Considerar ativar redução de movimento para usuários sensíveis');
    }

    return {
      passed: issues.length === 0,
      issues,
      recommendations,
    };
  }

  /**
   * Aplica recomendações de acessibilidade
   */
  applyAccessibility(config: InterfaceConfig): InterfaceConfig {
    const applied = { ...config };

    // Aplica recomendações
    applied.accessibility.fontSize = Math.max(applied.accessibility.fontSize, 14);
    applied.accessibility.highContrast = true;
    applied.accessibility.reducedMotion = true;

    // Ajusta cores para melhor contraste
    if (applied.theme.primary === applied.theme.secondary) {
      applied.theme.secondary = '#e0e0e0';
    }

    this.logger.info('[AdaptiveInterface] Accessibility applied');
    this.emit('accessibility:applied', { userId: config.userId });

    return applied;
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    totalProfiles: number;
    totalConfigs: number;
    accessibilityIssues: number;
  } {
    let accessibilityIssues = 0;
    for (const config of this.configs.values()) {
      const check = this.checkAccessibility(config);
      if (!check.passed) accessibilityIssues++;
    }

    return {
      totalProfiles: this.profiles.size,
      totalConfigs: this.configs.size,
      accessibilityIssues,
    };
  }
}
